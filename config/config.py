import os
from pathlib import Path
import tomllib

def get_env(key: str) -> str:
    """Gets environment variable by name. Raises an exception if none exist.

    Args:
        key (str): Environment variable by name

    Raises:
        Exception: Environment variable not found

    Returns:
        str: Environment variable value
    """
    val = os.getenv(key)
    if val:
        print(f"> Retrieved environment variable {key}")
        return val.strip()
    else:
        err = f"> Failed to get environment variable {key}"
        print(err)
        raise Exception(err)

class PluginConfig(object):
    """Helper class for root and plugin config files."""    
    def __init__(self, path: Path):
        self.path = path
        self.items = self._load_config()

    def _load_config(self) -> dict:
        """Loads plugin config items.

        Returns:
            dict: Plugin config items
        """
        with self.path.open(mode="rb") as f:
            conf = tomllib.load(f)
            print(f"> Loaded config: {conf}")
            return conf.get("plugin") or conf.get("plugins")
        
    def get_item(self, key: str, fallback_value: any = None) -> any:
        """Get plugin config item.

        Args:
            key (str): Plugin config item key
            fallback_value (any, optional): Value to return if key doesn't exist. Defaults to None.

        Returns:
            any: Plugin config item
        """
        try:
            val = self.items.get(key, fallback_value)
            if type(val) == str:
                val = val.strip()
            print(f"> Retrieved {val} for config item key {key}")
            return val
        except Exception as e:
            print(f"> Failed to get config item: {key}. Error {e}")
            raise
