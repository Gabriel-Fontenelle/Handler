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
from io import IOBase, BytesIO
from sys import getsizeof
from tarfile import TarFile, TarError
from zipfile import BadZipFile, ZipFile

from psd_tools import PSDImage
from py7zr import SevenZipFile
from py7zr.exceptions import Bad7zFile
from rarfile import BadRarFile, RarFile, NotRarFile

from .extractor import Extractor
from .. import Pipeline
from ..hasher import CRC32Hasher
from ...exception import ValidationError

__all__ = [
    'PackageExtractor',
    'PSDLayersFromPackageExtractor',
    'SevenZipCompressedFilesFromPackageExtractor',
    'RarCompressedFilesFromPackageExtractor',
    'TarCompressedFilesFromPackageExtractor',
    'ZipCompressedFilesFromPackageExtractor',
]


class PackageExtractor(Extractor):
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
        This class should be override in children of PackageExtractor to
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
        mode = None
        """
        Attribute to store the mode of read for the uncompressed content. 
        """

        def __init__(self, source_file_object, compressor_class, internal_file_filename, mode):
            """
            Method to initiate the object saving the data required to allow decompressing and reading content
            for specific file.
            """
            self.source_file_object = source_file_object
            self.compressor = compressor_class
            self.filename = internal_file_filename
            self.mode = mode

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
    def content_buffer(cls, file_object, internal_file_name, mode='rb'):
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        This method must be override in child class.
        """
        raise NotImplementedError("Method content_buffer must be overwritten on child class.")

    @classmethod
    def process(cls, **kwargs: dict):
        """
        Method used to run this class on Processor`s Pipeline for Extracting info from Data.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for package extraction override the method `Extractor.process` in order to validate
        the extension before processing the `object_to_process`.
        """
        try:
            object_to_process = kwargs.get('object_to_process', None)
            cls.validate(file_object=object_to_process)
        except (ValidationError, KeyError) as e:
            return False

        return super().process(**kwargs)


class MastrokaFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from mka, mkv files.
    """


class PSDLayersFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from PSD files.
    """

    extensions = ['psd', 'psb']
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor = PSDImage
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(cls, file_object, internal_file_name, mode='rb'):
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """

        class PSDContentBuffer(cls.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def read(self, *args, **kwargs) -> str:
                """
                Method to read the content of the object initiating the buffer if not exists.
                """
                if not hasattr(self, "buffer"):
                    # Instantiate the buffer of inner content
                    compressed = self.compressor.open(fp=self.source_file_object.buffer)

                    self.buffer = BytesIO()

                    # Save PSD content for layer in buffer.
                    compressed[self.filename].save(fp=self.buffer)

                    # Reset buffer to allow read.
                    self.buffer.seek(0)

                return self.buffer.read(*args, **kwargs)

        return PSDContentBuffer(file_object, cls.compressor_class, internal_file_name, mode)

    @classmethod
    def decompress(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to uncompress the content from a file_object.
        """
        try:
            # We need to create the directory because there is no extractor for handling PSD.
            extraction_path = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            compressed_file = cls.compressor.open(fp=file_object.buffer)

            for index, internal_file in compressed_file:
                filename = f"{index}-{internal_file.name or internal_file.layer_id}.psd"

                path = file_object.storage.join(extraction_path, filename)
                if not file_object.storage.exists(
                    path
                ) or overrider:

                    # Create directory if not exists
                    file_object.storage.create_directory(extraction_path)

                    # Save content buffer for file
                    buffer = BytesIO()
                    internal_file.save(fp=buffer)

                    # Reset pointer to initial point.
                    buffer.seek(0)

                    # Save buffer
                    file_object.storage.save_file(path=path, content=buffer, file_mode='w', write_mode='b')

        except (OSError, ValueError):
            return False

        return True

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        try:
            file_system = file_object.storage
            file_class = file_object.__class__

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            compressed_object = PSDImage.open(fp=file_object.buffer)

            for index, internal_file in enumerate(compressed_object):
                filename = f"{index}-{internal_file.name or internal_file.layer_id}.psd"

                # Skip duplicate only if not choosing to override.
                if filename in file_object._content_files and not overrider:
                    continue

                # Create file object for internal file
                internal_file_object = file_class(
                    path=file_system.join(file_object.save_to, file_object.filename, filename),
                    extract_data_pipeline=Pipeline(
                        'handler.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
                        'handler.pipelines.extractor.MimeTypeFromFilenameExtractor',
                    ),
                    file_system_handler=file_system
                )

                # Update size of file
                internal_file_object.size = getsizeof(internal_file.tobytes())

                # Set up action to be extracted instead of to save.
                internal_file_object._actions.to_extract()

                # Set mode
                mode = "rb"

                # Set up content pointer to internal file using content_buffer
                internal_file_object.content = cls.content_buffer(
                    file_object=file_object,
                    internal_file_name=index,
                    mode=mode
                )

                # Set up metadata for internal file
                internal_file_object.meta.hashable = False
                internal_file_object.meta.internal = True

                # Add internal file as File object to file.
                file_object._content_files[filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except OSError:
            return False

        return True


class TarCompressedFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from tar.gz or tar.bz files.
    As gzip and bzip compression don`t provide a manifest, as it is not an archive format just a compression algorithm,
    the tarfile library should be used to try to extract information of files with compression .bz and .gz as its the
    most common usage of tar with those compressors.
    """

    extensions = ['gz', 'tar', 'bz', 'cbt']
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor = TarFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(cls, file_object, internal_file_name, mode='rb'):
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """

        class TarContentBuffer(cls.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def read(self, *args, **kwargs) -> str:
                """
                Method to read the content of the object initiating the buffer if not exists.
                """
                if not hasattr(self, "buffer"):
                    # Instantiate the buffer of inner content
                    compressed = self.compressor(fileobj=self.source_file_object.buffer)

                    self.buffer = compressed.extractfile(member=self.filename)

                return self.buffer.read(*args, **kwargs)

        return TarContentBuffer(file_object, cls.compressor_class, internal_file_name, mode)

    @classmethod
    def decompress(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to uncompress the content from a file_object.
        """
        try:
            # We don't need to create the directory because the extractor will create it if not exists.
            extraction_path = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor(fileobj=file_object.buffer) as compressed_file:

                # targets as None will extract all data, overwriting existing ones.
                targets = None

                if not overrider:
                    targets = []
                    for filename in compressed_file.getnames():
                        # Avoid files beginning with `..` or `/` for security reason.
                        if filename[0] == '/' or filename[0:2] == '..':
                            continue

                        if not file_object.storage.exists(
                            file_object.storage.join(extraction_path, filename)
                        ):
                            targets.append(filename)

                    # Avoid calling the extractor if the list is empty.
                    if not targets:
                        return True

                # Concurrent extract file in external file system using a custom pathlib.Path
                # with accessor informed by storage of file_object.
                compressed_file.extractall(path=file_object.storage.get_pathlib_path(extraction_path), members=targets)

        except BadZipFile:
            return False

        return True

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        try:
            file_system = file_object.storage
            file_class = file_object.__class__

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor(fileobj=file_object.buffer) as compressed_object:

                for internal_file in compressed_object.getmembers():
                    # Skip directories
                    if internal_file.isdir():
                        continue

                    # Skip duplicate only if not choosing to override.
                    if internal_file.name in file_object._content_files and not overrider:
                        continue

                    # Create file object for internal file
                    internal_file_object = file_class(
                        path=file_system.join(file_object.save_to, internal_file.name),
                        extract_data_pipeline=Pipeline(
                            'handler.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
                            'handler.pipelines.extractor.MimeTypeFromFilenameExtractor',
                        ),
                        file_system_handler=file_system
                    )

                    # Update creation and modified date
                    internal_file_object.create_date = internal_file.mtime
                    internal_file_object.update_date = internal_file.mtime

                    # Update size of file
                    internal_file_object.size = internal_file.size

                    # Update hash generating the hash file and adding its content
                    if internal_file.chksum:
                        hash_file = CRC32Hasher.create_hash_file(
                            object_to_process=internal_file_object,
                            digested_hex_value=internal_file.chksum
                        )
                        internal_file_object.hashes['crc32'] = internal_file.chksum, hash_file, CRC32Hasher

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Get mode from type
                    mode = "r" if internal_file_object.type == "text" else "rb"

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content = cls.content_buffer(
                        file_object=file_object,
                        internal_file_name=internal_file.filename,
                        mode=mode)

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[internal_file.name] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except TarError:
            return False

        return True


class ZipCompressedFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from zip and cbz files.
    """

    extensions = ['zip', 'cbz']
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor = ZipFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(cls, file_object, internal_file_name, mode='rb'):
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """

        class ZipContentBuffer(cls.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def read(self, *args, **kwargs) -> str:
                """
                Method to read the content of the object initiating the buffer if not exists.
                """
                if not hasattr(self, "buffer"):
                    # Instantiate the buffer of inner content
                    compressed = cls.compressor(file=self.source_file_object.buffer)

                    self.buffer = compressed.open(name=self.filename)

                return self.buffer.read(*args, **kwargs)

        return ZipContentBuffer(file_object, cls.compressor_class, internal_file_name, mode)

    @classmethod
    def decompress(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to uncompress the content from a file_object.
        """
        try:
            # We don't need to create the directory because the extractor will create it if not exists.
            extraction_path = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor(file=file_object.buffer) as compressed_file:

                # targets as None will extract all data, overwriting existing ones.
                targets = None

                if not overrider:
                    targets = []
                    for filename in compressed_file.namelist():
                        # Avoid files beginning with `..` or `/` for security reason.
                        if filename[0] == '/' or filename[0:2] == '..':
                            continue

                        if not file_object.storage.exists(
                                file_object.storage.join(extraction_path, filename)
                        ):
                            targets.append(filename)

                    # Avoid calling the extractor if the list is empty.
                    if not targets:
                        return True

                # Concurrent extract file in external file system using a custom pathlib.Path
                # with accessor informed by storage of file_object.
                compressed_file.extractall(path=file_object.storage.get_pathlib_path(extraction_path), members=targets)

        except BadZipFile:
            return False

        return True

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        try:
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
                        path=file_system.join(file_object.save_to, path=internal_file.filename),
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
                        object_to_process=internal_file_object,
                        digested_hex_value=internal_file.CRC
                    )
                    internal_file_object.hashes['crc32'] = internal_file.CRC, hash_file, CRC32Hasher

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Get mode from type
                    mode = "r" if internal_file_object.type == "text" else "rb"

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content = cls.content_buffer(
                        file_object=file_object,
                        internal_file_name=internal_file.filename,
                        mode=mode)

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[internal_file.filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except BadZipFile:
            return False

        return True


class RarCompressedFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from rar files.
    """

    extensions = ['rar', 'cbr']
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor = RarFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(cls, file_object, internal_file_name, mode='rb'):
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """

        class RarContentBuffer(cls.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def read(self, *args, **kwargs) -> str:
                """
                Method to read the content of the object initiating the buffer if not exists.
                """
                if not hasattr(self, "buffer"):
                    # Instantiate the buffer of inner content
                    compressed = cls.compressor(file=self.source_file_object.buffer)

                    self.buffer = compressed.open(name=self.filename)

                return self.buffer.read(*args, **kwargs)

        return RarContentBuffer(file_object, cls.compressor_class, internal_file_name, mode)

    @classmethod
    def decompress(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to uncompress the content from a file_object.
        """
        try:
            # We don't need to create the directory because the extractor will create it if not exists.
            extraction_path = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor(file=file_object.buffer) as compressed_file:

                # targets as None will extract all data, overwriting existing ones.
                targets = None

                if not overrider:
                    targets = []
                    for filename in compressed_file.namelist():
                        # Avoid files beginning with `..` or `/` for security reason.
                        if filename[0] == '/' or filename[0:2] == '..':
                            continue

                        if not file_object.storage.exists(
                            file_object.storage.join(extraction_path, filename)
                        ):
                            targets.append(filename)

                    # Avoid calling the extractor if the list is empty.
                    if not targets:
                        return True

                # Concurrent extract file in external file system using a custom pathlib.Path
                # with accessor informed by storage of file_object.
                compressed_file.extractall(path=file_object.storage.get_pathlib_path(extraction_path), members=targets)

        except (BadRarFile, NotRarFile):
            return False

        return True

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        try:
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
                        path=file_system.join(file_object.save_to, internal_file.filename),
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
                            object_to_process=internal_file_object,
                            digested_hex_value=internal_file.CRC
                        )
                        internal_file_object.hashes['crc32'] = internal_file.CRC, hash_file, CRC32Hasher

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Get mode from type
                    mode = "r" if internal_file_object.type == "text" else "rb"

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content = cls.content_buffer(
                        file_object=file_object,
                        internal_file_name=internal_file.filename,
                        mode=mode)

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[internal_file.filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except (BadRarFile, NotRarFile):
            return False

        return True


class SevenZipCompressedFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from 7z files.
    """

    extensions = ['7z', 'cb7']
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor = SevenZipFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(cls, file_object, internal_file_name, mode='rb'):
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """
        class SevenZipContentBuffer(cls.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def read(self, *args, **kwargs) -> str:
                """
                Method to read the content of the object initiating the buffer if not exists.
                """
                if not hasattr(self, "buffer"):
                    # Instantiate the buffer of inner content
                    compressed = cls.compressor(file=self.source_file_object.buffer)

                    self.buffer = next(iter(compressed.read(targets=[self.filename]).values()))

                return self.buffer.read(*args, **kwargs)

        return SevenZipContentBuffer(file_object, cls.compressor_class, internal_file_name, mode)

    @classmethod
    def decompress(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to uncompress the content from a file_object.
        """
        try:
            # We don't need to create the directory because the extractor will create it if not exists.
            extraction_path = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor(file=file_object.buffer) as compressed_file:

                # targets as None will extract all data, overwriting existing ones.
                targets = None

                if not overrider:
                    targets = []
                    for filename in compressed_file.getnames():
                        # Avoid files beginning with `..` or `/` for security reason.
                        if filename[0] == '/' or filename[0:2] == '..':
                            continue

                        if not file_object.storage.exists(
                            file_object.storage.join(extraction_path, filename)
                        ):
                            targets.append(filename)

                    # Avoid calling the extractor if the list is empty.
                    if not targets:
                        return True

                # Concurrent extract file in external file system using a custom pathlib.Path
                # with accessor informed by storage of file_object.
                compressed_file.extract(path=file_object.storage.get_pathlib_path(extraction_path), targets=targets)

        except Bad7zFile:
            return False

        return True

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
                        path=file_system.join(file_object.save_to, internal_file.filename),
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
                        object_to_process=internal_file_object,
                        digested_hex_value=internal_file.crc32
                    )
                    internal_file_object.hashes['crc32'] = internal_file.crc32, hash_file, CRC32Hasher

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Get mode from type
                    mode = "r" if internal_file_object.type == "text" else "rb"

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content = cls.content_buffer(
                        file_object=file_object,
                        internal_file_name=internal_file.filename,
                        mode=mode)

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[internal_file.filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except Bad7zFile:
            return False

        return True
