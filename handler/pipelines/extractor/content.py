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
from datetime import datetime
from zipfile import BadZipFile, ZipFile

from ..hasher import CRC32Hasher
from tinytag import TinyTag

from py7zr import SevenZipFile
from py7zr.exceptions import Bad7zFile
from rarfile import BadRarFile, RarFile, NotRarFile

from .extractor import Extractor
from .. import Pipeline

from ...exception import ValidationError

__all__ = [
    'AudioMetadataFromContentExtractor',
    'ContentExtractor',
    'MimeTypeFromContentExtractor',
    'SevenZipCompressedFilesFromContentExtractor',
    'RarCompressedFilesFromContentExtractor',
    'ZipCompressedFilesFromContentExtractor',
]


class ContentExtractor(Extractor):
    """
    Extractor class with focus to processing information from file's content.
    This class was created to allow parsing and extraction of data designated to
    internal files.
    """

    extensions = None
    """
    Attribute to store allowed extensions for use in `validator`.
    This attribute should be override in children classes.
    """
    compressor_class = None
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    This attribute should be override in children classes.
    """
    stopper = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """

    class ContentBuffer(IOBase):
        """
        Class to allow consumption of buffer in a lazy way.
        This class should be override in children of ContentExtractor to
        implementation of method read().
        """

        source_file_object = None
        """
        Attribute to store the related file object that has the buffer for the compressed content.
        """
        compressor = None
        """
        Attribute to store the class of the compressor able to uncompress the content.  
        """
        filename = None
        """
        Attribute to store the name of file that should be extract for this content.
        """

        def __init__(self, source_file_object, compressor_class, internal_file_filename):
            """
            Method to initiate the object saving the data required to allow decompressing and reading content
            for specific file.
            """
            self.source_file_object = source_file_object
            self.compressor = compressor_class
            self.filename = internal_file_filename

        def read(self, *args, **kwargs) -> str:
            """
            Method to read the content of the object initiating the buffer if not exists.
            This method should be overwritten in child class.
            """
            raise NotImplementedError(f"Method read of ContentBuffer should be override in child class "
                                      f"{self.__class__.__name__}.")

        def seek(self, *args, **kwargs):
            """
            Method to seek the content in the buffer.
            Buffer must exist for this method to work, else no action will be taken.
            """
            if not hasattr(self, "buffer"):
                return

            return self.buffer.seek(*args, **kwargs)

        def seekable(self):
            """
            Method to verify if buffer is seekable.
            Buffer must exist for this method to work, else no action will be taken.
            """

            if not hasattr(self, "buffer"):
                return False

            return self.buffer.seekable()

        def close(self):
            """
            Method to close the buffer.
            Buffer must exist for this method to work, else no action will be taken.
            """
            if not hasattr(self, "buffer"):
                return

            self.buffer.close()
            delattr(self, "buffer")

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

    @classmethod
    def decompress(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to uncompress the content from a file_object.
        This method must be override in child class.
        """
        raise NotImplementedError("Method extract_content must be overwritten on child class.")

    @classmethod
    def content_buffer(cls, file_object, internal_file_name):
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        This method must be override in child class.
        """
        raise NotImplementedError("Method content_buffer must be overwritten on child class.")


class MastrokaFilesFromContentExtractor(ContentExtractor):
    """
    Class to extract internal files from mka, mkv files.
    """


class PSDLayersFromContentExtractor(ContentExtractor):
    """
    Class to extract internal files from PSD files.
    """


class ZipCompressedFilesFromContentExtractor(ContentExtractor):
    """
    Class to extract internal files from rar files.
    """

    extensions = ['zip']
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor = ZipFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        try:
            cls.validate(file_object)

            file_system = file_object.storage
            file_class = file_object.__class__

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor(file=file_object.buffer) as compressed_object:

                for internal_file in compressed_object.infolist():
                    # Skip directories and symbolic link
                    if internal_file.is_dir():
                        continue

                    # Skip duplicate only if not choosing to override.
                    if internal_file.filename in file_object._content_files and not overrider:
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

                    # Update creation and modified date. Zip don't store the created date, only the modified one.
                    # To avoid problem the created date will be consider the same as modified.
                    internal_file_object.create_date = datetime(*internal_file.date_time)
                    internal_file_object.update_date = internal_file_object.create_date

                    # Update size of file
                    internal_file_object.size = internal_file.file_size

                    # Update hash generating the hash file and adding its content
                    hash_file = CRC32Hasher.create_hash_file(
                        object_to_process=file_object,
                        digested_hex_value=internal_file.CRC
                    )
                    internal_file_object.hashes['crc32'] = internal_file.CRC, hash_file, CRC32Hasher

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content = cls.content_buffer(file_object, internal_file.filename)

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[internal_file.filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

            return True

        except (BadZipFile, ValidationError):
            return False


class RarCompressedFilesFromContentExtractor(ContentExtractor):
    """
    Class to extract internal files from rar files.
    """

    extensions = ['rar']
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor = RarFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        try:
            cls.validate(file_object)

            file_system = file_object.storage
            file_class = file_object.__class__

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor(file=file_object.buffer) as compressed_object:

                for internal_file in compressed_object.infolist():
                    # Skip directories and symbolic link
                    if internal_file.is_dir() or internal_file.is_symlink():
                        continue

                    # Skip duplicate only if not choosing to override.
                    if internal_file.filename in file_object._content_files and not overrider:
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
                    internal_file_object.create_date = internal_file.ctime
                    internal_file_object.update_date = internal_file.mtime

                    # Update size of file
                    internal_file_object.size = internal_file.file_size

                    # Update hash generating the hash file and adding its content
                    if internal_file.CRC:
                        hash_file = CRC32Hasher.create_hash_file(
                            object_to_process=file_object,
                            digested_hex_value=internal_file.CRC
                        )
                        internal_file_object.hashes['crc32'] = internal_file.CRC, hash_file, CRC32Hasher

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content = cls.content_buffer(file_object, internal_file.filename)

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[internal_file.filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

            return True

        except (BadRarFile, NotRarFile, ValidationError):
            return False


class SevenZipCompressedFilesFromContentExtractor(ContentExtractor):
    """
    Class to extract internal files from 7z files.
    """

    extensions = ['7z']
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor = SevenZipFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        try:
            cls.validate(file_object)

            file_system = file_object.storage
            file_class = file_object.__class__

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor(file=file_object.buffer) as compressed_object:

                for internal_file in compressed_object.list():
                    # Skip directories
                    if internal_file.is_directory:
                        continue

                    # Skip duplicate only if not choosing to override.
                    if internal_file.filename in file_object._content_files and not overrider:
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

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content = cls.content_buffer(file_object, internal_file.filename)

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[internal_file.filename] = internal_file_object

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
        if file_object.buffer.seekable():
            file_object.buffer.seek(0)

        tinytag = TinyTag(file_object.buffer, len(file_object))
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
        if file_object.buffer.seekable():
            file_object.buffer.seek(0)


class MimeTypeFromContentExtractor(Extractor):
    pass
