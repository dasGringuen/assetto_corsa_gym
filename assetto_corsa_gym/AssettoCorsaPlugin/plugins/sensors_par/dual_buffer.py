import numpy as np
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

IMAGE_SHM_TAG = "Local\\DualBufferImage"

class GrabberSharedMemoryDualBuffer:
    """Shared Memory Dual Buffer Class that supports grayscale or BGR images."""
    def __init__(self, shm_image_width, shm_image_height, color_mode):
        self.shm_image_width = shm_image_width
        self.shm_image_height = shm_image_height

        # Determine channels based on the color_mode.
        if color_mode.lower() == "bgr":
            self.channels = 3
        elif color_mode.lower() == "gray":
            self.channels = 1
        else:
            raise ValueError(f"Invalid color_mode. Choose 'gray' or 'bgr'. Got: {color_mode}")

        self.image_size = shm_image_width * shm_image_height * self.channels
        # Reserve 4 bytes for the active index, and two buffers for dual buffering.
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
        # Reshape based on the number of channels.
        if self.channels == 1:
            img_array = np.frombuffer(img_bytes, dtype=np.uint8).reshape((self.shm_image_height, self.shm_image_width))
        else:
            img_array = np.frombuffer(img_bytes, dtype=np.uint8).reshape((self.shm_image_height, self.shm_image_width, self.channels))
        return active_index, img_bytes, img_array

    def write_image(self, image_bytes):
        """
        Writes a new image to the inactive buffer and toggles the active index.
        The image should be provided as a numpy array.
        """
        if len(image_bytes) > self.image_size:
            image_bytes = image_bytes[:self.image_size]
        elif len(image_bytes) < self.image_size:
            image_bytes += b'\0' * (self.image_size - len(image_bytes))

        active_index = self.read_active_index()
        new_index = 1 - active_index  # Toggle active index
        image_offset = 4 + new_index * self.image_size
        self.dual_shm.seek(image_offset)
        self.dual_shm.write(image_bytes)
        self.dual_shm.seek(0)
        self.dual_shm.write(new_index.to_bytes(4, "little"))
        self.dual_shm.flush()
