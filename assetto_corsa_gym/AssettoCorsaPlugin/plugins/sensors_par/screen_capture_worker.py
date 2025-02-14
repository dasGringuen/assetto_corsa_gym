import os
import logging

log_filename = os.path.join(".", "sensor_par_subprocess_log.txt")
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
logger.info("screen_capture_worker initialized")

try:
    import win32event
    import win32con
    from config import config
    import screen_capture
except Exception as e:
    logger.error("Error importing screen_capture: %s", e)
    raise e

def screen_capture_worker():
    shm_buffer = screen_capture.GrabberSharedMemoryDualBuffer(config.final_image_width, config.final_image_height,
                                                              color_mode=config.color_mode)
    EVENT_ALL_ACCESS = 0x1F0003
    hTriggerImageCapture = win32event.OpenEvent(EVENT_ALL_ACCESS, False, config.trigger_image_capture_event_name)

    relocate_screen = config.relocate_screen # relocate screen to 0,0 if True

    while True:
        if relocate_screen:
            if screen_capture.move_window(x=0, y=0):
                relocate_screen = False

        rc = win32event.WaitForSingleObject(hTriggerImageCapture, win32event.INFINITE)
        if rc == win32con.WAIT_OBJECT_0:
            win32event.ResetEvent(hTriggerImageCapture) # to make sure this is only handled once per trigger

            try:
                # Set show_original=True to display the full-resolution capture before processing.
                image, window_info = screen_capture.capture_and_process(config.final_image_width, config.final_image_height,
                                                                        save_to_disk=config.screen_capture_save_to_disk,
                                                                        save_path=config.screen_capture_save_path,
                                                                        verbose=config.screen_capture_verbose,
                                                                        color_mode=config.color_mode,
                                                                        show_original=False)
                if image is None:
                    logger.error("Failed to capture Assetto Corsa rendering.")
                    return
                # Write the processed image into shared memory.
                shm_buffer.write_image(image.tobytes())

            except Exception as e:
                logger.error("Error capturing screen: %s", e)

if __name__ == "__main__":
    if config.screen_capture_enable:
        screen_capture_worker()
