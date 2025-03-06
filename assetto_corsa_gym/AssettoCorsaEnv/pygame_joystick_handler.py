import logging

class JoystickHandler:
    def __init__(self):
        self._pygame = None
        self._joystick = None
        self.logger = logging.getLogger(__name__)

    @property
    def pygame(self):
        """Lazy-load pygame only when needed."""
        if self._pygame is None:
            import pygame
            self._pygame = pygame
        return self._pygame

    def initialize(self):
        """Initialize pygame and the joystick."""
        pg = self.pygame  # Trigger lazy import
        pg.display.init()
        pg.joystick.init()

        if pg.joystick.get_count() > 0:
            self._joystick = pg.joystick.Joystick(0)
            self._joystick.init()
            logger.info(self._joystick.get_init())
            logger.info(self._joystick.get_id())
            logger.info(self._joystick.get_name())
            logger.info(self._joystick.get_numaxes())
            logger.info(self._joystick.get_numballs())
            logger.info(self._joystick.get_numbuttons())
            logger.info(self._joystick.get_numhats())
            self.logger.info(f"Joystick initialized: {self._joystick.get_name()}")
        else:
            self.logger.warning("No joystick detected!")
            self._joystick = None  # Ensure it's None if not found

    def read_inputs(self):
        """Reads joystick inputs if available."""
        if self._joystick:
            self.pygame.event.pump()
            return {
                "steerAngleManual": self._joystick.get_axis(0),
                "accStatusManual": self._joystick.get_axis(1),
                "brakeStatusManual": self._joystick.get_axis(2),
            }
        return {}

    def is_initialized(self):
        """Check if joystick is available."""
        return self._joystick is not None
