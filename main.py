from threading import Thread, Event
from queue import Queue

from rgbmatrix import RGBMatrix, RGBMatrixOptions

from plugin_manager.plugin_manager import Plugin_Manager

def pipeline_task_plugins(funcs: list[tuple[str, object]], ai_result_queue: Queue, terminate_thread: Event):    
    try:
        while True:
            result = None
            for i, (name, impl) in enumerate(funcs):
                if not terminate_thread.is_set():
                    # run ai plugins (prev impl return is next impl args)
                    result = impl(result) if result else impl()
                    # if i == len(ordered_funcs) - 1:
                    #     # send final result to main thread
                    #     ai_result_queue.put(result)
            print(f"> pipeline_task_plugins() done. Final result: {result}")
    except Exception as e:
        print(f"> pipeline_task_plugins() interrupted: error: {e}")

def pipeline_rgb_plugins(funcs: list[tuple[str, object]], ai_result_queue: Queue, terminate_thread: Event):    
    try:
        while True:
            for i, (name, impl) in enumerate(funcs):
                # run rgb plugins
                impl()
            print("> pipeline_rgb_plugins() done.")
    except Exception as e:
        print(f"> pipeline_rgb_plugins() interrupted: error: {e}")
        raise e

def main():
    # setup
    rgb_start_event = Event()
    ai_end_event = Event()
    terminate_thread = Event()
    ai_result_queue = Queue()

    options = RGBMatrixOptions()
    options.show_refresh_rate = False
    options.brightness = 80 # TODO: make configurable # Note: lower brightness reduces RGB current draw (good for hardware w/ lower current ratings)
    options.rows = 64
    options.cols = 64
    options.gpio_slowdown = 4
    options.hardware_mapping = 'adafruit-hat-pwm'
    options.drop_privileges = False # TODO: allow pixel art to run as non-root user 
    matrix = RGBMatrix(options=options) # Note: must be singleton or else display bugs out (guessing all instances try to write from single call)

    # load and register plugins
    pm = Plugin_Manager()
    pm.load_plugins()
    pm.register_rgb_plugins(matrix, rgb_start_event, ai_end_event, ai_result_queue)
    pm.register_ai_plugins(rgb_start_event, ai_end_event, ai_result_queue, terminate_thread)
    pm.register_game_plugins(rgb_start_event, ai_end_event, ai_result_queue, terminate_thread)    
    rgb_funcs, task_funcs = pm.get_plugin_funcs()

    # start child thread for ai
    t_wake = Thread(name="process_wake", target=pipeline_task_plugins, args=(task_funcs, ai_result_queue, terminate_thread))
    t_wake.start()

    try:
        pipeline_rgb_plugins(rgb_funcs, ai_result_queue, terminate_thread)
        terminate_thread.set()
        t_wake.join()
    except KeyboardInterrupt:
        print("> main() interrupted by user.")
        terminate_thread.set()
        t_wake.join()
        return
    except Exception as e:
        print(f"Error from main(): {e}")
    print("> main() exited.")

if __name__ == "__main__":
    main()