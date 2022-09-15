"""
Handler is a package for creating files in an object-oriented way,
allowing extendability to any file system.

Copyright (C) 2021 Gabriel Fontenelle Senno Silva

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Should there be a need for contact the electronic mail
`handler <at> gabrielfontenelle.com` can be used.
"""
import base64
import cv2
import numpy as np
import warnings
from io import BytesIO

from PIL import Image as PillowImageClass
from wand.display import display as wand_display
from wand.image import Image as WandImageClass

__all__ = [
    "ImageEngine",
    "OpenCVImage",
    "PillowImage",
    "WandImage"
]


class ImageEngine:
    """
    Class that standardized methods of different image manipulators.
    """
    image = None
    """
    """

    def __init__(self, buffer):
        """
        Method to instantiate the current class using a buffer for the image content as a source
        for manipulation by the class to be used.
        """
        self.source_buffer = buffer

        self.prepare_image()

    def change_color(self, colorspace="gray"):
        """
        Method to change the color space of the current image.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method change_color should be override in child class.")

    def clone(self):
        """
        Method to copy the current image object and return it.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method clone should be override in child class.")

    def crop(self, width, height):
        """
        Method to crop the current image object.
        This method must affect the current image object.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method crop should be override in child class.")

    @staticmethod
    def get_aspect_ratio(width, height):
        """
        Method to obtain the width and height proportion (aspect ratio) to use in transformations.
        """
        ratio_width = width / height
        ratio_height = height / width

        return ratio_width, ratio_height

    def get_base64(self, encode_format="jpeg"):
        """
        Method to obtain the base64 representation for the content of the current image object.
        """
        content = self.get_bytes(encode_format)

        # Convert buffer to base64 string representation in ASCII
        return base64.b64encode(content).decode('ascii')

    def get_buffer(self, encode_format="jpeg"):
        """
        Method to get a buffer IO from the current image.
        """
        return BytesIO(self.get_bytes(encode_format=encode_format))

    def get_bytes(self, encode_format="jpeg"):
        """
        Method to obtain the bytes' representation for the content of the current image object.
        This method must return bytes already compressed by format.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method get_bytes_from_image should be override in child class.")

    def get_relative_size(self, width, height, new_width, new_height, constraint=True):
        """
        Method to obtain a new size relative to width and height that respect the aspect ratio
        keeping it constraining to new_width and new_height or not.
        """
        # Get current ratio from width and height.
        ratio = self.get_aspect_ratio(width, height)

        # Use ratio to get new size keep or not the new size constraining to new values.
        if (constraint and width < height) or (not constraint and width >= height):
            a = 1
            b = ratio[0]
            size = new_height
        else:
            a = ratio[1]
            b = 1
            size = new_width

        return int(ratio[0] * a * size), int(b * ratio[1] * size)

    def get_size(self):
        """
        Method to obtain the size of current image.
        This method should return a tuple with width and height.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method get_size should be override in child class.")

    def prepare_image(self):
        """
        Method to prepare the image using the stored buffer as the source.
        This method should use `self.source_buffer` and `self.image` to set the current image object.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method prepare_image should be override in child class.")

    def resize(self, width, height, constraint=True, keep_ratio=False, crop=False):
        """
        Method to scale the current image object implement some logic as keeping ratio or cropping the current image.
        This method must affect the current image object.
        This method should be overwritten in child class.
        """
        # Sanitize width and height to int
        width = int(width)
        height = int(height)

        if keep_ratio and crop:
            warnings.warn(
                "Using parameters keep_ratio and crop together will result in only keep_ratio being used."
            )

        current_width, current_height = self.get_size()

        if keep_ratio:
            # Resize image keeping the aspect ratio constraining or not to new width and height.
            width, height = self.get_relative_size(
                width=current_width,
                height=current_height,
                new_width=width,
                new_height=height,
                constraint=constraint
            )

        elif crop:
            # Resize image cropping it to have the same aspect ratio as the new width and height.
            ratio_width, ratio_height = self.get_aspect_ratio(width, height)
            self.crop(int(ratio_width * current_height), int(ratio_height * current_width))

        # Scale image with the new width, height
        self.scale(width, height)

    def scale(self, width, height):
        """
        Method to scale the current image object without implementing additional logic.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method scale should be override in child class.")

    def show(self):
        """
        Method to display the image for debugging purposes.
        This method should be overwritten in child class with the appropriate mode of displaying the image.
        """
        raise NotImplementedError("The method show should be override in child class.")


class OpenCVImage(ImageEngine):
    """
    This class depends on OpenCV being installed in the system.
    In OpenCV the image is basically a numpy matrix.
    """

    def change_color(self, colorspace="gray"):
        """
        Method to change the color space of the current image.
        """
        # Convert to grey scale
        colorscheme = {
            "gray": cv2.COLOR_BGR2GRAY,
            "Lab": cv2.COLOR_BGR2LAB,
            "YCrCb": cv2.COLOR_BGR2YCrCb,
            "HSV": cv2.COLOR_BGR2HSV
        }

        self.image = cv2.cvtColor(self.image, colorscheme[colorspace])

    def clone(self):
        """
        Method to copy the current image object and return it.
        """
        return self.image.copy()

    def crop(self, width, height):
        """
        Method to crop the current image object.
        """
        current_width, current_height = self.get_size()

        # Set `top` based on center gravity
        top = current_height // 2 - height // 2

        # Set `left` based on center gravity
        left = current_width // 2 - width // 2

        self.image = self.image[top:top+height, left:left+width]

    def get_bytes(self, encode_format="jpeg"):
        """
        Method to obtain the bytes' representation for the content of the current image object.
        """
        formats = {
            "jpeg": ".jpg"
        }
        success, buffer = cv2.imencode(formats[encode_format], self.image)

        if not success:
            raise ValueError(f"Could not convert image to format {encode_format} in OpenCVImage.get_bytes_from_image.")

        return buffer

    def get_size(self):
        """
        Method to obtain the size of current image.
        OpenCV shape attribute is a tuple (height, width, channels).
        """
        return self.image.shape[1], self.image.shape[0]

    def prepare_image(self):
        """
        Method to prepare the image using the stored buffer as the source.
        """
        # convert to numpy array
        array = np.asarray(bytearray(self.source_buffer.read()), dtype="uint8")

        self.image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)

    def scale(self, width, height):
        """
        Method to scale the current image object without implementing additional logic.
        """
        self.image = cv2.resize(self.image, (width, height), interpolation=cv2.INTER_AREA)

    def show(self):
        """
        Method to display the image for debugging purposes.
        """
        cv2.imshow("Image", self.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


class PillowImage(ImageEngine):

    def change_color(self, colorspace="gray"):
        """
        Method to change the color space of the current image.
        """
        # Convert to grey scale
        colorscheme = {
            "gray": "L",
            "Lab": "",
            "YCrCb": "",
            "HSV": ""
        }
        self.image = self.image.convert(colorscheme[colorspace])

    def clone(self):
        """
        Method to copy the current image object and return it.
        """
        return self.image.copy()

    def crop(self, width, height):
        """
        Method to crop the current image object.
        """
        current_width, current_height = self.get_size()

        # Set `top` based on center gravity
        top = current_height // 2 - height // 2

        # Set `left` based on center gravity
        left = current_width // 2 - width // 2

        self.image = self.image.crop((top, left, width, height))

    def get_buffer(self, encode_format="jpeg"):
        """
        Method to get a buffer IO from the current image.
        For optimization this function performance the same as get_bytes_from_image except by the return of
        BytesIO without reading bytes content.
        """
        output = BytesIO()
        self.image.save(output, format=encode_format)
        return output

    def get_bytes(self, encode_format="jpeg"):
        """
        Method to obtain the bytes' representation for the content of the current image object.
        """
        output = BytesIO()
        self.image.save(output, format=encode_format)
        return output.read()

    def get_size(self):
        """
        Method to obtain the size of current image.
        This method should return a tuple with width and height.
        """
        return self.image.size[0], self.image.size[1]

    def prepare_image(self):
        """
        Method to prepare the image using the stored buffer as the source.
        """
        self.image = PillowImageClass.open(fp=self.source_buffer)

    def scale(self, width, height):
        """
        Method to scale the current image object without implementing additional logic.
        """
        self.image = self.image.resize((width, height))

    def show(self):
        """
        Method to display the image for debugging purposes.
        """
        self.image.show()


class WandImage(ImageEngine):
    """
    Class that standardized methods of Wand library.
    This class depends on Wand being installed in the system.
    """

    def change_color(self, colorspace="gray"):
        """
        Method to change the color space of the current image.
        """
        colorscheme = {
            "gray": "gray",
            "Lab": "",
            "YCrCb": "",
            "HSV": ""
        }
        # Convert to grey scale
        self.image.transform_colorspace(colorscheme[colorspace])

    def clone(self):
        """
        Method to copy the current image object and return it.
        """
        return self.image.clone()

    def crop(self, width, height):
        """
        Method to crop the current image object.
        """
        self.image.crop(width=width, height=height, gravity='center')

    def get_bytes(self, encode_format="jpeg"):
        """
        Method to obtain the bytes' representation for the content of the current image object.
        """
        return self.image.make_blob(encode_format)

    def get_size(self):
        """
        Method to obtain the size of current image.
        """
        return self.image.size[0], self.image.size[1]

    def prepare_image(self):
        """
        Method to prepare the image using the stored buffer as the source.
        """
        self.image = WandImageClass(file=self.source_buffer)

    def scale(self, width, height):
        """
        Method to scale the current image object without implementing additional logic.
        """
        self.image.sample(width, height)

    def show(self):
        """
        Method to display the image for debugging purposes.
        """
        wand_display(self.image)
