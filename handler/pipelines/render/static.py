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
from io import BytesIO

from psd_tools import PSDImage
from .. import ValidationError, Pipeline

__all__ = [
    "StaticRender",
    "ImageRender",
    "PSDRender",
]


class StaticRender:
    """
    Render class with focus to processing information from file's content to create a static representation of it.
    """

    extensions = None
    """
    Attribute to store allowed extensions for use in `validator`.
    This attribute should be override in children classes.
    """

    stopper = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """

    @classmethod
    def create_static_file(cls, object_to_process, content):
        """
        Method to create a file structured for the static image on same class as object_to_process.
        """
        defaults = object_to_process._thumbnail.defaults

        # Create file object for image, change filename from parent to use
        # the new format as base for extension.
        static_file = object_to_process.__class__(
            path=f"{object_to_process.sanitize_path}.{defaults.format_extension}",
            extract_data_pipeline=Pipeline(
                'handler.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
                'handler.pipelines.extractor.MimeTypeFromFilenameExtractor',
            ),
            file_system_handler=object_to_process.storage
        )

        # Set content from buffer.
        static_file.content = content

        # Set metadata for file object of thumbnail.
        static_file.meta.thumbnail = True

        return static_file

    @classmethod
    def process(cls, **kwargs):
        """
        Method used to run this class on Processor`s Pipeline for Rendering images from Data.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        """
        object_to_process = kwargs.pop('object_to_process', None)
        try:
            # Validate whether the extension for the current class is compatible with the render.
            cls.validate(file_object=object_to_process)

            # Render the static image for the FileThumbnail.
            cls.render(file_object=object_to_process, **kwargs)

        except (ValueError, IOError) as e:
            if not hasattr(cls, 'errors'):
                setattr(cls, 'errors', [e])
            elif isinstance(cls.errors, list):
                cls.errors.append(e)

            return False

        except ValidationError:
            # Don't register validation error because it is a expected error case the extension is
            # not compatible with the method.
            return False

        return True

    @classmethod
    def render(cls, file_object, **kwargs: dict):
        """
        Method to render the image representation of the file_object.
        This method must be override in child class.
        """
        raise NotImplementedError("Method render must be overwritten on child class.")

    @classmethod
    def validate(cls, file_object):
        """
        Method to validate if content can be rendered to given extension.
        """
        if cls.extensions is None:
            raise NotImplementedError(f"The attribute extensions is not overwritten in child class {cls.__name__}")

        # The ValidationError should be captured in children classes else it will not register as an error and
        # the pipeline will break.
        if file_object.extension not in cls.extensions:
            raise ValidationError(f"Extension {file_object.extension} not allowed in validate for class {cls.__name__}")


class ImageRender(StaticRender):

    extensions = ["jpeg", "jpg", "png", "gif"]
    """
    Attribute to store allowed extensions for use in `validator`.
    """

    @classmethod
    def render(cls, file_object, **kwargs: dict):
        """
        Method to render the image representation of the file_object.
        """
        image_engine = kwargs.pop('engine')

        defaults = file_object._thumbnail.defaults

        # Resize image using the image_engine and default values.
        image = image_engine(buffer=file_object.buffer)

        image.resize(defaults.width, defaults.height, keep_ratio=defaults.keep_ratio)

        # Set static file for current file_object.
        file_object._thumbnail._static_file = cls.create_static_file(
            file_object,
            content=image.get_buffer(encode_format=defaults.format)
        )


class PDFRender(StaticRender):
    pass


class PSDRender(StaticRender):

    extensions = ["psd", "psb"]
    """
    Attribute to store allowed extensions for use in `validator`.
    """

    @classmethod
    def render(cls, file_object, **kwargs: dict):
        """
        Method to render the image representation of the file_object.
        """
        image_engine = kwargs.pop('engine')

        defaults = file_object._thumbnail.defaults

        # Load PSD from buffer
        psd = PSDImage.open(fp=file_object.buffer)

        # Compose image from PSD visible layers and
        # convert it to RGB to remove alpha channel before saving it to buffer.
        buffer = BytesIO()
        psd.composite().convert(mode="RGB").save(fp=buffer, format=defaults.format)

        # Reset buffer to beginning before being loaded in image_engine.
        buffer.seek(0)

        image = image_engine(buffer=buffer)

        image.resize(defaults.width, defaults.height, keep_ratio=defaults.keep_ratio)

        # Set static file for current file_object.
        file_object._thumbnail._static_file = cls.create_static_file(
            file_object,
            content=image.get_buffer(encode_format=defaults.format)
        )


class VideoRender(StaticRender):

    extensions = ["avi", "mkv", "mpg", "mpeg", "flv"]
    """
    Attribute to store allowed extensions for use in `validator`.
    """


class DocumentRender(StaticRender):
    pass
