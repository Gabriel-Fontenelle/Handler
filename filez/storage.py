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

import os
import re
from datetime import datetime
from filecmp import cmp
from glob import iglob
from io import open
from os.path import (
    abspath,
    basename,
    dirname,
    exists,
    getctime,
    getmtime,
    getsize,
    isdir,
    join,
    normcase,
    normpath,
)
from pathlib import (
    Path,
    WindowsPath,
    PosixPath
)
# third-party
from shutil import copyfile, rmtree
from sys import version_info
from typing import Any, TYPE_CHECKING, Generator, Iterator, Pattern, IO

from send2trash import send2trash

if TYPE_CHECKING:
    from io import BytesIO, StringIO

__all__ = [
    'Storage',
    'WindowsFileSystem',
    'LinuxFileSystem',
]


class Storage:
    """
    Class that standardized methods of different file systems.
    """

    sep: str = os.sep
    """
    Directory separator in the filesystem.
    """
    folder_size_limit: int = 200
    """
    Limit for the length of directory path 
    """
    path_size_limit: int = 254
    """
    Limit for the whole path
    """

    backup_extension: Pattern = re.compile(r'\.bak(\.\d*)?$')
    """
    Define what is identifiable as a backup`s extension.
    """

    temporary_folder: str
    temporary_folder = None
    """
    Define the location of temporary content in filesystem.
    """

    # High-end methods to use with files and directories.
    # Those methods were created to be used by BaseFile.
    @classmethod
    def is_dir(cls, path: str) -> bool:
        """
        The default implementation uses `os.path` operations.
        Override this method if that’s not appropriate for your storage.
        """
        return isdir(cls.get_absolute_path(path))

    @classmethod
    def is_file(cls, path: str) -> bool:
        """
        The default implementation uses `os.path` operations.
         Override this method if that’s not appropriate for your storage.
        """
        return not cls.is_dir(path)

    @classmethod
    def is_empty(cls, path: str) -> bool:
        """
        The default implementation uses `os.path` operations.
        Override this method if that’s not appropriate for your storage.
        """
        return getsize(path) == 0

    @classmethod
    def create_directory(cls, path: str, mode: int = 0o777) -> bool:
        """
        Method to create directory in the file system.
        This method will try to create a directory only if it not exists already.
        Override this method if that’s not appropriate for your storage.
        """
        # Create Directory
        if not path:
            raise ValueError("Is necessary the receive a folder name on create_directory method.")

        if not cls.exists(path):
            os.makedirs(path, mode)
            return True

        return False

    @classmethod
    def create_file(cls, path: str) -> bool:
        """
        Method to create an empty file.
        This method will try to create a file only if it not exists already.
        Override this method if that’s not appropriate for your storage.
        """
        # Check if file exists.
        if cls.exists(path):
            return False

        basedir: str = dirname(path)

        cls.create_directory(basedir)

        open(path, 'a').close()

        return True

    @classmethod
    def open_file(cls, path: str, mode: str = 'rb') -> StringIO | BytesIO | IO:
        """
        Method to return a buffer to a file. This method don't automatically closes file buffer.
        Override this method if that’s not appropriate for your storage.
        """
        return open(path, mode=mode)

    @classmethod
    def close_file(cls, file_buffer: StringIO | BytesIO | IO) -> None:
        """
        Method to close a buffer previously opened by open_file.
        Override this method if that’s not appropriate for your storage.
        """
        return file_buffer.close()

    @classmethod
    def save_file(cls, path: str, content: Any, **kwargs: Any) -> None:
        """
        Method to save content on file.
        This method will throw an exception if content is not iterable.
        Override this method if that’s not appropriate for your storage.
        """
        content = iter(content)

        if 'file_mode' not in kwargs:
            kwargs['file_mode'] = 'a'

        if 'write_mode' not in kwargs:
            kwargs['write_mode'] = 'b'

        with open(path, kwargs['file_mode'] + kwargs['write_mode']) as file_pointer:
            for chunk in content:
                file_pointer.write(chunk)
                file_pointer.flush()
                os.fsync(file_pointer.fileno())

    @classmethod
    def backup(cls, file_path_origin: str, force: bool = False) -> bool:
        """
        Method used to copy a file in the same path with .bak append to its name.
        This method only try to copy if file exists.
        This method not check if there is an error and maybe can
        produce a OSError exception if not enough space in destination.

        This method will overwrite destination file if force is True. If force is False
        it will append a number from a counter to `.bak` until there is existing file.

        Override this method if that’s not appropriate for your storage.
        """
        file_path_destination: str = file_path_origin + '.bak'

        i = 1
        while not force and cls.exists(file_path_destination):
            file_path_destination = re.sub(cls.backup_extension, f".bak.{i}", file_path_destination)
            i += 1

        return cls.copy(file_path_origin, file_path_destination, force=True)

    @classmethod
    def copy(cls, file_path_origin: str, file_path_destination: str, force: bool = False) -> bool:
        """
        Method used to copy a file from origin to destination.
        This method only try to copy if file exists.
        This method not check if there is a error and maybe can
        produce a OSError exception if not enough space in destination.

        This method will overwrite destination file if force is True.
        Override this method if that’s not appropriate for your storage.

        TODO: Test what happens if file_path_destination is a directory.
        """
        if cls.exists(file_path_origin) and (not cls.exists(file_path_destination) or force):
            copyfile(file_path_origin, file_path_destination)
            return True

        return False

    @classmethod
    def move(cls, file_path_origin: str, file_path_destination: str, force: bool = False) -> bool:
        """
        Method used to move a file from origin to destination.
        This method do use copy_file to first copy the file and after send file to trash.
        The file only will be sent to trash if no exception was raised on copy.
        Override this method if that’s not appropriate for your storage.
        """
        if cls.copy(file_path_origin, file_path_destination, force):
            cls.delete(file_path_origin)
            return True

        return False

    @classmethod
    def rename(cls, source: str, destination: str) -> bool:
        """
        Method to rename a file from origin to destination.
        This method try to find a new filename if one already exists.
        """
        i = 1
        while cls.exists(destination):
            destination = cls.get_renamed_path(path=destination, sequence=i)
            i += 1

        return cls.move(source, destination)

    @classmethod
    def replace(cls, source: str, destination: str) -> bool:
        """
        Method to rename a file from origin to destination.
        This method will replace the destination path if already exists.
        """
        return cls.move(source, destination, force=True)

    @classmethod
    def clone(cls, source: str, destination: str) -> bool:
        """
        Method to copy a file from origin to destination avoiding override of destination file.
        This method try to find a new filename if one already exists before copying the file.
        The difference between this method and copy is that this method generate a new filename
        for destination file before trying to copy to destination path.
        """
        i = 1
        while cls.exists(destination):
            destination = cls.get_renamed_path(path=destination, sequence=i)
            i += 1

        return cls.copy(source, destination, force=False)

    @classmethod
    def delete(cls, path: str, force: bool = False) -> bool:
        """
        Method to delete a file or a whole directory.
        this method will delete permanently a file or directory
        specified in path if `force` is True. If `force` is False
        it will only send `path` to trash (It's more safe to send to trash).
        Override this method if that’s not appropriate for your storage.
        """
        if not cls.exists(path):
            return False

        if not force:
            send2trash(path)

        elif cls.is_file(path):
            os.remove(path)

        else:
            rmtree(path)

        return True

    @classmethod
    def exists(cls, path: str) -> bool:
        """
        The default implementation uses `os.path` operations.
        Override this method if that’s not appropriate for your storage.
        """
        return exists(path)

    @classmethod
    def compare(cls, file_path_1: str, file_path_2: str) -> bool:
        """
        Method used to compare file from file_path informed.
        Override this method if that’s not appropriate for your storage.
        """
        # Compare data from pointers and not stats.

        return cmp(file_path_1, file_path_2, False)

    @classmethod
    def join(cls, *paths: str) -> str:
        """
        Method used to concatenate two or more paths.
        Override this method if that’s not appropriate for your storage.
        """
        return join(*paths)

    @classmethod
    def list_files(cls, path: str, filter_pattern: str = "*") -> Generator[str]:
        """
        Method used to list files following pattern in filter.
        Override this method if that’s not appropriate for your storage.
        This method must return an iterable that filter results based on filter values.
        `filter` should accept wildcards.
        """
        if version_info.major == 3 and version_info.minor > 9:
            iter_glob = iglob(filter_pattern, root_dir=path)
        else:
            iter_glob = iglob(f"{path}{cls.sep}{filter_pattern}")

        for file in iter_glob:
            if cls.is_file(cls.join(path, file)):
                yield file

    @classmethod
    def list_files_and_directories(cls, path: str) -> Iterator:
        """
        Method used to list directories and files.
        """
        if version_info.major == 3 and version_info.minor > 9:
            return iglob("*", root_dir=path)
        else:
            return iglob(f"{path}")

    @classmethod
    def get_filename_from_path(cls, path: str) -> str:
        """
        Method used to get the filename from a complete path.
        """
        return basename(path)

    @classmethod
    def get_directory_from_path(cls, path: str) -> str:
        """
        Method used to get the path without filename from a complete path.
        """
        if cls.is_dir(path):
            return path

        return dirname(path)

    @classmethod
    def get_relative_path(cls, path: str, relative_to: str) -> str:
        """
        Method used to get relative path given two paths. The relative path is based on the path in based_on.
        relative_to = c/a/b/c/d/g/index.html
        path = c/a/b/e/i/file.c
        return = ../../../e/i/file.c

        path and relative_to must have its separator correct before being used.
        """
        
        # Fix directory without sep on end
        fix: tuple = relative_to.rpartition(cls.sep)
        if '.' not in fix[2]:
            relative_to += cls.sep

        base_length: int = len(relative_to)
        path_length: int = len(path)
        count: int = 0
        last_bar: int = 0

        length: int = path_length if base_length > path_length else base_length

        for i in range(0, length):
            if path[i] != relative_to[i]:
                break
            else:
                count += 1
                if path[i] == '/':
                    last_bar = count

        if last_bar:
            return '../' * relative_to[last_bar:].count(cls.sep) + path[last_bar:]

        return path

    @classmethod
    def get_absolute_path(cls, path: str) -> str:
        """
        Method used to convert the relative path informed in `path` to its absolute version.
        """
        return abspath(path)

    @classmethod
    def get_size(cls, path: str) -> int:
        """
        Method to get the size of file at path in bytes.
        """
        return getsize(path)

    @classmethod
    def get_modified_date(cls, path: str) -> datetime:
        """
        Method to get the modified time as datetime converted from float.
        """
        return datetime.fromtimestamp(getmtime(path))

    @classmethod
    def get_created_date(cls, path: str) -> datetime:
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        This method should be overwritten in child specific for Operational System.
        """
        raise NotImplementedError("Method get_created_date(path) should be accessed through inherent class.")

    @classmethod
    def get_renamed_path(cls, path: str, sequence: int = 1) -> str:
        """
        Method used to get a new filename base on `path`.
        This method requires that attribute `file_sequence_style` be set in child specific for Operational System or
        this method should be overwritten in child specific for Operational System as each OS has its own style of
        sequence.
        """
        if not (
                hasattr(cls, 'file_sequence_style')
                and isinstance(cls.file_sequence_style, tuple)
                and len(cls.file_sequence_style) == 2
                and isinstance(cls.file_sequence_style[0], re.Pattern)
                and isinstance(cls.file_sequence_style[1], str)
                and 'sequence' in cls.file_sequence_style[1]
        ):
            raise NotImplementedError("Method `get_renamed_path(path, sequence)` requires that `file_sequence_style` "
                                      "to be set in through inherent class as a tuple with a pattern and string value "
                                      "with the placeholder for sequence `{sequence}`.")

        filename: str = cls.get_filename_from_path(path)

        return path.replace(filename, re.sub(
            cls.file_sequence_style[0], cls.file_sequence_style[1].format(sequence=sequence), filename)
        )

    @classmethod
    def get_path_id(cls, path: str) -> str:
        """
        Method to get the file system id for path.
        This method should be overwritten in child specific for Operational System.
        """
        raise NotImplementedError("Method get_path_id(path) should be accessed through inherent class.")

    @classmethod
    def get_temp_directory(cls) -> str:
        if cls.temporary_folder is None:
            raise ValueError(f"There is no `temporary_folder` attribute set for {cls.__name__}!")

        if not cls.exists(cls.temporary_folder):
            cls.create_directory(cls.temporary_folder)

        return cls.temporary_folder

    @classmethod
    def read_lines(cls, path: str) -> Generator[str]:
        """
        Method generator to get lines from file without loading all data in one step.
        """
        with open(path, 'r') as file:
            line = file.readline()
            while line:
                yield line
                line = file.readline()

    @classmethod
    def sanitize_path(cls, path: str) -> str:
        """
        Method to normalize a path for use.
        This method collapse redundant separators and up-level references so that A//B, A/B/, A/./B and A/foo/../B
        all become A/B.
        """
        return normpath(path.replace('/', cls.sep))

    # Low-end methods to use with Path
    # Those methods were created to be used by pathlib.Path, tough
    # they can be used by BaseFile.
    @classmethod
    def opener(cls, *args: Any, **kwargs: Any) -> Any:
        """
        Method to open the file as a file pointer compatible with os.open.
        This method should not be used, it exists only for usage with get_accessor.
        """
        return os.open(*args, **kwargs)

    @classmethod
    def get_pathlib_path(cls, path: str) -> Path:
        """
        Method to get the custom Path class with accessor override.
        This method should be overwritten in child specific for Operational System.
        """
        raise NotImplementedError("Method get_pathlib_path(path) should be accessed through inherent class.")


class WindowsFileSystem(Storage):
    """
    Class that standardized methods of file systems for Windows Operational System.
    """

    temporary_folder: str = "C:\\temp\\Handler"
    """
    Define the location of temporary content in filesystem.
    """
    file_sequence_style: tuple[Pattern[str], str] = (re.compile(r"(\ *\(\d+?\))?(\.[^.]*$)"), r" ({sequence})\2")
    """
    Define the pattern to use to replace a sequence in the stylus of the filesystem.
    The first part identify the search and the second the replace value.
    This allow search by `<str>.<str>` and replace by `<str> (<int>).<str>`.
    """

    @classmethod
    def get_path_id(cls, path: str) -> str:
        """
        Method to get the file system id for a path.
        Path can be both a directory or file.

        TODO: Test it at Windows.
        """
        # TODO: Conclude function after testing on Windows.
        file = r"C:\Users\Grandmaster\Desktop\testing.py"
        output = os.popen(fr"fsutil file queryfileid {file}").read()

        return str(output)

    @classmethod
    def get_created_date(cls, path: str) -> datetime:
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See https://stackoverflow.com/a/39501288/1709587 for explanation.
        Source: https://stackoverflow.com/a/39501288
        """
        time = getctime(path)

        return datetime.fromtimestamp(time)

    @classmethod
    def sanitize_path(cls, path: str) -> str:
        """
        Method to normalize a path for use.
        This method collapse redundant separators and up-level references so that A//B, A/B/, A/./B and A/foo/../B
        all become A/B. It will also convert uppercase character to lowercase and `/` to `\\`.
        """
        return normpath(normcase(path))

    @classmethod
    def get_pathlib_path(cls, path: str) -> Path:
        """
        Method to get the custom Path class with accessor override.
        """
        class CustomPath(WindowsPath):

            def open(self, *args: Any, **kwargs: Any) -> Any:
                return cls.opener(*args, **kwargs)

            def listdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.list_files_and_directories(*args, **kwargs)

            def mkdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.create_directory(*args, **kwargs)

            def rmdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.delete(*args, **kwargs)

            def rename(self, *args: Any, **kwargs: Any) -> Any:
                return cls.rename(*args, **kwargs)

            def replace(self, *args: Any, **kwargs: Any) -> Any:
                return cls.replace(*args, **kwargs)

        return CustomPath(path)


class LinuxFileSystem(Storage):
    """
    Class that standardized methods of file systems for Linux Operational System.
    """

    temporary_folder: str = "/tmp/Handler"
    """
    Define the location of temporary content in filesystem.
    """
    file_sequence_style: tuple[Pattern[str], str] = (re.compile(r"(\ *-\ *\d+?)?(\.[^.]*$)"), r" - {sequence}\2")
    """
    Define the pattern to use to replace a sequence in the stylus of the filesystem.
    The first part identify the search and the second the replace value.
    This allow search by `<str>.<str>` and replace by `<str> - <int>.<str>`.
    """

    @classmethod
    def get_path_id(cls, path: str) -> str:
        """
        Method to get the file system id for a path.
        Path can be both a directory or file.
        """
        return str(os.stat(path, follow_symlinks=False).st_ino)

    @classmethod
    def get_created_date(cls, path: str) -> datetime:
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See https://stackoverflow.com/a/39501288/1709587 for explanation.
        Source: https://stackoverflow.com/a/39501288
        """
        stats = os.stat(path)
        try:
            time = stats.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            time = stats.st_mtime

        return datetime.fromtimestamp(time)

    @classmethod
    def get_pathlib_path(cls, path: str) -> Path:
        """
        Method to get the custom Path class with accessor override.
        """

        class CustomPath(PosixPath):

            def open(self, *args: Any, **kwargs: Any) -> Any:
                return cls.opener(*args, **kwargs)

            def listdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.list_files_and_directories(*args, **kwargs)

            def mkdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.create_directory(*args, **kwargs)

            def rmdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.delete(*args, **kwargs)

            def rename(self, *args: Any, **kwargs: Any) -> Any:
                return cls.rename(*args, **kwargs)

            def replace(self, *args: Any, **kwargs: Any) -> Any:
                return cls.replace(*args, **kwargs)

        return CustomPath(path)
