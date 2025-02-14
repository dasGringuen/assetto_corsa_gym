import os
import logging
import time
import mmap
import numpy as np
import cv2
import mss
import win32gui
import datetime
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

IMAGE_SHM_TAG = "Local\\DualBufferImage"

def move_window(window_title="Assetto Corsa", x=0, y=0):
    """
    Moves the specified window to a given (x, y) position on the screen.
    """
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        logger.error(f"Window '{window_title}' not found.")
        return False

    rect = win32gui.GetWindowRect(hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]

    win32gui.MoveWindow(hwnd, x, y, width, height, True)
    logger.info(f"Moved '{window_title}' to ({x},{y}).")
    return True


def get_client_area(window_title="Assetto Corsa"):
    """
    Returns the client area of the specified window as (x, y, width, height).
    """
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        logger.error(f"Window '{window_title}' not found.")
        return None

    rect = win32gui.GetClientRect(hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]

    client_top_left = win32gui.ClientToScreen(hwnd, (0, 0))
    x, y = client_top_left
    return x, y, width, height


def capture_and_process(
    shm_image_width, shm_image_height,
    window_title="Assetto Corsa", save_to_disk=False,
    save_path="captures", show_original=False, verbose=False
):
    """
    Captures a game's client area, converts it to grayscale, resizes it,
    and returns the processed image.

    Returns:
      (processed_image_bytes, processed_image_array)
    """
    start_time = time.time()

    with mss.mss() as sct:
        area = get_client_area(window_title)
        if area is None:
            return None, None
        x, y, width, height = area
        window_info = {"top": y, "left": x, "width": width, "height": height}

        sct_img = sct.grab(window_info)
        capture_time = time.time() - start_time
        if verbose:
            logger.info("Screen captured in {:.4f} seconds. Window info: {}".format(capture_time, window_info))

        img = np.array(sct_img)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        if show_original:
            cv2.imshow("Original Capture", img)
            cv2.waitKey(0)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        final_image = cv2.resize(gray, (shm_image_width, shm_image_height), interpolation=cv2.INTER_LINEAR)

        if save_to_disk:
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(save_path, f"capture_{timestamp}.png")
            cv2.imwrite(filename, final_image)
            if verbose:
                logger.info(f"Screenshot saved: {os.path.abspath(filename)}")

        total_time = time.time() - start_time
        if verbose:
            logger.info("Total execution time: {:.4f} seconds".format(total_time))

        return final_image, window_info


class GrabberSharedMemoryDualBuffer:
    """ Shared Memory Dual Buffer Class """
    def __init__(self, shm_image_width, shm_image_height):
        self.shm_image_height = shm_image_height
        self.shm_image_width = shm_image_width
        self.image_size = shm_image_width * shm_image_height
        self.dual_shm_size = 4 + 2 * self.image_size

        self.dual_shm = mmap.mmap(-1, self.dual_shm_size, tagname=IMAGE_SHM_TAG)

    def read_active_index(self):
        self.dual_shm.seek(0)
        index_bytes = self.dual_shm.read(4)
        try:
            active_index = int.from_bytes(index_bytes, "little")
        except Exception:
            active_index = 0
        return active_index

    def get_active_image(self):
        active_index = self.read_active_index()
        image_offset = 4 + active_index * self.image_size
        self.dual_shm.seek(image_offset)
        img_bytes = self.dual_shm.read(self.image_size)
        img_bytes = img_bytes.rstrip(b'\0')
        img_array = np.frombuffer(img_bytes, dtype=np.uint8).reshape((self.shm_image_height, self.shm_image_width))
        return active_index, img_bytes, img_array

    def write_image(self, image):
        """
        Writes a new image to the inactive buffer and toggles the active index.
        """
        if len(image) > self.image_size:
            image = image[:self.image_size]
        elif len(image) < self.image_size:
            image += b'\0' * (self.image_size - len(image))

        active_index = self.read_active_index()
        new_index = 1 - active_index  # Toggle active index
        image_offset = 4 + new_index * self.image_size
        self.dual_shm.seek(image_offset)
        self.dual_shm.write(image)
        self.dual_shm.seek(0)
        self.dual_shm.write(new_index.to_bytes(4, "little"))
        self.dual_shm.flush()


def main():
    """
    Test function for capturing, processing, and writing images to shared memory.
    """
    move_window("Assetto Corsa", x=0, y=0)

    image_bytes, window_info = capture_and_process(
        config.final_image_width, config.final_image_height,
        window_title="Assetto Corsa", show_original=True, save_to_disk=True, verbose=True
    )
    if image_bytes is None:
        logger.error("Failed to capture rendering.")
        return

    shm_buffer = GrabberSharedMemoryDualBuffer(config.final_image_width, config.final_image_height)
    shm_buffer.write_image(image_bytes.tobytes())

    logger.info("Image written to shared memory.")

    # Read back and display image from shared memory
    active_index, shm_img_bytes, img_array = shm_buffer.get_active_image()
    logger.info(f"Active buffer index: {active_index}, image size: {len(shm_img_bytes)} bytes")
    cv2.imshow("Shared Memory Image", img_array)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    from config import config  # Only used for testing
    main()
