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

import imageio as iio
from moviepy.editor import VideoClip
import cv2

__all__ = [
    "VideoEngine",
    "MoviePyVideo",
]


class VideoEngine:
    """
    Class that standardized methods of different video manipulators.
    """

    video = None
    """
    Attribute where the current video converted from buffer is stored.
    """
    metadata = None
    """
    Attribute where the current video metadata is stored.
    """

    def __init__(self, buffer):
        """
        Method to instantiate the current class using a buffer for the image content as a source
        for manipulation by the class to be used.
        """
        self.source_buffer = buffer

        self.prepare_video()

    def get_duration(self):
        """
        Method to return the duration in seconds of the video.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method get_duration should be override in child class.")

    def get_frame_rate(self):
        """
        Method to return the framerate of the video.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method get_frame_rate should be override in child class.")

    def get_frame_amount(self):
        """
        Method to return the total amount of frame available in the video.
        """
        return int(self.get_duration() * self.get_frame_rate())

    def get_frame_as_bytes(self, index, encode_format="jpeg"):
        """
        Method to return content of the frame at index as bytes.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method get_frame_as_bytes should be override in child class.")

    def get_frame_image(self, index):
        """
        Method to return the array representing the frame at index.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method get_frame_image should be override in child class.")

    def get_size(self):
        """
        Method to return the width and height of the video.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method get_size should be override in child class.")

    def prepare_video(self):
        """
        Method to prepare the video using the stored buffer as the source.
        This method should use `self.source_buffer` and `self.video` to set the current video object.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method prepare_video should be override in child class.")

    def show(self):
        """
        Method to display the video for debugging purposes.
        This method should be overwritten in child class.
        """
        raise NotImplementedError("The method show should be override in child class.")


class MoviePyVideo(VideoEngine):
    """
    Class that standardized methods of MoviePy library.
    This class depends on MoviePy, OpenCV and FFMPG installed in the system.
    """

    def get_duration(self):
        """
        Method to return the duration in seconds of the video.
        """
        return self.video.duration

    def get_frame_rate(self):
        """
        Method to return the framerate of the video.
        """
        return self.video.fps

    def get_frame_as_bytes(self, index, encode_format="jpeg"):
        """
        Method to return content of the frame at index as bytes.
        """
        formats = {
            "jpeg": ".jpg"
        }
        success, buffer = cv2.imencode(formats[encode_format], self.video.get_frame(index))

        if not success:
            raise ValueError(f"Could not convert image to format {encode_format} in MoviePyVideo.get_frame_as_bytes.")

        return buffer

    def get_frame_image(self, index):
        """
        Method to return the array representing the frame at index.
        """
        return self.video.get_frame(index)

    def get_size(self):
        """
        Method to return the width and height of the video.
        """
        return self.video.size

    def prepare_video(self):
        """
        Method to prepare the video using the stored buffer as the source.
        """
        video_array = iio.imopen(self.source_buffer, io_mode="r")
        self.metadata = video_array.metadata()

        def make_frame(t):
            """
            Internal function to create the frame from video_array.
            This function allow for consuming of video with lazy operation.
            """
            return video_array.read(index=t)

        self.video = VideoClip(make_frame, duration=self.metadata['duration'])
        self.video.fps = self.metadata['fps']

    def show(self):
        """
        Method to display the video for debugging purposes.
        """
        total_frames = self.get_frame_amount()

        frame = 0

        while frame < total_frames:
            cv2.imshow("Video", self.get_frame_image(frame))
            frame += 1

            if cv2.waitKey(25) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()
