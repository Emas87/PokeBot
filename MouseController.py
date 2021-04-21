import logging
import mouse
import time


class MouseController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.click_delay = 0.5
        mouse.on_click(self.report_position, args=())

    def report_position(self):
        x, y = mouse.get_position()
        self.logger.info("Mouse position: " + str(x) + ", " + str(y))

    def click(self, x=None, y=None):
        if x is None or y is None:
            x, y = mouse.get_position()
        x = int(x)
        y = int(y)
        mouse.move(x, y)
        mouse.press(button='left')
        time.sleep(self.click_delay)
        mouse.release(button='left')

    def drag(self, x1, y1, x2, y2):
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)
        mouse.move(x1, y1)
        mouse.drag(x1, y1, x2, y2, duration=self.click_delay)
