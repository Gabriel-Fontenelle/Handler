"""
File for classes that abstract methods of file and opertational systems.
This file can be accessed directly.
"""

# Python internals
from shutil import copyfile

from os import (
    makedirs,
    sep as os_sep, remove
)
from os.path import (
    exists,
    isdir,
    getsize,
    dirname
)
from io import open

# third-party
from shutil import rmtree
from send2trash import send2trash
from psutil import (
    disk_usage,
    virtual_memory,
    swap_memory
)

__all__ = [
    'FileSystem',
    'System',
]


class FileSystem:
    """
    Class that standardized methods of different file systems.
    """
    sep = os_sep

    @classmethod
    def is_dir(cls, path):
        """
        The default implementation uses os.path operations.
        Override this method if that’s not appropriate for your storage.
        """
        return isdir(path)

    @classmethod
    def is_file(cls, path):
        """
        The default implementation uses os.path operations.
         Override this method if that’s not appropriate for your storage.
        """
        return cls.is_dir(path)

    @classmethod
    def is_empty(cls, path):
        """
        The default implementation uses os.path operations.
        Override this method if that’s not appropriate for your storage.
        """
        return getsize(path) == 0

    @classmethod
    def create_directory(cls, directory_path):
        """
        Method to create directory in the file system.
        This method will try to create a directory only if it not exists already.
        """
        # Create Directory
        if not directory_path:
            raise ValueError("Is necessary the receive a folder name on create_directory method.")

        if not cls.exists(directory_path):
            makedirs(directory_path)
            return True

        return False

    @classmethod
    def create_file(cls, file_path):
        """
        Method to create a empty file.
        This method will try to create a file only if it not exists already.
        """
        # Check if file exists.
        if cls.exists(file_path):
            return False

        basedir = dirname(file_path)

        cls.create_directory(basedir)

        open(file_path, 'a').close()

        return True

    @classmethod
    def copy(cls, file_path_origin, file_path_destination, force=False):
        """
        Method used to copy a file from origin to destination.
        This method only try to copy if file exists.
        This method not check if there is a error and maybe can
        produce a OSError exception if not enough space in destination.

        This method will overwrite destination file if force is True.
        """
        if cls.exists(file_path_origin) and (not cls.exists(file_path_destination) or force):
            copyfile(file_path_origin, file_path_destination)
            return True

        return False

    @classmethod
    def move(cls, file_path_origin, file_path_destination, force=False):
        """
        Method used to move a file from origin to destination.
        This method do use copy_file to first copy the file and after send file to trash.
        The file only will be sent to trash if no exception was raised on copy.
        """
        if cls.copy(file_path_origin, file_path_destination, force):
            cls.delete(file_path_origin)
            return True

        return False

    @classmethod
    def delete(cls, path, force=False):
        """
        Method to delete a file or a whole directory.
        this method will delete permanently a file or directory
        specified in path if `force` is True. If `force` is False
        it will only send `path` to trash (It's more safe to send to trash).
        """
        if not cls.exists(path):
            return False

        if not force:
            send2trash(path)

        elif cls.is_file(path):
            remove(path)

        else:
            rmtree(path)

        return True

    @classmethod
    def exists(cls, path):
        """
        The default implementation uses os.path operations.
        Override this method if that’s not appropriate for your storage.
        """
        return exists(path)

    @classmethod
    def get_relative_path(cls, path, relative_to):
        """
        Method used to get relative path given two paths. The relative path is based on the path in based_on.
        relative_to = c/a/b/c/d/g/index.html
        path = c/a/b/e/i/file.c
        return = ../../../e/i/file.c

        path and relative_to must have its separator correct before being used.
        """
        
        # Fix directory without sep on end
        fix = relative_to.rpartition(cls.sep)
        if '.' not in fix[2]:
            relative_to += cls.sep

        base_length = len(relative_to)
        path_length = len(path)
        count = 0
        last_bar = 0

        length = path_length if base_length > path_length else base_length

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


class System:
    """
    Class that standardized methods of different storage and processing systems.
    """
    
    @classmethod
    def has_available_swap(cls, reversed_data=0):
        """
        Method to verify if there is swap memory available for reserved_data.
        The default implementation uses psutil operations.
        Override this method if that's not appropriate for your system.
        """
        data = virtual_memory()
        return data.available >= reversed_data

    @classmethod
    def has_available_memory(cls, reserved_data=0):
        """
        Method to verify if there is memory available for reserved_data.
        The default implementation uses psutil operations.
        Override this method if that's not appropriate for your system.
        """
        data = swap_memory()
        return data.free >= reserved_data

    @classmethod
    def has_available_disk(cls, drive, reserved_data=0):
        """
        Method to verify if there is available space in disk for reserved_data.
        The default implementation uses psutil operations.
        Override this method if that's not appropriate for your system.
        """
        data = disk_usage(drive)
        return data.free >= reserved_data
