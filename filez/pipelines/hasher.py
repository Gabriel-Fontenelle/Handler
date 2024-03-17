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

# Python internals
from __future__ import annotations

import hashlib
from typing import Any, Type, TYPE_CHECKING, Iterator, Sequence

from zlib import crc32

from ..exception import ImproperlyConfiguredFile
# core modules
from ..pipelines import Pipeline
# modules
from ..storage import Storage

if TYPE_CHECKING:
    from ..file import BaseFile

__all__ = [
    'Hasher',
    'CRC32Hasher',
    'MD5Hasher',
    'SHA256Hasher'
]


class Hasher:
    """
    Base class to be inherent to define class to be used on Hasher pipelines.
    """

    file_system_handler: Type[Storage] = Storage
    """
    File System Handler currently in use by class.
    """
    hasher_name: str
    hasher_name = None
    """
    Name of hasher algorithm and also its extension abbreviation.
    """
    hash_objects: dict = {}
    """
    Cache of hashes for given objects' ids.
    """
    hash_digested_values: dict = {}
    """
    Cache of digested hashes for given objects filename.
    """

    @classmethod
    def check_hash(cls, **kwargs: Any) -> bool | None:
        """
        Method to verify integrity of file checking if hash save in file object is the same
        that is generated from file content. File content can be from File System, Memory or Stream
        so it is susceptible to data corruption.
        """
        object_to_process: BaseFile = kwargs.pop('object_to_process')
        hex_value: str = kwargs.pop('compare_to_hex', None) or object_to_process.hashes[cls.hasher_name][0]

        hash_instance: Any = cls.instantiate_hash()

        content_iterator: Iterator[Sequence[object]] | None = object_to_process.content_as_iterator

        if content_iterator is None:
            return None

        cls.generate_hash(hash_instance=hash_instance, content_iterator=content_iterator)
        digested_hex_value: str = cls.digest_hex_hash(hash_instance=hash_instance)

        return digested_hex_value == hex_value


    @classmethod
    def digest_hash(cls, hash_instance: Any) -> str:
        """
        Method to digest the hash generated at hash_instance.
        """
        return hash_instance.digest()

    @classmethod
    def digest_hex_hash(cls, hash_instance: Any) -> str:
        """
        Method to digest the hash generated at hash_instance.
        """
        return hash_instance.hexdigest()

    @classmethod
    def get_hash_objects(cls) -> dict:
        """
        Method to get the `hash_object` filtering the `hasher_name` considering that `hash_objects` is a dictionary
        shared between all classes that inherent from `Hasher`.
        """
        hash_object: dict = cls.hash_objects.get(cls.hasher_name, {})
        cls.hash_objects[cls.hasher_name] = hash_object

        return hash_object

    @classmethod
    def get_hash_instance(cls, file_id: str) -> Any:
        """
        Method to get the cached instantiate hash object for the given file id.
        """
        try:
            return cls.hash_objects[cls.hasher_name][file_id]
        except KeyError:
            h: Any = cls.instantiate_hash()
            if cls.hasher_name in cls.hash_objects:
                cls.hash_objects[cls.hasher_name][file_id] = h
            else:
                cls.hash_objects[cls.hasher_name] = {file_id: h}

            return h

    @classmethod
    def update_hash(cls, hash_instance: Any, content: str | bytes) -> None:
        """
        Method to update content in hash_instance to generate the hash. We convert all content to bytes to
        generate a hash of it.
        """
        if isinstance(content, str):
            content = content.encode('utf8')

        hash_instance.update(content)

    @classmethod
    def instantiate_hash(cls) -> Any:
        """
        Method to instantiate the hash generator to be used digesting the hash.
        """
        raise NotImplementedError("Method instantiate_hash must be overwrite on child class.")

    @classmethod
    def generate_hash(cls, hash_instance: Any, content_iterator: Iterator[Sequence[bytes | str]]) -> None:
        """
        Method to update the hash to be generated from content in blocks using a normalized content that can be
        iterated regardless from its source (e.g. file system, memory, stream).
        """
        for block in content_iterator:
            cls.update_hash(hash_instance, block)

    @classmethod
    def create_hash_file(cls, object_to_process: BaseFile, digested_hex_value: str) -> BaseFile:
        """
        Method to create a file structured for the hash based on same class as object_to_process
        """
        if object_to_process.save_to is None or not object_to_process.complete_filename:
            raise ImproperlyConfiguredFile("Generating a hash file for a file without a directory set at `save_to`"
                                           " and without a `complete_filename` is not supported.")

        # Add hash to file
        hash_file: BaseFile = object_to_process.__class__(
            path=f"{cls.file_system_handler.sanitize_path(object_to_process.save_to)}"
                 f"{cls.file_system_handler.sep}{object_to_process.complete_filename}.{cls.hasher_name}",
            extract_data_pipeline=Pipeline(
                'filez.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
                'filez.pipelines.extractor.MimeTypeFromFilenameExtractor',
            ),
            file_system_handler=object_to_process.storage
        )
        # Set up metadata checksum as boolean to indicate whether the source
        # of the hash is a CHECKSUM.hasher_name file (contains multiple files) or not.
        hash_file.meta.checksum = False

        # Set up metadata loaded as boolean to indicate whether the source
        # of the hash was loaded from a file or not.
        hash_file.meta.loaded = False

        # Generate content for file
        content: str = "# Generated by Handler\r\n"
        content += f"{digested_hex_value} {object_to_process.filename}\r\n"
        hash_file.content = content

        # Change hash file state to be saved
        hash_file._actions.to_save()

        return hash_file

    @classmethod
    def load_from_file(
        cls,
        directory_path: str,
        filename: str,
        extension: str | None,
        full_check: bool = False
    ) -> tuple[str, str]:
        """
        Method to find and load the hash value from a file named <filename>.<hasher name> or CHECKSUM.<hasher name>
        or <directory_path>.<hasher_name>.
        Both names will be used if `full_check` is True, else only <filename>.<hasher name> will be searched.
        """
        extension = f'.{extension}' if extension else ''
        full_name: str = filename + extension

        # Load and cache dictionary
        hash_digested: dict = cls.hash_digested_values.get(cls.hasher_name, {})
        if not hash_digested:
            # Add missing hasher_name dictionary
            cls.hash_digested_values[cls.hasher_name] = hash_digested

        hash_directories: dict = hash_digested.get(full_name, {})
        if not hash_directories:
            cls.hash_digested_values[cls.hasher_name][full_name] = hash_directories

        # Return cached hash if already processed.
        if directory_path in hash_directories:
            return hash_directories[directory_path]

        files_to_check: list[str] = [
            # Check checksum files that contain the full name of file plus `cls.hasher_name`
            full_name + '.' + cls.hasher_name,
            # Check checksum files that removed the extension from filename plus `cls.hasher_name`.
            filename + '.' + cls.hasher_name,
            # Check checksum files that literally are named `CHECKSUM`.
            'CHECKSUM.' + cls.hasher_name,
            # Check checksum files that are named after its directory
            cls.file_system_handler.get_filename_from_path(directory_path) + '.' + cls.hasher_name
        ]

        if full_check:
            # Iterate through directory to find all files of type `cls.hasher_name` in order to load all available
            # checksums.
            files_to_check += list(cls.file_system_handler.list_files(directory_path, f'*.{cls.hasher_name}'))

        # Try to find filename with hasher_name in directory_path or
        # try to find filename in CHECKSUM.<hasher_name> in directory_path
        for hash_filename in set(files_to_check):
            file_path = cls.file_system_handler.join(directory_path, hash_filename)
            if cls.file_system_handler.exists(file_path):
                for line in cls.file_system_handler.read_lines(file_path):
                    # We ignore lines that begin with comment describer `;`.
                    if ';' != line[0] and full_name in line:
                        # Get hash from line and return it.
                        # It's assuming that first argument until first white space if the hash and second
                        # is the filename.
                        hashed_value: str = line.lstrip().split(maxsplit=1)[0]

                        # Add hash to cache
                        hash_directories[directory_path] = hashed_value

                        return hashed_value, hash_filename

        raise FileNotFoundError(f"{full_name} not found!")

    @classmethod
    def process(cls, **kwargs: Any) -> bool:
        """
        Method used to run this class on Processor's Pipeline for Hash.
        This method and to_processor() is not need to generate hash outside a pipelines.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for hasher uses only one object that must be settled through first argument
        or through key work `object`.

        FUTURE CONSIDERATION: Making the pipeline multi thread or multi process will require that iterator of content
        be a isolated copy of content to avoid race condition when using content where its provenience came from file
        pointer.

        This processors return boolean to indicate that process was ran successfully.
        """
        object_to_process: BaseFile = kwargs['object_to_process']
        try_loading_from_file: bool = kwargs.get('try_loading_from_file', False)
        full_check: bool = kwargs.get('full_check', False)

        # Check if there is already a hash previously loaded on file,
        # so that we don't try to digest it again.
        if cls.hasher_name not in object_to_process.hashes:

            if try_loading_from_file:
                # Check if hash loaded from file and if so exit with success.
                if cls.process_from_file(full_check=full_check, **kwargs):
                    return True

            file_id: str = str(id(object_to_process))

            # Check if there is already a hash previously generated in cache.
            if file_id not in cls.get_hash_objects():
                # Check if there is a content loaded for file before generating a new one
                content = object_to_process.content_as_iterator
                if content is None:
                    return False

                # Get hash_instance
                hash_instance: Any = cls.get_hash_instance(file_id)

                # Generate hash
                cls.generate_hash(hash_instance=hash_instance, content_iterator=content)

            else:
                hash_instance = cls.get_hash_objects()[file_id]

            # Digest hash
            digested_hex_value: str = cls.digest_hex_hash(hash_instance=hash_instance)

            # Add hash to file
            hash_file: BaseFile = cls.create_hash_file(object_to_process, digested_hex_value)

            object_to_process.hashes[cls.hasher_name] = (
                digested_hex_value, hash_file, cls
            )

        return True

    @classmethod
    def process_from_file(cls, **kwargs: Any) -> bool:
        """
        Method to try to process the hash from a hash's file instead of generating one.
        It will return False if no hash was found in files.

        Specifying the keyword argument `full_check` as True will make the processor to verify the hash value in file
        CHECKSUM.<cls.hasher_name>, if there is any in the same directory as the file to be processed.
        """
        object_to_process: BaseFile = kwargs.pop('object_to_process')
        full_check: bool = kwargs.pop('full_check', True)

        # Save current file system filez
        class_file_system_handler: Type[Storage] = cls.file_system_handler

        cls.file_system_handler = object_to_process.storage

        # Don't proceed if no path was setted.
        if not object_to_process.path:
            return False

        path: str = cls.file_system_handler.sanitize_path(object_to_process.path)
        directory_path: str = cls.file_system_handler.get_directory_from_path(path)

        try:
            hex_value, hash_filename = cls.load_from_file(
                directory_path=directory_path,
                filename=object_to_process.filename,
                extension=object_to_process.extension,
                full_check=full_check
            )
        except FileNotFoundError:
            return False
        finally:
            # Restore File System attribute to original.
            cls.file_system_handler = class_file_system_handler

        file_system: Type[Storage] = object_to_process.storage

        # Add hash to file. The content will be obtained from file pointer.
        hash_file: BaseFile = object_to_process.__class__(
            path=f"{file_system.join(directory_path, hash_filename)}",
            extract_data_pipeline=Pipeline(
                'filez.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
                'filez.pipelines.extractor.MimeTypeFromFilenameExtractor',
                'filez.pipelines.extractor.FileSystemDataExtractor'
            ),
            file_system_handler=file_system
        )
        # Set-up metadata checksum as boolean to indicate whether the source
        # of the hash is a CHECKSUM.hasher_name file (contains multiple files) or not.
        hash_file.meta.checksum = 'CHECKSUM.' in hash_filename

        # Set-up metadata loaded as boolean to indicate whether the source
        # of the hash was loaded from a file or not.
        hash_file.meta.loaded = True

        # Change hash file state to be a existing one already saved.
        hash_file._state.adding = False
        hash_file._actions.saved()

        # Set-up the hex value and hash_file to hash content.
        object_to_process.hashes[cls.hasher_name] = hex_value, hash_file, cls

        return True


class MD5Hasher(Hasher):
    """
    Class specifying algorithm MD5 to be used on Hasher pipelines.
    """

    hasher_name: str = 'md5'
    """
    Name of hasher algorithm and also its extension abbreviation.
    """

    @classmethod
    def instantiate_hash(cls) -> Any:
        """
        Method to instantiate the hash generator to be used digesting the hash.
        """
        return hashlib.md5()


class SHA256Hasher(Hasher):
    """
    Class specifying algorithm SHA256 to be used on Hasher pipelines.
    """

    hasher_name: str = 'sha256'
    """
    Name of hasher algorithm and also its extension abbreviation.
    """

    @classmethod
    def instantiate_hash(cls) -> Any:
        """
        Method to instantiate the hash generator to be used digesting the hash.
        """
        return hashlib.sha256()


class CRC32Hasher(Hasher):
    """
    Class specifying algorithm CRC32 to be used on Hasher pipelines.
    """

    hasher_name: str = 'crc32'
    """
    Name of hasher algorithm and also its extension abbreviation.
    """

    @classmethod
    def instantiate_hash(cls) -> dict[str, str]:
        """
        Method to instantiate the hash generator to be used digesting the hash.
        """
        return {'crc32': "0"}

    @classmethod
    def digest_hash(cls, hash_instance: dict[str, Any]) -> str:
        """
        Method to digest the hash generated at hash_instance.
        As CRC32 don't work as hashlib we used the instantiate_hash to start a dictionary
        for the sum of the digested hash.
        """
        return hash_instance['crc32']

    @classmethod
    def digest_hex_hash(cls, hash_instance: dict[str, Any]) -> str:
        """
        Method to digest the hash generated at hash_instance.
        """
        return hash_instance['crc32']

    @classmethod
    def update_hash(cls, hash_instance: dict[str, Any], content: bytes | str) -> None:
        """
        Method to update content in hash_instance to generate the hash. We convert all content to bytes to
        generate a hash of it.
        """
        if isinstance(content, str):
            content = content.encode('utf8')

        hash_instance['crc32'] = str(crc32(content, hash_instance['crc32']))
