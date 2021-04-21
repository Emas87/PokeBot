import sys
from Finder import Finder
from ImageDict import ImageDict
from ScreenReader import ScreenReader
from MouseController import MouseController
import time
import multiprocessing
import numpy
import json
import logging
from directkeys import release_key, press_key
translate = []


class Bot:
    def __init__(self, debug=False):
        if debug:
            level = logging.DEBUG
        else:
            level = logging.INFO
        logging.basicConfig(filename='logger.log', level=level, filemode="w")

        self.logger = logging.getLogger()
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.image_dict = ImageDict()
        self.mouse_controller = MouseController()
        self.debug = debug
        self.finder = Finder(debug=debug)
        self.screen_reader = ScreenReader(debug=debug)

        # Cofnig file
        with open("config/config.json") as input_file:
            self.config = json.load(input_file)
        self.image_dict.load_images(self.config)

        # Processes
        self.control_process = None

        # variables
        self.enter_exit_waiting_time = 1.1

    def get_boxes(self, key, image=None, color=False, threshold=0.85):
        # Will get all matches for the images inside the dict with key 'key'
        # screen_shot = self.screen_reader.background_screenshot()
        screen_shot = self.screen_reader.get_all_screen()
        # This takes a little bit more time
        # screen_shot = self.screen_reader.foreground_screenshot()
        if screen_shot is None:
            self.logger.error("Couldn't get a screenshot of the program")
            return [], [], False
        # windows_pos = self.screen_reader.get_windows_position()
        windows_pos = (0, 0)

        if image is not None:
            final_rectangles, final_centers, status = self.finder.find_images(screen_shot, [image],
                                                                              offset=(windows_pos[0], windows_pos[1]),
                                                                              color=color, threshold=threshold)
        else:
            final_rectangles, final_centers, status = self.finder.find_images(screen_shot, self.image_dict.get(key),
                                                                              offset=(windows_pos[0], windows_pos[1]),
                                                                              color=color, threshold=threshold)

        return final_rectangles, final_centers, status

    def start(self):
        # self.control_process = multiprocessing.Process(target=self.control_mining)
        # self.control_process.start()

        self.mouse_controller.click(514, 148)
        self.go_to_cave()
        time.sleep(1)
        self.provoke_fight()
        self.provoke_fight()
        self.provoke_fight()
        self.provoke_fight()
        self.provoke_fight()
        self.provoke_fight()
        self.provoke_fight()
        self.provoke_fight()
        self.go_to_pokecenter()
        self.heal_pokemon()

    def stop(self):
        self.control_process.terminate()

    def go_to_cave(self):
        cmd_list = [('left', 2), ('down', 5)]
        self.move_to(cmd_list)
        time.sleep(self.enter_exit_waiting_time)
        cmd_list = [('down', 15), ('right', 4), ('down', 9), ('left', 1), ('down', 8),
                    ('right', 7), ('down', 10), ('left', 3), ('up', 3)]
        self.move_to(cmd_list)
        self.logger.info("Arrived to cave")

    def heal_pokemon(self):
        cmd_list = [('a', 1)]
        self.move_to(cmd_list)
        time.sleep(1)
        self.move_to(cmd_list)
        time.sleep(1)
        self.move_to(cmd_list)
        time.sleep(1)
        self.move_to(cmd_list)
        time.sleep(1)
        self.move_to(cmd_list)
        time.sleep(1)
        self.move_to(cmd_list)
        time.sleep(1)
        self.move_to([('down', 1)])
        self.move_to(cmd_list)
        self.logger.info("Healed Pokemon")

    def make_sure_click_is_done(self, image, image_centers_save, threshold=0.85):
        while True:
            x = image_centers_save[0][0]
            y = image_centers_save[0][1]
            self.mouse_controller.click(x, y)
            self.logger.info("Click on button " + image)
            image_start, image_centers_save = self.is_it("fight", threshold=threshold)
            if image_start:
                continue
            else:
                return True

    def provoke_fight(self):
        threshold = 0.8
        self.mouse_controller.click(514, 48)
        time.sleep(4)
        finish = False
        while not finish:
            # Mouse position: 398, 703
            fight_start, fight_centers_save = self.is_it("fight", threshold=threshold)
            if fight_start:
                self.make_sure_click_is_done("fight", fight_centers_save, threshold=threshold)
            surf_start, surf_centers_save = self.is_it("surf", threshold=threshold)
            if surf_start:
                self.make_sure_click_is_done("surf", surf_centers_save, threshold=threshold)
                time.sleep(1)
                # Mouse position: 399, 756
                self.logger.info("Clicking again")
                self.mouse_controller.click()
                self.mouse_controller.click()
            finish, out_centers_save = self.is_it("out", threshold=threshold)
        self.logger.info("Out of battle")
        return True

    def is_it(self, image, threshold):
        # Look for enemies
        rec, centers, status = self.get_boxes("button", image=self.image_dict["button"][image], threshold=threshold)
        if len(centers) > 0:
            return True, centers
        else:
            self.logger.debug("No " + image + " button found")
        return False, []

    def go_to_pokecenter(self):
        cmd_list = [('down', 1)]
        self.move_to(cmd_list)
        time.sleep(self.enter_exit_waiting_time)
        cmd_list = [('down', 1), ('left', 2), ('down', 7), ('down', 15), ('right', 4), ('down', 9), ('left', 1), ('down', 8),
                    ('right', 7), ('down', 10), ('left', 3)]
        self.move_to(cmd_list, back=True)
        self.logger.info("Arrived to pokecenter")

    def move_to(self, cmd_list, back=False):
        waiting_time = 0.3
        delay_time = 0.15

        if back:
            cmd_list = reversed(cmd_list)

        for direction, times in cmd_list:
            key = self.config["key_binding"][direction][0]
            if back: 
                key = self.config["key_binding"][direction][1]
            for i in range(0, times):
                self.logger.info("Press: " + key)
                press_key(key)
                time.sleep(delay_time)
                release_key(key)
                time.sleep(waiting_time)
            time.sleep(waiting_time)


if __name__ == "__main__":
    import wmi

    #    print(process.ProcessId, process.Name)
    bot = Bot(debug=False)
    while True:
        bot.start()
    # bot.keep_drawing_boxes("tools")
