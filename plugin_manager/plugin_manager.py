import sys
import inspect
import re
import subprocess
import importlib.util
from pathlib import Path

import pluggy
import semver

from config.config import PluginConfig
from plugin_manager.hook_spec import MySpec
from plugins.ai_pico_plugin import AIPicoPlugin
from plugins.rgb_plugin import RGBPlugin
from plugins.game_plugin import GamePlugin

class Plugin_Manager():
    def __init__(self):
        # create manager and add hookspecs
        self.plugin_manager = pluggy.PluginManager("pixel_art")
        self.plugin_manager.add_hookspecs(MySpec)
        self.root_config = PluginConfig(Path(__file__).parents[1] / "config.toml")
        self.ai_include_list: list[str] = self.root_config.items["ai"]
        self.rgb_include_list: list[str] = self.root_config.items["rgb"]
        self.rgb_plugin_classes: list[type] = []
        self.ai_plugin_classes: list[type] = []
        self.game_plugin_classes: list[type] = []

    def _get_absolute_module_paths(self, search_path: str) -> list[Path]:
        collected_paths = []
        abs_paths = [p.resolve() for p in Path(search_path).rglob("*.py")]
        for path in abs_paths:
            is_not_dunder = not re.match('^.+__.+__.+$', path.name)
            is_not_asset = "assets" not in path.parts
            if is_not_dunder and is_not_asset:
                collected_paths.append(path)
        return collected_paths
    
    def _filter_absolute_module_paths(self, paths: list[Path]) -> list[Path]:
        collected_paths = []
        for path in paths:
            include_plugin = any(p.startswith(path.stem) for p in self.ai_include_list + self.rgb_include_list)
            if include_plugin:
                collected_paths.append(path)
        return collected_paths
    
    def _pip_install_package(self, packages: set[str]):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])
            print(f"> Successfully installed package: {packages}")
        except subprocess.CalledProcessError as e:
            print(f"Error installing package: {packages}: {e}")
    
    def _install_plugin_deps(self, paths: list[Path]):
        # collect requirements paths
        collected_paths = []
        for path in paths:
            i = path.parts.index("plugins")
            if path.parts[i + 1] in ["ai", "game", "rgb"]:
                requirements = Path().joinpath(*path.parts[:i + 3], "requirements.txt")
                if requirements.exists():
                    collected_paths.append(requirements)
        # collect packages
        packages = []
        for requirements in collected_paths:
            with open(requirements, "r") as f:
                packages.extend([pkg.strip() for pkg in f.readlines()])
        packages.sort()
        # TODO: refactor plugins as child processes w/ own sys.path instead?
        reduced_packages = set()
        for i, pkg in enumerate(packages[:-1]):
            pkg_next = packages[i + 1]
            v1 = re.split(r"[<>=~]+", pkg)[-1]
            v2 = re.split(r"[<>=~]+", pkg_next)[-1]
            result = semver.compare(v1, v2)
            if result:
                # pkg greater
                reduced_packages.add(pkg)
            else:
                # pkg_next greater or equal
                reduced_packages.add(pkg_next)
        reduced_packages.add(packages[-1]) # add last pkg since not iterated over
        # install packages
        self._pip_install_package(reduced_packages)

    def _import_plugin_modules(self, paths: list[Path]) -> list:
        modules = []
        for path in paths:
            # get module spec
            spec = importlib.util.spec_from_file_location(path.stem, path)
            print(spec)
            # import plugin module
            module = importlib.util.module_from_spec(spec)
            sys.modules[path.stem] = module
            spec.loader.exec_module(module)
            modules.append(module)
        return modules

    def load_plugins(self):
        # collect plugin modules & classes
        plugin_paths = self._get_absolute_module_paths("plugins")
        filtered_plugin_paths = self._filter_absolute_module_paths(plugin_paths)
        self._install_plugin_deps(filtered_plugin_paths)
        plugin_modules = self._import_plugin_modules(filtered_plugin_paths)
        for p in plugin_modules:
            # append plugin class
            for m in inspect.getmembers(p):
                if inspect.isclass(m[1]):
                    if issubclass(m[1], (RGBPlugin)) and m[0] not in ["RGBPlugin"]:
                        self.rgb_plugin_classes.append(m[1])
                    elif issubclass(m[1], (AIPicoPlugin)) and m[0] not in ["AIPicoPlugin", "GamePlugin"]:
                        if issubclass(m[1], (GamePlugin)):
                            self.game_plugin_classes.append(m[1])
                        else:
                            self.ai_plugin_classes.append(m[1])

    def register_rgb_plugins(self, matrix, rgb_start_event, ai_end_event, ai_result_queue):
        for C in self.rgb_plugin_classes:
            self.plugin_manager.register(
                plugin=C(matrix, rgb_start_event, ai_end_event, ai_result_queue),
                name=C.__name__
            )
    
    def register_ai_plugins(self, rgb_start_event, ai_end_event, ai_result_queue, terminate_thread):
        for C in self.ai_plugin_classes:
            self.plugin_manager.register(
                plugin=C(rgb_start_event, ai_end_event, ai_result_queue, terminate_thread),
                name=C.__name__
            )

    def register_game_plugins(self, rgb_start_event, ai_end_event, ai_result_queue, terminate_thread):
        for C in self.game_plugin_classes:
            self.plugin_manager.register(
                plugin=C(rgb_start_event, ai_end_event, ai_result_queue, terminate_thread),
                name=C.__name__
            )

    def _filter_plugin_funcs(self, plugin_funcs: list[tuple[str, object]], include_list: list[str]) -> list[tuple[str, object]]:
        ordered_filtered_plugin_funcs = []
        funcs_dict = dict(plugin_funcs)
        for inc in include_list:
            if inc in funcs_dict.keys():
                ordered_filtered_plugin_funcs.append((inc, funcs_dict[inc]))
            else:
                print("> Error: _filter_plugin_funcs() can't find plugin")
        return ordered_filtered_plugin_funcs

    def get_plugin_funcs(self) -> tuple[list[tuple[str, object]], list[tuple[str, object]]]:
        # get plugin funcs
        rgb_funcs = [(f"{i.plugin.__module__}.{i.plugin_name}.{i.function.__name__}", i.function) for i in self.plugin_manager.hook.rgb_hook.get_hookimpls()]
        ai_funcs = [(f"{i.plugin.__module__}.{i.plugin_name}.{i.function.__name__}", i.function) for i in self.plugin_manager.hook.ai_hook.get_hookimpls()]
        game_funcs = [(f"{i.plugin.__module__}.{i.plugin_name}.{i.function.__name__}", i.function) for i in self.plugin_manager.hook.game_hook.get_hookimpls()]
        ai_funcs.extend(game_funcs)
        # filter plugin funcs
        filtered_rgb_funcs = self._filter_plugin_funcs(rgb_funcs, self.rgb_include_list)
        filtered_ai_funcs = self._filter_plugin_funcs(ai_funcs, self.ai_include_list)
        return filtered_rgb_funcs, filtered_ai_funcs
