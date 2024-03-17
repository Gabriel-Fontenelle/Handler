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

from typing import Any, TYPE_CHECKING

from . import ImageEngine
from ...utils import LazyImportClass

if TYPE_CHECKING:
    from numpy import ndarray

__all__ = [
    "OpenCVImage",
]

cv2 = LazyImportClass('cv2')
"""Lazy import of cv2 module"""

np = LazyImportClass('numpy')
"""Lazy import of numpy module as alias np"""


class OpenCVImage(ImageEngine):
    """
    Class that standardized methods of OpenCV library.
    This class depends on OpenCV being installed in the system.
    In OpenCV the image is basically a numpy matrix.
    """

    def append_to_sequence(self, images: list[Any], **kwargs: Any) -> None:
        """
        Method to append a list of images to the current image, if the current image is not a sequence
        this method should convert it to a sequence.
        """
        return

    def change_color(self, colorspace="gray", **kwargs: Any):
        """
        Method to change the color space of the current image.
        """
        # Convert to grey scale
        colorscheme: dict[str, int] = {
            "gray": cv2.COLOR_BGR2GRAY,
            "Lab": cv2.COLOR_BGR2LAB,
            "YCrCb": cv2.COLOR_BGR2YCrCb,
            "HSV": cv2.COLOR_BGR2HSV
        }

        self.image = cv2.cvtColor(self.image, colorscheme[colorspace])

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

        # Set `top` based on center gravity
        top: int = current_height // 2 - height // 2

        # Set `left` based on center gravity
        left: int = current_width // 2 - width // 2

        self.image = self.image[top:top+height, left:left+width]

    def get_bytes(self, encode_format: str = "jpeg") -> bytes | ndarray:
        """
        Method to obtain the bytes' representation for the content of the current image object.
        """
        formats: dict[str, str] = {
            "jpeg": ".jpg"
        }
        success, buffer = cv2.imencode(formats[encode_format], self.image)

        if not success:
            raise ValueError(f"Could not convert image to format {encode_format} in OpenCVImage.get_bytes_from_image.")

        return buffer

    def get_size(self) -> tuple[int, int]:
        """
        Method to obtain the size of current image.
        OpenCV shape attribute is a tuple (height, width, channels).
        """
        return self.image.shape[1], self.image.shape[0]

    def has_sequence(self) -> bool:
        """
        Method to verify if image has multiple frames, e.g `.gif`, or distinct sizes, e.g `.ico`.
        """
        return False

    def has_transparency(self) -> bool:
        """
        Method to verify if image has a channel for transparency.
        """
        return self.image.shape[2] > 3 or self.image.shape[2] == 2

    def prepare_image(self) -> None:
        """
        Method to prepare the image using the stored buffer as the source.
        """
        # convert to numpy array
        array = np.asarray(bytearray(self.source_buffer.read()), dtype="uint8")

        self.image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)

    def resample(self, percentual: int = 10, encode_format: str = "webp") -> None:
        """
        Method to re sample the image sequence with only the percentual amount of items distributed through the image
        sequences.
        As OpenCV don`t support animated images nothing should be done.
        """
        return

    def scale(self, width: int, height: int, **kwargs: Any) -> None:
        """
        Method to scale the current image object without implementing additional logic.
        """
        self.image = cv2.resize(self.image, (width, height), interpolation=cv2.INTER_AREA)

    def show(self) -> None:
        """
        Method to display the image for debugging purposes.
        """
        cv2.imshow("Image", self.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def trim(self, color: tuple[int, int, int] | None = None) -> None:
        """
        Method to trim the current image object.
        The parameter color is used to indicate the color to trim else it will use transparency.
        """
        if color:
            # Create new image with same color
            background: ndarray = np.zeros(self.image.shape, np.uint8)

            if self.has_transparency():
                background[:] = tuple([*color, 255])
            else:
                background[:] = color

            diff = cv2.absdiff(self.image, background)

            # Convert channels to one channel to allow boundingRect to work
            diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

            bounding_border = cv2.boundingRect(diff)

        elif self.has_transparency():
            splitted_channels = cv2.split(self.image)
            bounding_border = cv2.boundingRect(splitted_channels[-1])

        else:
            raise ValueError("Cannot trim image because no color was informed and no alpha channel exists in the "
                             "current image.")

        if bounding_border:
            # bounding_border is equal to `x, y, w, h = bounding_border`
            self.image = self.image[bounding_border[1]:bounding_border[3], bounding_border[0]:bounding_border[2]]
