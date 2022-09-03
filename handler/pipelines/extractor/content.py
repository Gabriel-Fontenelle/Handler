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
from ..hasher import CRC32Hasher
from tinytag import TinyTag

from py7zr import SevenZipFile
from py7zr.exceptions import Bad7zFile

from .extractor import Extractor
from .. import Pipeline

from ...exception import ValidationError

__all__ = [
    'AudioMetadataFromContentExtractor',
    'ContentExtractor',
    'SevenZipCompressedFilesFromContentExtractor',
    'RARCompressedFilesFromContentExtractor',
    'MimeTypeFromContentExtractor'
]


class ContentExtractor(Extractor):
    """
    Extractor class with focus to processing information from file's content.
    This class was created to allow parsing and extraction of data designated to
    internal files.
    """

    extensions = None
    """
    Attribute to store allowed extensions to be used in validator.
    This attribute should be override in children classes.
    """
    stopper = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """

    @classmethod
    def validate(cls, file_object):
        """
        Method to validate if content can be extract to given extension.
        """
        if cls.extensions is None:
            raise NotImplementedError(f"The attribute extensions is not overwritten in child class {cls.__name__}")

        # The ValidationError should be captured in children classes else it will not register as an error and
        # the pipeline will break.
        if file_object.extension not in cls.extensions:
            raise ValidationError(f"Extension {file_object.extension} not allowed in validate for class {cls.__name__}")


class MastrokaFilesFromContentExtractor(ContentExtractor):
    """
    Class to extract internal files from mka, mkv files.
    """


class PSDLayersFromContentExtractor(ContentExtractor):
    """
    Class to extract internal files from PSD files.
    """


class RARCompressedFilesFromContentExtractor(ContentExtractor):
    """
    Class to extract internal files from rar files.
    """


class SevenZipCompressedFilesFromContentExtractor(ContentExtractor):
    """
    Class to extract internal files from 7z files.
    """

    extensions = ['7z']
    """
    Attribute to store allowed extensions to be used in validator.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        try:
            cls.validate(file_object)

            # Reset buffer to initial location
            if file_object._content.buffer.seekable():
                file_object._content.buffer.seek(0)

            file_system = file_object.storage
            file_class = file_object.__class__

            file7z = SevenZipFile(file=file_object._content.buffer)

            for internal_file in file7z.list():
                # Skip directories
                if internal_file.is_directory:
                    continue

                # Skip duplicate only if not choosing to override.
                if internal_file.filename in file_object._content and not overrider:
                    continue

                # Create file object for internal file
                internal_file_object = file_class(
                    path=internal_file.filename,
                    extract_data_pipeline=Pipeline(
                        'handler.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
                        'handler.pipelines.extractor.MimeTypeFromFilenameExtractor',
                    ),
                    file_system_handler=file_system
                )

                # Update creation and modified date
                internal_file_object.create_date = internal_file.creationtime
                internal_file_object.update_date = internal_file.creationtime

                # Update size of file
                internal_file_object.size = internal_file.uncompressed

                # Update hash generating the hash file and adding its content
                hash_file = CRC32Hasher.create_hash_file(
                    object_to_process=file_object,
                    digested_hex_value=internal_file.crc32
                )
                internal_file_object.hashes['crc32'] = internal_file.crc32, hash_file, CRC32Hasher

                # Set up action to be extracted instead of to save.
                internal_file_object._actions.to_extract()

                # Add internal file as File object to file.
                file_object._content_files[internal_file.filename] = internal_file_object

            # Reset buffer to initial location
            if file_object._content.buffer.seekable():
                file_object._content.buffer.seek(0)

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

            return True

        except (Bad7zFile, ValidationError):
            return False


class VideoMetadataFromContentExtractor(Extractor):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract additional metadata information from content.
        """


class ImageMetadataFromContentExtractor(Extractor):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract additional metadata information from content.
        """


class AudioMetadataFromContentExtractor(Extractor):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract additional metadata information from content.
        """
        # Use tinytag to get additional metadata.
        if not file_object.content:
            raise ValueError(
                "Attribute `content` must be settled before calling `AudioMetadataFromContentExtractor.extract`!"
            )
        if not len(file_object):
            raise ValueError(
                "Length for file's object must set before calling `AudioMetadataFromContentExtractor.extract`!"
            )

        # Reset buffer to initial location
        if file_object._content.buffer.seekable():
            file_object._content.buffer.seek(0)

        tinytag = TinyTag(file_object._content.buffer, len(file_object))
        tinytag.load(tags=True, duration=True, image=False)
        # Same as code in tinytag, it turn default dict into dict so that it can throw KeyError
        tinytag.extra = dict(tinytag.extra)

        attributes_to_extract = [
            'album',
            'albumartist',
            'artist',
            'audio_offset',
            'bitrate',
            'channels',
            'comment',
            'composer',
            'disc',
            'disc_total',
            'duration',
            'extra',
            'genre',
            'samplerate',
            'title',
            'track',
            'track_total',
            'year'
        ]
        for attribute in attributes_to_extract:
            tinytag_attribute = getattr(tinytag, attribute, None)
            if tinytag_attribute and (not getattr(file_object.meta, attribute, None) or overrider):
                setattr(file_object.meta, attribute, tinytag_attribute)

        # Reset buffer to initial location
        if file_object._content.buffer.seekable():
            file_object._content.buffer.seek(0)
