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

import logging
import re
from typing import Any
from typing import Type, Pattern, TYPE_CHECKING
from uuid import uuid4

# modules
from ..storage import Storage

if TYPE_CHECKING:
    from ..file import BaseFile

__all__ = [
    'Renamer',
    'WindowsRenamer',
    'LinuxRenamer',
    'UniqueRenamer'
]


class Renamer:
    """
    Base class to be inherent to define class to be used on Renamer pipeline.
    """

    stopper: bool = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """
    file_system_handler: Type[Storage] = Storage
    """
    Variable to store the local storage system.
    """
    enumeration_pattern: Pattern
    enumeration_pattern = None
    """
    Variable that define the pattern to detect enumeration in file system.
    """

    reserved_names: list = []
    """
    Variable that define the reversed names by the file system that should be avoid in renaming.
    """

    @classmethod
    def prepare_filename(cls, filename: str, extension: str | None = None) -> tuple[str, str | None]:
        """
        Method to separated extension from filename if extension
        not informed and save on class.
        """
        # Remove extension from filename if it was given
        if extension and filename[-len(extension):] == extension:
            filename = filename[:-len(f".{extension}")]

        return filename, extension

    @classmethod
    def get_name(cls, directory_path: str, filename: str, extension: str | None) -> tuple[str, str | None]:
        """
        Method to get the new generated name.
        This class should raise BlockingIOError when a custom error should happen that will be
        caught by `process` when using Pipeline.
        """
        raise NotImplementedError("Method get_name must be overwrite on child class.")

    @classmethod
    def process(cls, **kwargs: Any) -> bool:
        """
        Method used to run this class on Processor`s Pipeline for Files.
        This method and to_processor() is not need to rename files outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for renamer uses only one object that must be settled through first argument
        or through key work `object`.

        The keyword argument `path_attribute` allow using a different attribute for specify the file object path other
        than the default `path`.
        The keyword argument `reserved_names` allow for override of current list of reserved_names in pipeline. This
        override will affect the class and thus all usage of `reserved_names`. It isn`t thread safe.

        FUTURE CONSIDERATION: Making the pipeline multi thread or multi process only will required that
        a lock be put between usage of get_name.
        FUTURE CONSIDERATION: Multi thread will need to consider that the attribute `file_system_handler`
        is shared between the reference of the class and all object of it and will have to be change the
        code (multi process don't have this problem).

        This processors return boolean to indicate that process was ran successfully.

        This method can throw BlockingIOError when trying to rename the file.
        The `Pipeline.run` method will catch it.
        """
        # Get default values from keywords arguments
        object_to_process: BaseFile = kwargs.pop('object_to_process')
        path_attribute: str = kwargs.pop('path_attribute', 'path')
        reserved_names: list | None = kwargs.pop('reserved_names', None)

        # Override current reserved names if list of new one provided.
        if reserved_names:
            cls.clean_reserved_names()
            cls.add_reserved_name(reserved_names)

        # Prepare filename from File's object
        filename, extension = cls.prepare_filename(object_to_process.filename, object_to_process.extension)

        # Save current file system filez
        class_file_system_handler = cls.file_system_handler

        # Overwrite File System attribute with File System of File only when running in pipeline.
        # This will alter the File System for the class, any other call to this class will use the altered
        # file system.
        cls.file_system_handler = object_to_process.storage

        # Get directory from object to be processed.
        path = cls.file_system_handler.sanitize_path(getattr(object_to_process, path_attribute))

        # When is not possible to get new name by some problem either with file or filesystem
        # is expected BlockingIOError
        new_filename, extension = cls.get_name(path, filename, extension)

        # Restore File System attribute to original.
        cls.file_system_handler = class_file_system_handler

        # Set new name at File's object.
        # The File class should set the old name at File`s cache/history automatically,
        # filename and extension should be property functions.
        object_to_process.complete_filename_as_tuple = (new_filename, extension)

        return True

    @classmethod
    def is_name_reserved(cls, filename: str, extension: str) -> bool:
        """
        Method to check if filename in list of reserved names.
        Those name should be set-up before rename pipeline being called.
        """
        return filename + extension in cls.reserved_names

    @classmethod
    def add_reserved_name(cls, value: str | list) -> None:
        """
        Method to update list of reserved names allowing append of multiple values with list.
        This method accept string or list to be added to reserved_names.
        """
        if isinstance(value, str):
            cls.reserved_names.append(value)

        elif isinstance(value, list):
            cls.reserved_names += value

    @classmethod
    def clean_reserved_names(cls) -> None:
        """
        Method to reset the `reserved_names` attribute to a empty list.
        """
        cls.reserved_names = []

    @classmethod
    def register_error(cls, error: Exception) -> None:
        """
        Method to log error in system. It could be override to register error in list or distinct output.
        """
        # Log error message
        logging.error(str(error))


class WindowsRenamer(Renamer):
    """
    Class following Windows style of renaming existing file to be used on Renamer pipelines.
    """
    enumeration_pattern: Pattern = re.compile(r' ?\([0-9]+\)$|\[[0-9]+\]$|$')

    @classmethod
    def get_name(cls, directory_path: str, filename: str, extension: str | None) -> tuple[str, str | None]:
        """
        Method to get the new generated name.
        If there is a duplicated name the new name will follow
        the style of Windows: `new name (1).ext`
        """
        # Prepare filename and extension removing enumeration from filename
        # and setting up a empty string is extension is None
        filename = cls.enumeration_pattern.sub('', filename)
        formatted_extension: str = f'.{extension}' if extension else ''

        i = 0
        while (
                cls.file_system_handler.exists(directory_path + filename + formatted_extension)
                or cls.is_name_reserved(filename, formatted_extension)
        ):
            i += 1
            filename = cls.enumeration_pattern.sub(f' ({i})', filename)

        return filename, extension


class LinuxRenamer(Renamer):
    """
    Class following Linux style of renaming existing file to be used on Renamer pipelines.
    """
    enumeration_pattern: Pattern = re.compile(r'( +)?\- +[0-9]+$|$')

    @classmethod
    def get_name(cls, directory_path: str, filename: str, extension: str | None) -> tuple[str, str | None]:
        """
        Method to get the new generated name.
        If there is a duplicated name the new name will follow
        the style of Linux: `new name - 1.ext`
        """
        # Prepare filename and extension removing enumeration from filename
        # and setting up a empty string is extension is None
        filename = cls.enumeration_pattern.sub('', filename)
        formatted_extension: str = f'.{extension}' if extension else ''

        i = 0
        while (
                cls.file_system_handler.exists(directory_path + filename + formatted_extension)
                or cls.is_name_reserved(filename, formatted_extension)
        ):
            i += 1
            filename = cls.enumeration_pattern.sub(f' - {i}', filename)

        return filename, extension


class UniqueRenamer(Renamer):

    @classmethod
    def get_name(cls, directory_path: str, filename: str, extension: str | None) -> tuple[str, str | None]:
        """
        Method to get the new generated name. The new name will be the UUID version 4.
        This method will throw a BlockingIOError if there is more then
        100 tries to generate a unique UUID4.
        """
        formatted_extension: str = f'.{extension}' if extension else ''

        #Generate Unique filename
        filename = str(uuid4())

        i = 0
        while (
                cls.file_system_handler.exists(directory_path + filename + formatted_extension)
                or cls.is_name_reserved(filename, formatted_extension)
        ) and i < 100:
            i += 1
            #Generate Unique filename
            filename = str(uuid4())

        if i == 100:
            raise BlockingIOError("Too many files being filez simultaneous!")

        return filename, extension
