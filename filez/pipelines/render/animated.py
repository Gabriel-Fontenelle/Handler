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
from typing import Any, TYPE_CHECKING, Type

from .static import StaticRender
from .. import Pipeline
from ...exception import RenderError

if TYPE_CHECKING:
    from io import StringIO
    from ...file import BaseFile
    from ...file.thumbnail import PreviewDefaults
    from ...image.engine import ImageEngine
    from ...video.engine import VideoEngine

__all__ = [
    'AnimatedRender',
    'DocumentAnimatedRender',
    'ImageAnimatedRender',
    'PSDAnimatedRender',
    'StaticAnimatedRender',
    'VideoAnimatedRender',
]


class AnimatedRender(StaticRender):
    """
    Render class with focus to processing information from file's content to create an animated representation of it.
    """

    @classmethod
    def create_file(cls, object_to_process: BaseFile, content: str | bytes | BytesIO | StringIO) -> BaseFile:
        """
        Method to create a file structured for the animated image on same class as object_to_process.
        """
        defaults: Type[PreviewDefaults] = object_to_process._thumbnail.animated_defaults

        # Create file object for image, change filename from parent to use
        # the new format as base for extension.
        animated_file: BaseFile = object_to_process.__class__(
            path=f"{object_to_process.sanitize_path}.{defaults.format_extension}",
            extract_data_pipeline=Pipeline(
                'filez.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
                'filez.pipelines.extractor.MimeTypeFromFilenameExtractor',
            ),
            file_system_handler=object_to_process.storage
        )

        # Set content from buffer.
        if isinstance(content, (BytesIO, StringIO)):
            animated_file.content_as_buffer = content
        else:
            animated_file.content = content

        # Set metadata for file object of preview.
        animated_file.meta.preview = True

        return animated_file


class StaticAnimatedRender(AnimatedRender):
    """
    Render class for processing information from file's content focusing in rendering the whole image.
    This class not make use of sequences.
    """

    extensions: set[str] = {"jpeg", "jpg", "bmp", "tiff", "tif"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """

    @classmethod
    def render(cls, file_object: BaseFile, **kwargs: Any) -> None:
        """
        Method to render the animated representation of the file_object.
        But because those extensions don`t need to be animated to represent the whole image,
        there is no need to animate it.
        """
        image_engine: Type[ImageEngine] = kwargs.pop('image_engine')

        defaults: Type[PreviewDefaults] = file_object._thumbnail.animated_defaults

        # Resize image using the image_engine and default values.
        buffer = file_object.content_as_buffer

        if not buffer:
            raise RenderError("There is no content in buffer format available to render.")

        image: ImageEngine = image_engine(buffer=buffer)

        image.resize(defaults.width, defaults.height, keep_ratio=defaults.keep_ratio)

        # Set static file for current file_object.
        file_object._thumbnail._animated_file = cls.create_file(
            file_object,
            content=image.get_buffer(encode_format=defaults.format)
        )


class ImageAnimatedRender(AnimatedRender):
    """
    Render class for processing information from file's content focusing in rendering a sample of the whole animated
    image.
    This class make use of sequences.
    """

    extensions: set[str] = {"gif", "png", "apng", "webp"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """

    @classmethod
    def render(cls, file_object: BaseFile, **kwargs: Any) -> None:
        """
        Method to render the animated representation of the file_object that has animation.
        """
        image_engine: Type[ImageEngine] = kwargs.pop('image_engine')

        defaults: Type[PreviewDefaults] = file_object._thumbnail.animated_defaults

        buffer = file_object.content_as_buffer

        if not buffer:
            raise RenderError("There is no content in buffer format available to render.")

        # Resize image using the image_engine and default values.
        image: ImageEngine = image_engine(buffer=buffer)

        image.resample(percentual=defaults.duration, encode_format=defaults.format)

        image.resize(defaults.width, defaults.height, keep_ratio=defaults.keep_ratio)

        # Set animated file for current file_object.
        file_object._thumbnail._animated_file = cls.create_file(
            file_object,
            content=image.get_buffer(encode_format=defaults.format)
        )


class DocumentAnimatedRender(AnimatedRender):
    """
    Render class for processing information from file's content focusing in rendering a sample of the document's pages.
    This class make use of sequences.
    """

    extensions: set[str] = {"pdf", "epub", "fb2", "xps", "oxps"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """

    @classmethod
    def render(cls, file_object: BaseFile, **kwargs: Any) -> None:
        """
        Method to render the animated representation of the file_object that has pages.
        """
        image_engine: Type[ImageEngine] = kwargs.pop('image_engine')

        defaults: Type[PreviewDefaults] = file_object._thumbnail.animated_defaults

        buffer = file_object.content_as_buffer

        if not buffer:
            raise RenderError("There is no content in buffer format available to render.")

        # Local import to avoid longer time to load FileZ library.
        import fitz

        # Use fitz from PyMuPDF to open the document.
        # Because BufferedReader (default return for file_system.open) is not accept
        # we need to consume to get its bytes as bytes are accepted as stream.
        doc = fitz.open(
            stream=buffer.read(),
            filetype=file_object.extension,
            # width and height are only used for content that requires rendering of vectors as `epub`.
            width=defaults.width * 5,
            height=defaults.height * 5
        )

        images: list[ImageEngine] = []

        total_frames: int = doc.page_count
        steps: int = total_frames // (total_frames * defaults.duration // 100)

        for page in doc.pages(0, total_frames, steps):
            bitmap = page.get_pixmap(dpi=defaults.format_dpi)

            # Save the image in buffer with Pillow.
            buffer = BytesIO()
            bitmap.pil_save(fp=buffer, format=defaults.format)
            buffer.seek(0)

            image: ImageEngine = image_engine(buffer=buffer)

            # Trim white space originated from epub.
            image.trim(color=defaults.color_to_trim)

            # Resize image using the image_engine and default values.
            image.resize(defaults.width, defaults.height, keep_ratio=defaults.keep_ratio)

            # Append buffers
            images.append(image)

        # Create sequence image.
        image = images[0].clone()
        image.append_to_sequence(images=[image.image for image in images[1:]], encode_format=defaults.format)

        # Set static file for current file_object.
        file_object._thumbnail._animated_file = cls.create_file(
            file_object,
            content=image.get_buffer(encode_format=defaults.format)
        )


class PSDAnimatedRender(AnimatedRender):
    """
    Render class for processing information from file's content focusing in rendering a sample of the PSD layers.
    This class make use of sequences.
    """

    extensions: set[str] = {"psd", "psb"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """

    @classmethod
    def render(cls, file_object: BaseFile, **kwargs: Any) -> None:
        """
        Method to render the animated representation of the file_object that has layers.
        """
        image_engine: Type[ImageEngine] = kwargs.pop('image_engine')

        defaults: Type[PreviewDefaults] = file_object._thumbnail.animated_defaults

        buffer = file_object.content_as_buffer

        if not buffer:
            raise RenderError("There is no content in buffer format available to render.")

        # Local import to avoid longer time to load FileZ library.
        from psd_tools import PSDImage

        # Load PSD from buffer
        psd: PSDImage = PSDImage.open(fp=buffer)

        images: list[ImageEngine] = []

        total_frames: int = len(psd.layers)
        steps: int = total_frames // (total_frames * defaults.duration // 100)

        # Compose image from PSD visible layers and
        # convert it to RGB to remove alpha channel before saving it to buffer.
        for index in set(range(0, total_frames, steps)):
            buffer = BytesIO()
            psd.layers[index].composite().convert(mode="RGB").save(fp=buffer, format=defaults.format)

            # Reset buffer to beginning before being loaded in image_engine.
            buffer.seek(0)

            image: ImageEngine = image_engine(buffer=buffer)

            image.resize(defaults.width, defaults.height, keep_ratio=defaults.keep_ratio)

            # Append buffers
            images.append(image)

        # Create sequence image.
        image = images[0].clone()
        image.append_to_sequence(images=[image.image for image in images[1:]], encode_format=defaults.format)

        # Set static file for current file_object.
        file_object._thumbnail._animated_file = cls.create_file(
            file_object,
            content=image.get_buffer(encode_format=defaults.format)
        )


class VideoAnimatedRender(AnimatedRender):
    """
    Render class for processing information from file's content focusing in rendering a sample of the video frames.
    This class make use of sequences.
    """

    extensions: set[str] = {"avi", "mkv", "mpg", "mpeg", "mp4", "flv"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """

    @classmethod
    def render(cls, file_object: BaseFile, **kwargs: Any) -> None:
        """
        Method to render the animated representation of the file_object that has frames.
        """
        image_engine: Type[ImageEngine] = kwargs.pop('image_engine')
        video_engine: Type[VideoEngine] = kwargs.pop('video_engine')

        defaults: Type[PreviewDefaults] = file_object._thumbnail.animated_defaults

        buffer = file_object.content_as_buffer

        if not buffer:
            raise RenderError("There is no content in buffer format available to render.")

        video: VideoEngine = video_engine(buffer=buffer)

        total_frames: int = video.get_frame_amount()
        steps: int = total_frames // (total_frames * defaults.duration // 100)

        images: list[ImageEngine] = []

        for index in set(range(0, total_frames, steps)):
            image: ImageEngine = image_engine(
                buffer=BytesIO(video.get_frame_as_bytes(index=index, encode_format=defaults.format))
            )

            image.resize(defaults.width, defaults.height, keep_ratio=defaults.keep_ratio)

            # Append buffers
            images.append(image)

        # Create sequence image.
        image = images[0].clone()
        image.append_to_sequence(images=[image.image for image in images[1:]], encode_format=defaults.format)

        # Set static file for current file_object.
        file_object._thumbnail._animated_file = cls.create_file(
            file_object,
            content=image.get_buffer(encode_format=defaults.format)
        )
