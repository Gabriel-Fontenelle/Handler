"""
File for classes that abstract methods of file and opertational systems.
This file can be accessed directly.
"""

# Python internals
from datetime import datetime
from filecmp import cmp
from shutil import copyfile

from os import (
    makedirs,
    popen,
    sep as os_sep, remove, fsync,
    stat
)
from os.path import (
    exists,
    isdir,
    getsize,
    dirname, getmtime, getctime, join
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
    'WindowsFileSystem',
    'LinuxFileSystem',
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
        Override this method if that’s not appropriate for your storage.
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
        Override this method if that’s not appropriate for your storage.
        """
        # Check if file exists.
        if cls.exists(file_path):
            return False

        basedir = dirname(file_path)

        cls.create_directory(basedir)

        open(file_path, 'a').close()

        return True

    @classmethod
    def save_file(cls, file_path, content, **kwargs):
        """
        Method to save content on file.
        This method will throw a exception if content is not iterable.
        Override this method if that’s not appropriate for your storage.
        """
        content = iter(content)

        if 'file_mode' not in kwargs:
            kwargs['file_mode'] = 'a'

        if 'write_mode' not in kwargs:
            kwargs['write_mode'] = 'b'

        with open(file_path, kwargs['file_mode'] + kwargs['write_mode']) as file_pointer:
            for chunk in content:
                file_pointer.write(chunk)
                file_pointer.flush()
                fsync(file_pointer.fileno())

    @classmethod
    def copy(cls, file_path_origin, file_path_destination, force=False):
        """
        Method used to copy a file from origin to destination.
        This method only try to copy if file exists.
        This method not check if there is a error and maybe can
        produce a OSError exception if not enough space in destination.

        This method will overwrite destination file if force is True.
        Override this method if that’s not appropriate for your storage.
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
        Override this method if that’s not appropriate for your storage.
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
        Override this method if that’s not appropriate for your storage.
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
    def cmp(cls, file_path_1, file_path_2):
        """
        Method used to compare file from file_path informed.
        Override this method if that’s not appropriate for your storage.
        """
        # Compare data from pointers and not stats.

        return cmp(file_path_1, file_path_2, False)

    @classmethod
    def join(cls, *paths):
        """
        Method used to concatenate two or more paths.
        Override this method if that’s not appropriate for your storage.
        """
        return join(*paths)

    @classmethod
    def get_filename_from_path(cls, path):
        """
        Method used to get the filename from a complete path.
        """
        return path.basename(path)

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

    @classmethod
    def get_size(cls, path):
        """
        Method to get the size of file at path in bytes.
        """
        return getsize(path)

    @classmethod
    def get_modified_date(cls, path):
        """
        Method to get the modified time as datetime converted from float.
        """
        return datetime.fromtimestamp(getmtime(path))

    @classmethod
    def get_created_date(cls, path):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        This method should be overwritten in child specific for Operational System.
        """
        raise NotImplementedError("Method get_created_date(path) should be accessed through inherent class.")

    @classmethod
    def get_path_id(cls, path):
        """
        Method to get the file system id for path.
        This method should be overwritten in child specific for Operational System.
        """
        raise NotImplementedError("Method get_path_id(path) should be accessed through inherent class.")


class WindowsFileSystem(FileSystem):
    """
    Class that standardized methods of file systems for Windows Operational System.
    """

    @classmethod
    def get_path_id(cls, path):
        """
        Method to get the file system id for a path.
        Path can be both a directory or file.
        """
        # TODO: Conclude function after testing on Windows.
        file = r"C:\Users\Grandmaster\Desktop\testing.py"
        output = popen(fr"fsutil file queryfileid {file}").read()

    @classmethod
    def get_created_date(cls, path):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See http://stackoverflow.com/a/39501288/1709587 for explanation.
        Source: https://stackoverflow.com/a/39501288
        """
        time = getctime(path)

        return datetime.fromtimestamp(time)


class LinuxFileSystem(FileSystem):
    """
    Class that standardized methods of file systems for Linux Operational System.
    """

    @classmethod
    def get_path_id(cls, path):
        """
        Method to get the file system id for a path.
        Path can be both a directory or file.
        """
        return stat(path, follow_symlinks=False).st_ino

    @classmethod
    def get_created_date(cls, path):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See http://stackoverflow.com/a/39501288/1709587 for explanation.
        Source: https://stackoverflow.com/a/39501288
        """
        stats = stat(path)
        try:
            time = stats.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            time = stats.st_mtime

        return datetime.fromtimestamp(time)


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
