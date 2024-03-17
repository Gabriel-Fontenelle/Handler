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

from typing import TYPE_CHECKING, Iterator, Type, Any

from ..exception import ImproperlyConfiguredFile, SerializerError, ValidationError

if TYPE_CHECKING:
    from . import BaseFile
    from ..pipelines.hasher import Hasher

__all__ = [
    "FileHashes"
]


class FileHashes:
    """
    Class that store file instance digested hashes.
    """

    _cache: dict[str, tuple[str, BaseFile, Type[Hasher]]]
    """
    Descriptor to storage the digested hashes for the file instance.
    This must be instantiated at `__init__` class. 
    """
    _loaded: list[Any]
    """
    Descriptor to storage the digested hashes that were loaded from external source. 
    This must be instantiated at `__init__` class.
    """

    related_file_object: BaseFile
    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Method to create the current object using the keyword arguments.
        """
        # Set class dict and list attributes
        self._cache = {}
        self._loaded = []

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

    def __setitem__(self, hasher_name: str, value: tuple[str, BaseFile, Type[Hasher]]) -> None:
        """
        Method to set up values for file hash as dict item.
        This method expects a tuple as value to set up the hash hexadecimal value and hash file related
        to the hasher.
        """
        hex_value, hash_file, processor = value

        # Instead of using isinstance, we check for the class name to avoid circular import.
        if "BaseFile" not in [hash_class.__name__ for hash_class in hash_file.__class__.__mro__]:
            raise ImproperlyConfiguredFile("Tuple for hashes must be the Hexadecimal value and a File Object for the "
                                           "hash.")

        self._cache[hasher_name] = hex_value, hash_file, processor

        if hash_file.meta.loaded:
            # Add `hash_file` loaded from external source in a list for easy retrieval of loaded hashes.
            self._loaded.append(hasher_name)

    def __getitem__(self, hasher_name) -> tuple[str, BaseFile, Type[Hasher]]:
        """
        Method to get the hasher value and file associated saved in self._cache.
        """
        return self._cache[hasher_name]

    def __iter__(self) -> Iterator:
        """
        Method to return iterable from self._cache instead of current class.
        """
        return iter(self._cache)

    def __bool__(self) -> bool:
        """
        Method to check if there is any hash saved in self._cache.
        """
        return bool(self._cache)

    @property
    def __serialize__(self) -> dict[str, Any]:
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes: set = {"_cache", "_loaded", "related_file_object"}

        return {key: getattr(self, key) for key in attributes}

    def keys(self) -> set:
        """
        Method to return the keys availabke at `_cache`.
        """
        return set(self._cache.keys())

    def rename(self, new_filename) -> None:
        """
        This method will rename file for each hash file existing in _caches.
        This method don`t save files, only prepare the filename and content to be correct before saving it.
        """
        for hasher_name, value in self._cache.items():
            hex_value, hash_file, processor = value

            if not hash_file.meta.checksum:
                # Rename filename if is not `checksum.hasher_name`
                # complete_filename is a property that will set up additional action to rename the file`s filename if
                # it was already saved before.
                hash_file.complete_filename_as_tuple = new_filename, hasher_name

            # Load content from generator.
            # First we set up content of type binary or string.
            content: bytes | str

            if hash_file.is_binary:
                content = b""

                # Then we load content from generator using a loop.
                for block in hash_file.content_as_iterator:
                    content += block

                # Change file`s filename inside content of hash file.
                content = content.replace(
                    f"{hash_file.filename}.{hasher_name}".encode("uft-8"),
                    f"{new_filename}.{hasher_name}".encode("uft-8")
                )
            else:
                content = ""

                # Then we load content from generator using a loop.
                for block in hash_file.content_as_iterator:
                    content += block

                # Change file`s filename inside content of hash file.
                content = content.replace(f"{hash_file.filename}.{hasher_name}", f"{new_filename}.{hasher_name}")

            # Set-up new content after renaming and specify that hash_file was not saved yet.
            hash_file.content = content
            hash_file._actions.to_save()

    def validate(self, force: bool=False) -> None:
        """
        Method to validate the integrity of file comparing hashes`s hex value with file content.
        This method will only check the first hex value from files loaded, or any cached hash if no hash loaded from
        external source is available, for efficient sake. If desire to check all hashes in loaded set `force` to True.
        """
        if not (self._loaded or self._cache):
            raise ValueError(f"There is no hash available to compare for file {self.related_file_object}.")

        for hash_name in self._loaded or self._cache.keys():
            hex_value, hash_file, processor = self._cache[hash_name]
            # Compare content with hex_value
            result = processor.check_hash(object_to_process=self.related_file_object, compare_to_hex=hex_value)

            if result is False:
                raise ValidationError(f"File {self.related_file_object} don`t pass the integrity check with "
                                      f"{hash_name}!")

            if not force:
                break

    def save(self, overwrite: bool=False) -> None:
        """
        Method to save all hashes files if it was not saved already.
        """
        if not self.related_file_object:
            raise ImproperlyConfiguredFile("A related file object must be specified for hashes before saving.")

        for hex_value, hash_file, processor in self._cache.values():
            if hash_file._actions.save:
                if hash_file.meta.checksum:
                    # If file is CHECKSUM.<hasher_name> we not allow to overwrite.
                    hash_file.save(overwrite=False, allow_update=overwrite)
                else:
                    hash_file.save(overwrite=overwrite, allow_update=overwrite)
