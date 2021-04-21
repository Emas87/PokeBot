import logging
import os
import cv2
import numpy as np
import wx
import time


class Finder:
    def __init__(self, debug=False):
        self.logger = logging.getLogger(__name__)
        self.base = 'images/test1.png'
        self.templates = ('images/red_gem_left.png',)
        self.debug = debug

    def find_images(self, base_cv_rgb, templates_cv, offset=(0, 0), threshold=0.85, color=False, path=False):

        # Setting method
        method = cv2.TM_CCOEFF_NORMED

        # Read the base images and turning it to gray scale
        if path:
            self.logger.debug(base_cv_rgb)
            base_cv_rgb = cv2.imread(base_cv_rgb)

        if not color:
            gray = cv2.cvtColor(base_cv_rgb, cv2.COLOR_BGR2GRAY)
        else:
            gray = base_cv_rgb
        # look for images
        rectangles = []
        centers = []
        for image in templates_cv:

            if path:
                # read image to look for
                image = cv2.imread(image)

            # read image to look for
            if not color:
                template = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                template = image

            # Step 2: Get the size of the template. This is the same size as the match.
            height, width = template.shape[:2]

            # look for several matches
            try:
                result = cv2.matchTemplate(gray, template, method)
            except cv2.error:
                self.logger.error("Something went wrong with matchTemplate using template number: " +
                                  str(templates_cv.index(image)))
                return 0, 0, False

            # get locations of all omages above threshold
            loc = np.where(result >= threshold)

            # Draw rectangles frop each location
            for point in zip(*loc[::-1]):
                # top-left, width, height
                rectangles.append((point[0] + offset[0], point[1] + offset[1], width, height))
                # Store centers of rectangles
                centers.append((point[0] + offset[0] + int(width / 2), point[1] + offset[1] + int(height / 2)))

        final_rectangles = []
        final_centers = []

        # delete repeated rectangles
        for i in range(0, len(rectangles)):
            matches = 0
            for j in range(0, len(rectangles)):
                matches = 0
                if i < j:
                    for k in range(0, len(rectangles[i])):
                        if abs(rectangles[i][k] - rectangles[j][k]) <= 10:
                            matches += 1
                    if matches == 4:
                        break
            if matches == 4:
                continue
            final_rectangles.append(rectangles[i])
            final_centers.append(centers[i])

        final_rectangles = sorted(final_rectangles)
        final_centers = sorted(final_centers)

        # Display the original image with the rectangle around the match for testing purposes.
        if self.debug:
            print("Rectangles = " + str(len(final_rectangles)))
            for rentangle in final_rectangles:
                point, width, height = (rentangle[0], rentangle[1]), rentangle[2], rentangle[3]
                start_point = (point[0] + offset[0], point[1] + offset[1])
                end_point = (point[0] + offset[0] + width, point[1] + offset[1] + height)
                color_r = (0, 0, 255)
                thickness = 2
                cv2.rectangle(base_cv_rgb, start_point, end_point, color_r, thickness)

            cv2.imshow('output', base_cv_rgb)

        # The image is only displayed if we call this, for testing purposes.
            cv2.waitKey(0)

        return final_rectangles, final_centers, True

    def draw_rentangles(self, rectangles):
        self.logger.debug(len(rectangles))
        app = wx.App()
        if app:
            pass
        dc = wx.ScreenDC()
        dc.StartDrawingOnTop(None)
        dc.SetPen(wx.Pen('red', 2))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        # dc.DrawRectangleList(rectangles)
        for rectangle in rectangles:
            dc.DrawRectangle(rectangle)
            time.sleep(0.05)
            dc.DrawRectangle(rectangle)

    @staticmethod
    def load_image(image_path):
        return cv2.imread(image_path)


if __name__ == "__main__":
    finder = Finder(debug=True)
    templates = [os.path.abspath(os.path.join('images', 'Mining', path)) for path in os.listdir('images/Mining')]
    files = [os.path.abspath(os.path.join('images', path)) for path in os.listdir('images')]
    finder.debug = True
    for test_file in files:
        if "test" in test_file:
            base = test_file
            _, rentangles, status = finder.find_images(base, templates, threshold=0.6, path=True)
            # finder.draw_rentangles(rentangles)
