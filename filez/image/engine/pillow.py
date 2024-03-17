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

from io import BytesIO
from typing import Any, Type, Iterator, TYPE_CHECKING

from . import ImageEngine
from ...utils import LazyImportClass

if TYPE_CHECKING:
    from PIL import Image as PillowImageClass


__all__ = [
    "PillowImage",
]


PillowSequence = LazyImportClass('ImageSequence', from_module='PIL')
"""Lazy import of ImageSequence class as alias"""


class PillowImage(ImageEngine):
    """
    Class that standardized methods of Pillow library.
    """

    class_image: Type[PillowImageClass] = LazyImportClass('Image', from_module='PIL')
    """
    Attribute used to store the class reference responsible to create an image.
    """

    def _set_image_sequence(self, images: list[Any], encode_format: str) -> None:
        """
        Method to convert a list of images into a single one.
        """
        output: BytesIO = BytesIO()

        images[0].save(
            output,
            format=encode_format,
            save_all=True,
            append_images=images[1:],
            optimize=False,
        )

        self.image = self.class_image.open(fp=output)

    def append_to_sequence(self, images: list[Any], **kwargs: Any) -> None:
        """
        Method to append a list of images to the current image, if the current image is not a sequence
        this method should convert it to a sequence.
        """
        encode_format: str = kwargs.pop("encode_format", "webp")

        self._set_image_sequence(images, encode_format=encode_format)

    def change_color(self, colorspace: str = "gray", **kwargs: Any) -> None:
        """
        Method to change the color space of the current image.
        """
        encode_format: str = kwargs.pop("encode_format", "webp")

        # Convert to grey scale
        colorscheme: dict[str, str] = {
            "gray": "L",
            "Lab": "",
            "YCrCb": "",
            "HSV": ""
        }
        if self.has_sequence():
            def change_color_frame(image):

                return image.convert(colorscheme[colorspace])

            images = PillowSequence.all_frames(self.image, change_color_frame)
            self._set_image_sequence(images, encode_format)

        else:
            self.image = self.image.convert(colorscheme[colorspace])

    def clone(self) -> Any:
        """
        Method to copy the current image object and return it.
        """
        return self.image.copy()

    def crop(self, width: int, height: int, **kwargs: Any) -> None:
        """
        Method to crop the current image object.
        """
        current_width, current_height = self.get_size()
        encode_format: str = kwargs.pop("encode_format", "webp")

        # Set `top` based on center gravity
        top: int = current_height // 2 - height // 2

        # Set `left` based on center gravity
        left: int = current_width // 2 - width // 2

        if self.has_sequence():
            def crop_frame(image):
                return image.crop((top, left, width, height))

            images = PillowSequence.all_frames(self.image, crop_frame)
            self._set_image_sequence(images, encode_format)

        else:
            self.image = self.image.crop((top, left, width, height))

    def get_buffer(self, encode_format="jpeg"):
        """
        Method to get a buffer IO from the current image.
        For optimization this function performance the same as get_bytes_from_image except by the return of
        BytesIO without reading bytes content.
        """
        output = BytesIO()
        self.image.save(output, save_all=True, format=encode_format)
        return output

    def get_bytes(self, encode_format: str = "jpeg") -> bytes:
        """
        Method to obtain the bytes' representation for the content of the current image object.
        """
        output = BytesIO()
        self.image.save(output, format=encode_format)
        return output.read()

    def get_size(self) -> tuple[int, int]:
        """
        Method to obtain the size of current image.
        This method should return a tuple with width and height.
        """
        return self.image.size[0], self.image.size[1]

    def has_sequence(self) -> bool:
        """
        Method to verify if image has multiple frames, e.g `.gif`, or distinct sizes, e.g `.ico`.
        """
        return hasattr(self.image, 'n_frames') and self.image.n_frames > 1

    def has_transparency(self) -> bool:
        """
        Method to verify if image has a channel for transparency.
        """
        return self.image.info.get("transparency") is not None

    def prepare_image(self) -> None:
        """
        Method to prepare the image using the stored buffer as the source.
        """
        self.image = self.class_image.open(fp=self.source_buffer)

    def resample(self, percentual: int = 10, encode_format: str = "webp") -> None:
        """
        Method to re sample the image sequence with only the percentual amount of items distributed through the image
        sequences.
        """

        total_frames: int = self.image.n_frames

        if total_frames <= 1:
            return

        steps: int = total_frames // (total_frames * percentual // 100)

        duration: int | None
        try:
            # There is duration information for Gif, but not for WebP.
            duration = int(self.image.info["duration"] * percentual / 100)
        except KeyError:
            duration = None

        images: list = []

        sequence: Iterator = PillowSequence.Iterator(self.image)

        for index in set(range(0, total_frames, steps)):
            # Convert to SingleImage
            frame = sequence[index].copy()
            # Fix duration
            if duration:
                frame.info["duration"] = duration
            images.append(frame)

        self._set_image_sequence(images, encode_format)

    def scale(self, width: int, height: int, **kwargs: Any) -> None:
        """
        Method to scale the current image object without implementing additional logic.
        """
        encode_format: str = kwargs.get("encode_format", "webp")

        if self.has_sequence():
            def resize_frame(image):
                return image.resize((width, height), resample=self.class_image.Resampling.LANCZOS)

            images: list = PillowSequence.all_frames(self.image, resize_frame)

            self._set_image_sequence(images, encode_format)
        else:
            self.image = self.image.resize((width, height), resample=self.class_image.Resampling.LANCZOS)

    def show(self) -> None:
        """
        Method to display the image for debugging purposes.
        """
        if self.has_sequence():
            for image in PillowSequence.Iterator(self.image):
                image.show()
        else:
            self.image.show()

    def trim(self, color: tuple[int, int, int] | None = None) -> None:
        """
        Method to trim the current image object.
        The parameter color is used to indicate the color to trim else it will use transparency.
        This method will trim the whole image based on first frame/size if image has sequence.
        """
        if color:
            from PIL import ImageChops

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
