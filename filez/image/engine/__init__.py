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
`filez <at> gabrielfontenelle.com` can be used.
"""
from __future__ import annotations

import base64
import warnings
from io import BytesIO, StringIO
from typing import Any, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from ...pipelines.extractor.package import PackageExtractor

__all__ = [
    "ImageEngine",
]


class ImageEngine:
    """
    Class that standardized methods of different image manipulators.
    """
    image: Any
    image = None
    """
    Attribute where the current image converted from buffer is stored.
    """
    class_image: Type[Any] | None = None
    """
    Attribute used to store the class reference responsible to create an image.
    This attribute should be override by child class.
    """
    metadata: dict[str, Any]
    metadata = None
    """
    Attribute used to store image metadata if available.
    """

    def __init__(self, buffer: StringIO | BytesIO | PackageExtractor.ContentBuffer | None) -> None:
        """
        Method to instantiate the current class using a buffer for the image content as a source
        for manipulation by the class to be used.
        """
        if buffer is not None:
            self.source_buffer = buffer

            self.prepare_image()

    def append_to_sequence(self, images: list[Any], **kwargs: Any) -> None:
        """
        Method to append a list of images to the current image, if the current image is not a sequence
        this method should convert it to a sequence.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method append_to_sequence should be override in child class.")

    def change_color(self, colorspace: str = "gray", **kwargs: Any) -> None:
        """
        Method to change the color space of the current image.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method change_color should be override in child class.")

    def clone(self) -> Any:
        """
        Method to copy the current image object and return it.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method clone should be override in child class.")

    @classmethod
    def create_empty_image(cls) -> ImageEngine:
        """
        Method to instantiate the current class with an empty image.
        """
        if not hasattr(cls, 'class_image'):
            raise NotImplementedError(f"The current class {cls.__name__} don`t implement the attribute `class_image`.")

        if cls.class_image is None:
            raise NotImplementedError("The attribute `class_image` should be override in child class.")

        return cls.create_from_image(image=cls.class_image())

    @classmethod
    def create_from_image(cls, image: Any) -> ImageEngine:
        """
        Method to instantiate the current class using a preprocessed image of the same class.
        """
        self = cls(buffer=None)
        self.image = image

        return self
    
    def crop(self, width: int, height: int, **kwargs: Any) -> None:
        """
        Method to crop the current image object.
        This method must affect the current image object.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method crop should be override in child class.")

    @staticmethod
    def get_aspect_ratio(width: int, height: int) -> tuple[float, float]:
        """
        Method to obtain the width and height proportion (aspect ratio) to use in transformations.
        """
        ratio_width = width / height
        ratio_height = height / width

        return ratio_width, ratio_height

    def get_base64(self, encode_format: str = "jpeg") -> str:
        """
        Method to obtain the base64 representation for the content of the current image object.
        """
        content = self.get_bytes(encode_format)

        # Convert buffer to base64 string representation in ASCII
        return base64.b64encode(content).decode('ascii')

    def get_buffer(self, encode_format: str = "jpeg") -> BytesIO:
        """
        Method to get a buffer IO from the current image.
        """
        return BytesIO(self.get_bytes(encode_format=encode_format))

    def get_bytes(self, encode_format: str = "jpeg") -> bytes:
        """
        Method to obtain the bytes' representation for the content of the current image object.
        This method must return bytes already compressed by format.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method get_bytes_from_image should be override in child class.")

    def get_relative_size(
        self,
        width: int,
        height: int,
        new_width: int,
        new_height: int,
        constraint: bool = True
    ) -> tuple[int, int]:
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

    def get_size(self) -> tuple[int, int]:
        """
        Method to obtain the size of current image.
        This method should return a tuple with width and height.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method get_size should be override in child class.")

    def has_sequence(self) -> bool:
        """
        Method to verify if image has multiple frames, e.g `.gif`, or distinct sizes, e.g `.ico`.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method has_sequence should be override in child class.")

    def has_transparency(self) -> bool:
        """
        Method to verify if image has a channel for transparency.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method has_transparency should be override in child class.")

    def prepare_image(self) -> None:
        """
        Method to prepare the image using the stored buffer as the source.
        This method should use `self.source_buffer` and `self.image` to set the current image object.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method prepare_image should be override in child class.")

    def resample(self, percentual: int = 10, encode_format: str = "webp") -> None:
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

    def rotate(self, angle: int, background_color: tuple[int, int, int] | None = None):
        """
        Method to rotate the current image object given an angle. If `background_color` is set the extra space generated
         by the transformation will be filled with it.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method rotate should be override in child class.")

    def scale(self, width: int, height: int, **kwargs: Any) -> None:
        """
        Method to scale the current image object without implementing additional logic.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method scale should be override in child class.")

    def show(self) -> None:
        """
        Method to display the image for debugging purposes.
        This method should be overwritten in child class with the appropriate mode of displaying the image.
        """
        raise NotImplementedError("The method show should be override in child class.")

    def trim(self, color: tuple[int, int, int] | None = None) -> None:
        """
        Method to trim the current image object.
        This method must affect the current image object.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method trim should be override in child class.")
