import sys
from Finder import Finder
from ImageDict import ImageDict
from ScreenReader import ScreenReader
from MouseController import MouseController
import time
import json
import logging
from directkeys import release_key, press_key
from multiprocessing import Process, Manager

translate = []

SWEET = (514, 48)
FIGHT = (398, 703)
BAG = (498, 703)
POKEMON = (398, 803)
RUN = (498, 803)


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
        self.searching = None
        self.fight_p = None
        self.nomore_pp_p = None
        self.goback_p = None

        # variables
        self.enter_exit_waiting_time = 1.1
        self.process_busywaiting_time = 2

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

    def train(self, location, times=6, skip_move=False, out_image=('out1',)):
        # move pokemmo to foreground
        self.mouse_controller.click(514, 148)
        # Heal
        self.heal_pokemon()
        # Move to location
        self.move_to(location)
        for _ in range(0, times):
            self.fight(skip_move=skip_move, out_image=out_image)

        # Instead of moving back, teleport
        # location = [('down', 5), (self.enter_exit_waiting_time, 1), ('down', 1), ('right', 25), ('down', 6),
        #             ('right', 6), ('down', 1)]
        # self.move_to(location, back=True)
        # Press 9 where teleport is
        cmd = [('9', 2)]
        self.move_to(cmd)

        # self.mouse_controller.click(657, 55)
        # self.mouse_controller.click(657, 55)

    def move_rl(self, search_value, right=3, left=3, pressing_time=0.15, run=False):
        while True:
            # Run from fights
            if run:
                self.mouse_controller.click(610, 757)
            state = search_value[0]
            if state == "idle":
                print("Stop moving from move_rl with value of " + str(search_value))
                sys.stdout.flush()
                time.sleep(self.process_busywaiting_time)
            elif state == "run":
                location = [('right', right), ('left', left)]
                self.move_to(location, pressing_time=pressing_time)
            elif state == "end":
                search_value[1] = "search_end"
                break

    def move_ud(self, search_value, up=3, down=3, pressing_time=0.15):
        while True:
            state = search_value[0]
            if state == "idle":
                print("Stop moving from move_rl with value of " + str(search_value))
                sys.stdout.flush()
                time.sleep(self.process_busywaiting_time)
            elif state == "run":
                location = [('down', down), ('up', up)]
                self.move_to(location, pressing_time=pressing_time)
            elif state == "end":
                search_value[1] = "search_end"
                break

    def is_infight(self, fight_value, out_image):
        threshold = 0.8
        while True:
            state = fight_value[0]
            if state == "run":
                # Mouse position: 398, 703
                fight_start, fight_centers_save = self.is_it("fight", threshold=threshold)
                fight_start2, fight_centers_save2 = self.is_it("fight2", threshold=threshold)

                # Fight until you found out that fight is finished
                if fight_start or fight_start2:

                    fight_value[1] = "fight_started"
                    print("Found a fight button")
                    sys.stdout.flush()
                    if fight_start2:
                        self.make_sure_click_is_done("fight2", fight_centers_save2, threshold=threshold)
                    else:
                        self.make_sure_click_is_done("fight", fight_centers_save, threshold=threshold)
                    # Mouse position: 399, 756
                    self.logger.info("Clicking again")
                    self.mouse_controller.click()
                    self.mouse_controller.click()

                    # Mouse position: 399, 756
                    self.logger.info("Clicking again")
                    self.mouse_controller.click()
                    self.mouse_controller.click()
                finish, out_centers_save = self.is_it(out_image, threshold=threshold)
                if finish:
                    fight_value[1] = "fight_ended"
                    sys.stdout.flush()
            elif state == "idle":
                time.sleep(self.process_busywaiting_time)
            elif state == "end":
                fight_value[1] = "fight_p_ended"
                break

    def nomore_pp(self, nopp_value):
        threshold = 0.8
        while True:
            state = nopp_value[0]
            if state == "run":
                # Mouse position: 398, 703
                no_pp_start, no_pp_centers_save = self.is_it("no_pp", threshold=threshold)
                no_pp2_start, no_pp2_centers_save = self.is_it("no_pp2", threshold=threshold)
                if no_pp_start or no_pp2_start:
                    # Pause other Processes
                    nopp_value[1] = "nopp"
                    print("sent nopp")
                    sys.stdout.flush()

            elif state == "end":
                nopp_value[1] = "nopp_end"
                print("Terminating nopp process")
                sys.stdout.flush()
                break
            elif state == "idle":
                time.sleep(self.process_busywaiting_time)

    def horde_search(self, horde_value):
        threshold = 0.8
        while True:
            state = horde_value[0]
            if state == "run":
                # Mouse position: 398, 703
                horde_start1, _ = self.is_it("horde", threshold=threshold)
                horde_start2, _ = self.is_it("horde1", threshold=threshold)
                if horde_start1 or horde_start2:
                    # Pause other Processes
                    horde_value[1] = "horde_found"
                    print("sent horde_found")
                    sys.stdout.flush()
                    self.press_run_button()
            elif state == "end":
                horde_value[1] = "horde_found_end"
                print("Terminating nopp process")
                sys.stdout.flush()
                break
            elif state == "idle":
                time.sleep(self.process_busywaiting_time)

    def control_p(self, jobs):
        # jobs = {process_name: (process, list)}
        # Control write in [0]
        # Control read from [1]
        # Starting process
        jobs["search"][1][0] = "run"
        jobs["fight_p"][1][0] = "run"
        jobs["nomore_pp_p"][1][0] = "run"
        jobs["horde_p"][1][0] = "run"
        jobs["horde_p"][1][0] = "run"

        while True:
            nopp_state = jobs["nomore_pp_p"][1][1]
            fight_state = jobs["fight_p"][1][1]
            horde_state = jobs["horde_p"][1][1]
            if nopp_state == 'nopp':
                jobs["search"][1][0] = "end"
                jobs["fight_p"][1][0] = "end"
                jobs["nomore_pp_p"][1][0] = "end"
                jobs["horde_p"][1][0] = "end"

                print("NoPP was received, ending all processes")
                sys.stdout.flush()

                # Press Run button
                self.press_run_button()

                # dFinish Control
                break
            elif horde_state == "horde_found":
                # Stop fighting cycle
                jobs["search"][1][0] = "idle"
                jobs["fight_p"][1][0] = "idle"

                # Run from battle
                self.press_run_button()

                # Continue fighting cycle
                jobs["search"][1][0] = "run"
                jobs["fight_p"][1][0] = "run"

                # Reset state
                jobs["horde_p"][1][1] = ''
            elif fight_state == "fight_started":
                jobs["search"][1][0] = "idle"
                # Reset state
                jobs["fight_p"][1][1] = ''
            elif fight_state == "fight_ended":
                jobs["search"][1][0] = "run"
                # Reset state
                jobs["search"][1][1] = ''

    def farm_money(self):
        # Go to battle front waterfall
        self.mouse_controller.click(514, 148)
        self.heal_pokemon()
        location = [('down', 5), (bot.enter_exit_waiting_time, 1), ('1', 1), ('right', 13),
                    ('down', 3), ('right', 4), ('down', 1), ('a', 6)]
        self.move_to(location)
        jobs = {}
        manager = Manager()
        search_value = manager.list()
        search_value.append("idle")
        search_value.append("")

        # search for pokemon
        searching = Process(name='search', target=self.move_rl,
                            args=(search_value, 4, 4))
        searching.start()
        jobs["search"] = (searching, search_value)

        # fight
        fight_value = manager.list()
        fight_value.append("idle")
        fight_value.append("")
        fight_p = Process(name='fight', target=self.is_infight,
                          args=(fight_value, 'out1'))
        fight_p.start()
        jobs["fight_p"] = (fight_p, fight_value)

        # No more PP
        no_pp_value = manager.list()
        no_pp_value.append("idle")
        no_pp_value.append("")
        nomore_pp_p = Process(name='pp', target=self.nomore_pp, args=(no_pp_value, ))
        nomore_pp_p.start()
        jobs["nomore_pp_p"] = (nomore_pp_p, no_pp_value)

        # No more PP
        horde_value = manager.list()
        horde_value.append("idle")
        horde_value.append("")
        horde_p = Process(name='pp', target=self.horde_search, args=(horde_value,))
        horde_p.start()
        jobs["horde_p"] = (horde_p, horde_value)

        self.control_p(jobs)

        # Go Back if no more PP
        time.sleep(3)
        # Instead of moving back, teleport
        # location = [('down', 5), (self.enter_exit_waiting_time, 1), ('down', 1), ('right', 24), ('down', 6),
        #             ('right', 24), ('down', 1)]
        # # Use repelent
        # self.mouse_controller.click(377, 52)
        #
        # self.move_to(location, back=True)

        # self.mouse_controller.click(657, 55)
        # self.mouse_controller.click(657, 55)
        cmd = [('9', 1)]
        self.move_to(cmd)

    def heal_pokemon(self):
        healed = False
        cmd_list = [('a', 1), (1, 1)]
        while not healed:
            healed, _ = self.is_it("healed", category="message")
            self.move_to(cmd_list)
        self.logger.info("Healed Pokemon")

    def make_sure_click_is_done(self, image, image_centers_save, threshold=0.85):
        while True:
            x = image_centers_save[0][0]
            y = image_centers_save[0][1]
            self.mouse_controller.click(x, y)
            self.logger.info("Click on button " + image)
            image_start, image_centers_save = self.is_it(image, threshold=threshold)
            if image_start:
                continue
            else:
                return True

    def fight(self, out_image=('out1',), skip_move=False):
        threshold = 0.8
        # Press 6 where sweet scent is
        cmd = [('6', 1)]
        self.move_to(cmd)
        # self.mouse_controller.click(514, 48)
        # self.mouse_controller.click(514, 48)
        time.sleep(4)
        finish = False
        while not finish:
            # Mouse position: 398, 703
            fight_start, fight_centers_save = self.is_it("fight", threshold=threshold)
            fight_start2, fight_centers_save2 = self.is_it("fight2", threshold=threshold)

            # Fight until you found out that fight is finished
            if fight_start or fight_start2:
                if fight_start2:
                    self.make_sure_click_is_done("fight2", fight_centers_save2, threshold=threshold)
                else:
                    self.make_sure_click_is_done("fight", fight_centers_save, threshold=threshold)

                # Mouse position: 399, 756
                self.logger.info("Clicking again")
                self.mouse_controller.click()
                self.mouse_controller.click()

                # Mouse position: 399, 756
                self.logger.info("Clicking again")
                self.mouse_controller.click()
                self.mouse_controller.click()
            elif skip_move:
                skip_start, _ = self.is_it("skip_move", threshold=threshold)
                # type A button twice to skip move learning
                if skip_start:
                    cmd_list = [('a', 3)]
                    self.move_to(cmd_list)

            finish, out_centers_save = self.is_it(out_image, threshold=threshold)

        self.logger.info("Out of battle")
        return True

    def keep_fighting(self):
        threshold = 0.8
        # Move pokemmo to foreground
        self.mouse_controller.click(514, 48)
        finish = False
        while not finish:
            # Mouse position: 398, 703
            fight_start, fight_centers_save = self.is_it("fight", threshold=threshold)
            fight_start2, fight_centers_save2 = self.is_it("fight2", threshold=threshold)

            # Fight until you found out that fight is finished
            if fight_start or fight_start2:
                if fight_start2:
                    self.make_sure_click_is_done("fight2", fight_centers_save2, threshold=threshold)
                else:
                    self.make_sure_click_is_done("fight", fight_centers_save, threshold=threshold)

                # Mouse position: 399, 756
                self.logger.info("Clicking again")
                self.mouse_controller.click()
                self.mouse_controller.click()

                # Mouse position: 399, 756 since I change the duration of the clic I think this is no longer needed
                # self.logger.info("Clicking again")
                # self.mouse_controller.click()
                # self.mouse_controller.click()
        self.logger.info("Out of battle")

    def is_it(self, images, threshold=0.85, category="button"):
        # Look for enemies
        centers = []
        if type(images) is str:
            _, centers, _ = self.get_boxes(category, image=self.image_dict[category][images], threshold=threshold)
        elif type(images) is tuple:
            for img in images:
                _, centers_temp, _ = self.get_boxes(category, image=self.image_dict[category][img], threshold=threshold)
                centers = centers + centers_temp

        if len(centers) > 0:
            return True, centers
        else:
            self.logger.debug("No " + str(images) + " in category " + category + ", found")
        return False, []

    def move_to(self, cmd_list, back=False, pressing_time=0.15):
        waiting_time = 0.3
        if back:
            cmd_list = reversed(cmd_list)

        for direction, times in cmd_list:
            if type(direction) is int or type(direction) is float:
                time.sleep(direction)
                continue
            key = self.config["key_binding"][direction][0]
            if back:
                key = self.config["key_binding"][direction][1]

            for i in range(0, times):
                self.logger.info("Press: " + key)
                press_key(key)
                time.sleep(pressing_time)
                release_key(key)
                time.sleep(waiting_time)
            time.sleep(waiting_time)

    def press_run_button(self):
        threshold = 0.8
        run_found = False
        while not run_found:
            run_found, run_centers_save = self.is_it("run", threshold=threshold)
            run2_found, run2_centers_save = self.is_it("run2", threshold=threshold)
            if run_found or run2_found:
                if run2_found:
                    run_centers_save = run2_centers_save
                self.make_sure_click_is_done("run", run_centers_save, threshold=threshold)
                # Mouse position: 399, 756
                self.logger.info("Clicking again Run button")
                self.mouse_controller.click()
                self.mouse_controller.click()

                # Mouse position: 399, 756
                self.logger.info("Clicking again Run button")
                self.mouse_controller.click()
                self.mouse_controller.click()
                break


if __name__ == "__main__":

    #    print(process.ProcessId, process.Name)
    bot = Bot(debug=False)
    mode = "FARM"
    skip_move_temp = False
    while True:
        if mode == 1:
            bot.keep_fighting()
        elif mode == 2 or mode == "FARM":
            bot.farm_money()
        elif mode == 3:
            time.sleep(1)
        elif mode == 5 or mode == "RL":
            # Search Pokemon right and left
            search_value1 = ["run", ""]
            bot.mouse_controller.click(514, 148)
            bot.move_rl(search_value1, right=3, left=3, pressing_time=0.3, run=True)
        elif mode == 6 or mode == "UD":
            # Search Pokemon left and right
            search_value1 = ["run", ""]
            bot.mouse_controller.click(514, 148)
            bot.move_ud(search_value1, up=3, down=3, pressing_time=0.3)
        elif mode == 7 or mode == "SPD":
            # SP Def and EXP, Hoenn Battle Front Hoenn
            loecation_temp = [('down', 5), (bot.enter_exit_waiting_time, 1), ('1', 1), ('right', 13),
                              ('down', 3), ('right', 6), ('down', 1), ('a', 6)]
            bot.train(loecation_temp, skip_move=skip_move_temp, times=6)
        elif mode == 8 or mode == "HP":
            # HP Hoenn Petalburg city
            loecation_temp = [('down', 5), (bot.enter_exit_waiting_time, 1), ('left', 5),  ('down', 6),
                              ('left', 3), ('a', 6)]
            bot.train(loecation_temp, skip_move=skip_move_temp)
        elif mode == 9 or mode == "DEF":
            # DEF Hoenn before victory road
            loecation_temp = [('down', 5), (bot.enter_exit_waiting_time, 1), ('down', 3), ('left', 7),
                              ('down', 3), ('a', 6)]
            bot.train(loecation_temp, skip_move=skip_move_temp)
        elif mode == 10 or mode == "SPA":
            # SP ATTACK Hoenn route 119
            loecation_temp = [('down', 5), (bot.enter_exit_waiting_time, 1), ('left', 11), ('down', 3)]
            bot.train(loecation_temp, skip_move=skip_move_temp, out_image=("out_route119", "out_route1192"))
        elif mode == 11 or mode == "SPE":
            # SPEED Kanto route 16
            loecation_temp = [('down', 5), (bot.enter_exit_waiting_time, 1), ('left', 28), ('down', 4), ('left', 16),
                              ('down', 7), ('left', 26), (bot.enter_exit_waiting_time, 1), ('1', 1), ('left', 6),
                              (bot.enter_exit_waiting_time, 1), ('left', 4), ('down', 10), ('right', 2)]
            bot.train(loecation_temp, skip_move=skip_move_temp, out_image=('out_route16', 'out_route162'))
        elif mode == 12 or mode == "ATK":
            # ATTACK Hoenn route 120
            loecation_temp = [('down', 5), (bot.enter_exit_waiting_time, 1), ('down', 1), ('right', 5),  ('up', 4),
                              ('right', 22), ('down', 4), ('right', 28)]
            bot.train(loecation_temp, skip_move=skip_move_temp)
