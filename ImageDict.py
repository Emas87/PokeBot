import logging
import os
import glob

from Finder import Finder


class ImageDict(dict):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def load_images(self, config):
        # Will read all config entries in img_categories, and from that look for images, any image that doesnt follow
        # config pattern wont be loaded
        for category, directories in config["img_categories"].items():
            for directory, files in directories.items():
                for image in files:
                    files_path = os.path.abspath(os.path.join("images", directory, image))
                    glob_files = glob.glob(files_path)
                    if len(glob_files) < 1:
                        self.logger.error("file pattern didn't match: " + files_path)
                    for glob_file in glob_files:
                        name = os.path.basename(glob_file).split(".")[0]
                        self.add(glob_file, category, name)

    def add(self, image, key, name):
        # Add a image to the image dict
        loaded_image = Finder.load_image(image)
        if key not in self:
            self[key] = {name: loaded_image}
        else:
            self[key][name] = loaded_image

    def get(self, category):
        final_list = []
        for key, value in self[category].items():
            final_list.append(value)
        return final_list
