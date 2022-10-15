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
import warnings
from io import BytesIO

from PIL import Image as PillowImageClass, ImageChops, ImageSequence as PillowSequence
from wand.display import display as wand_display
from wand.image import Image as WandImageClass
from wand.color import Color

__all__ = [
    "ImageEngine",
    "PillowImage",
    "SequenceEngine",
    "WandImage"
]


class ImageEngine:
    """
    Class that standardized methods of different image manipulators.
    """
    image = None
    """
    Attribute where the current image converted from buffer is stored.
    """
    class_image = None
    """
    Attribute used to store the class reference responsible to create an image.
    This attribute should be override by child class.
    """

    def __init__(self, buffer):
        """
        Method to instantiate the current class using a buffer for the image content as a source
        for manipulation by the class to be used.
        """
        self.source_buffer = buffer

        if buffer:
            self.prepare_image()

    def append_to_sequence(self, images):
        """
        Method to append a list of images to the current image, if the current image is not a sequence
        this method should convert it to a sequence.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method append_to_sequence should be override in child class.")

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

    @classmethod
    def create_empty_image(cls):
        """
        Method to instantiate the current class with an empty image.
        """
        if not hasattr(cls, 'class_image'):
            raise NotImplementedError(f"The current class {cls.__name__} don`t implement the attribute `class_image`.")

        return cls.create_from_image(image=cls.class_image())

    @classmethod
    def create_from_image(cls, image):
        """
        Method to instantiate the current class using a preprocessed image of the same class.
        """
        self = cls(buffer=None)
        self.image = image

        return self
    
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

    def has_sequence(self):
        """
        Method to verify if image has multiple frames, e.g `.gif`, or distinct sizes, e.g `.ico`.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method has_sequence should be override in child class.")

    def has_transparency(self):
        """
        Method to verify if image has a channel for transparency.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method has_transparency should be override in child class.")

    def prepare_image(self):
        """
        Method to prepare the image using the stored buffer as the source.
        This method should use `self.source_buffer` and `self.image` to set the current image object.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method prepare_image should be override in child class.")

    def resample(self, percentual=10, encode_format="webp"):
        """
        Method to re sample the image sequence with only the percentual amount of items distributed through the image
        sequences.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method resample should be override in child class.")

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

    def trim(self, color=None):
        """
        Method to trim the current image object.
        This method must affect the current image object.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method trim should be override in child class.")


class PillowImage(ImageEngine, SequenceEngine):
    """
    Class that standardized methods of Pillow library.
    """

    class_image = PillowImageClass
    """
    Attribute used to store the class reference responsible to create an image.
    """

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

    def create_sequence_image(self, images):
        """
        Method to create a new image with sequence using a list of images.
        """
        pass

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

    def get_frame(self, index):
        """
        Method to obtain an engine from a specified index frame of current image object.
        This method should return None if no frame exists with given index.
        """
        if self.sequence_image is None:
            self.prepare_sequence_image()

        try:
            image = self.sequence_image[index]
            return self.create_from_image(image=image)

        except (StopIteration, IndexError):
            return None

    def get_size(self):
        """
        Method to obtain the size of current image.
        This method should return a tuple with width and height.
        """
        return self.image.size[0], self.image.size[1]

    def get_total_frames(self):
        """
        Method to obtain the total amount of frames in image.
        This method should return 1 if the current image is not iterable.
        """
        return len(self.sequence_image)

    def has_transparency(self):
        """
        Method to verify if image has a channel for transparency.
        """
        return self.image.info.get("transparency") is not None

    def prepare_image(self):
        """
        Method to prepare the image using the stored buffer as the source.
        """
        self.image = self.class_image.open(fp=self.source_buffer)

    def prepare_sequence_image(self):
        """
        Method to prepare the sequence object from image.
        """
        self.sequence_image = PillowSequence.Iterator(self.image)

    def scale(self, width, height):
        """
        Method to scale the current image object without implementing additional logic.
        """
        self.image = self.image.resize((width, height), resample=self.class_image.Resampling.LANCZOS)

    def show(self):
        """
        Method to display the image for debugging purposes.
        """
        self.image.show()

    def trim(self, color=None):
        """
        Method to trim the current image object.
        The parameter color is used to indicate the color to trim else it will use transparency.
        """
        if color:
            background = self.class_image.new(self.image.mode, self.image.size, color=color)
            bounding_border = ImageChops.difference(self.image, background).getbbox()
        elif self.has_transparency():
            # Trim transparency
            bounding_border = self.image.getchannel("A").getbbox()
        else:
            raise ValueError("Cannot trim image because no color was informed and no alpha channel exists in the "
                             "current image.")

        if bounding_border:
            self.image = self.image.crop(bounding_border)


class WandImage(ImageEngine, SequenceEngine):
    """
    Class that standardized methods of Wand library.
    This class depends on Wand being installed in the system.
    """

    class_image = WandImageClass
    """
    Attribute used to store the class reference responsible to create an image.
    """

    def append_to_sequence(self, image):
        """
        Method to append an image to the sequence of images in the current image.
        """
        if self.sequence_image is None:
            self.prepare_sequence_image()

        # Append the internal image inside the current WandImage object.
        self.sequence_image.append(image.image)

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

    @classmethod
    def create_sequence_image(cls, images):
        """
        Method to create a new image with sequence using a list of images.
        """
        image_object = cls.class_image()

        for image in images:
            image_object.sequence.append(image.image)

        # Create delay for each image.
        for index, image in image_object.sequence:

        return cls.create_from_image(image=image_object)

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

    def get_frame(self, index):
        """
        Method to obtain an engine from a specified index frame of current image object.
        This method should return None if no frame exists with given index.
        """
        if self.sequence_image is None:
            self.prepare_sequence_image()

        try:
            # Convert wand.SingleImage to wand.Image to allow IO manipulation of the image.
            return self.create_from_image(image=self.class_image(self.sequence_image[index]))

        except (StopIteration, IndexError):
            return None

    def get_size(self):
        """
        Method to obtain the size of current image.
        """
        return self.image.size[0], self.image.size[1]

    def get_total_frames(self):
        """
        Method to obtain the total amount of frames in image.
        This method should return 1 if the current image is not iterable.
        """
        if self.sequence_image is None:
            self.prepare_sequence_image()

        return len(self.sequence_image)

    def has_transparency(self):
        """
        Method to verify if image has a channel for transparency.
        """
        return self.image.alpha_channel

    def prepare_image(self):
        """
        Method to prepare the image using the stored buffer as the source.
        """
        self.image = self.class_image(file=self.source_buffer)

    def prepare_sequence_image(self):
        """
        Method to prepare the sequence object from image.
        """
        self.sequence_image = self.image.sequence

    def scale(self, width, height):
        """
        Method to scale the current image object without implementing additional logic.
        """
        self.image.resize(width, height, filter="lanczos2sharp")

    def show(self):
        """
        Method to display the image for debugging purposes.
        """
        wand_display(self.image)

    def trim(self, color=None):
        """
        Method to trim the current image object.
        The parameter color is used to indicate the color to trim else it will use transparency.
        """
        if color:
            color = Color(f"rgb({color[0]}, {color[1]}, {color[2]})")

        elif self.has_transparency():
            # Trim transparency
            color = Color('rgba(0,0,0,0)')

        else:
            raise ValueError("Cannot trim image because no color was informed and no alpha channel exists in the "
                             "current image.")

        self.image.trim(background_color=color, reset_coords=True)
