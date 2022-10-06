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


class VideoEngine:
    """
    Class that standardized methods of different video manipulators.
    """
    video = None
    """
    Attribute where the current video converted from buffer is stored.
    """

    def __init__(self, buffer):
        """
        Method to instantiate the current class using a buffer for the image content as a source
        for manipulation by the class to be used.
        """
        self.source_buffer = buffer

        self.prepare_video()

    def prepare_video(self):
        """
        Method to prepare the video using the stored buffer as the source.
        This method should use `self.source_buffer` and `self.video` to set the current video object.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method prepare_video should be override in child class.")

