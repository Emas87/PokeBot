import logging
from ctypes import windll

import pywintypes
from PIL import ImageGrab, Image
import win32gui
import win32ui
import time
import numpy as np


class ScreenReader:
    def __init__(self, program_title='PokeММO.exe', debug=False):
        self.logger = logging.getLogger(__name__)
        self.program_title = program_title
        self.debug = debug

    def foreground_screenshot(self):
        window_handle = win32gui.FindWindow(None, self.program_title.lower())
        win32gui.SetForegroundWindow(window_handle)
        bbox = win32gui.GetWindowRect(window_handle)
        img = ImageGrab.grab(bbox)
        # convert PIL image to ndarray required for opencv
        img = np.array(img)
        return img

    @staticmethod
    def get_all_screen():
        img = ImageGrab.grab()
        # convert PIL image to ndarray required for opencv
        img = np.array(img)
        return img

    def get_windows_position(self):
        window_handle = win32gui.FindWindow(None, self.program_title.lower())
        bbox = win32gui.GetWindowRect(window_handle)
        return bbox[0], bbox[1]

    @staticmethod
    def get_mouse_position():
        position = win32gui.GetCursorPos()
        logging.info(position)
        time.sleep(1)

    def background_screenshot(self):
        # Get infromation of the windows program
        window_handle = win32gui.FindWindow(None, self.program_title.lower())
        if window_handle == 0:
            return None

        bbox = win32gui.GetWindowRect(window_handle)

        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        # setup screenshot
        wdc = win32gui.GetWindowDC(window_handle)
        dcobj = win32ui.CreateDCFromHandle(wdc)
        cdc = dcobj.CreateCompatibleDC()
        databitmap = win32ui.CreateBitmap()
        databitmap.CreateCompatibleBitmap(dcobj, width, height)
        cdc.SelectObject(databitmap)

        # Take Screenshot
        windll.user32.PrintWindow(window_handle, cdc.GetSafeHdc(), 0)

        # Convert bitmap to PIL image
        bmpinfo = databitmap.GetInfo()
        bmpstr = databitmap.GetBitmapBits(True)

        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        if self.debug:
            databitmap.SaveBitmapFile(cdc, 'screenshot.bmp')

        # Clsoe handlers
        win32gui.DeleteObject(databitmap.GetHandle())
        cdc.DeleteDC()
        dcobj.DeleteDC()
        win32gui.ReleaseDC(window_handle, wdc)

        # convert PIL image to ndarray required for opencv
        open_cv_image = np.array(img)
        return open_cv_image


if __name__ == "__main__":
    screen_reader = ScreenReader()
    # screen_reader.foreground_screenshot()
    screen_reader.background_screenshot()
    print(screen_reader.get_windows_position())
    while True:
        screen_reader.get_mouse_position()
