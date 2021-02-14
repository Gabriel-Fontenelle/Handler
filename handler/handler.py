"""
File for classes that abstract methods of file and operational systems.
This file can be accessed directly.
"""

# Python internals
import re
from collections import namedtuple
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
    basename,
    dirname,
    exists,
    getctime,
    getmtime,
    getsize,
    isdir,
    join, normpath, normcase,
)
from io import open

# third-party
from shutil import rmtree
from urllib.parse import urlparse, parse_qsl, unquote, urlencode

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
    folder_size_limit = 200
    path_size_limit = 254

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
    def open_file(cls, file_path, mode='rb'):
        """
        Method to return a buffer to a file. This method don't automatically closes file buffer.
        Override this method if that’s not appropriate for your storage.
        """
        return open(file_path, mode=mode)

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
        return basename(path)

    @classmethod
    def get_directory_from_path(cls, path):
        """
        Method used to get the path without filename from a complete path.
        """
        return dirname(path)

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

    @classmethod
    def read_lines(cls, path):
        """
        Method generator to get lines from file without loading all data in one step.
        """
        with open(path, 'r') as file:
            line = file.readline()
            if line:
                yield line

    @classmethod
    def sanitize_path(cls, path: str) -> str:
        """
        Method to normalize a path for use.
        This method collapse redundant separators and up-level references so that A//B, A/B/, A/./B and A/foo/../B
        all become A/B.
        """
        return normpath(path.replace('/', cls.sep))


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

    @classmethod
    def sanitize_path(cls, path: str) -> str:
        """
        Method to normalize a path for use.
        This method collapse redundant separators and up-level references so that A//B, A/B/, A/./B and A/foo/../B
        all become A/B. It will also convert uppercase character to lowecase and `/` to `\\`.
        """
        return normpath(normcase(path))


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


class URI:
    """
    Class that standardized methods of different URI handlers.
    """

    uri_scheme = re.compile(r'([A-Za-z0-9_-]*:\/\/)')
    """
    Define what is identifiable as scheme. The parentheses required to allow returning of
    capture string in `re.split()`.
    """
    uri_fragment = re.compile(r'#[^#\/\\]+$')
    """
    Define what is identifiable as fragment. 
    e.g. `https://test.com/path/#fragment` or `https://test.com/path/test.php#fragment`.
    """
    uri_separator = re.compile(r'\/|\\|\?[^=]+=|&[^=]+=|&amp;[^=]+=')
    """
    Define characters that separate values in URLs. 
    """
    cache = {}
    """
    Dictionary to cache paths and URIs to avoid calculating it again.
    """
    Path = namedtuple('Relative path', ['directory', 'processed_uri'])
    Filename = namedtuple('Filename', ['filename', 'processed_uri'])
    Cache = namedtuple('Cache', ['filename', 'directory'])

    @classmethod
    def remove_fragments(cls, value: str) -> str:
        """
        Method to remove a fragment from URL informed in value.
        This method expected that value is a URL unquoted.
        """
        return cls.uri_fragment.sub('', value)

    @classmethod
    def parse_query(cls, value: str) -> list:
        """
        Method to parse a query from a URI returning a list of tuples (pairs of key, value).
        """
        return parse_qsl(value)

    @classmethod
    def unparse_query(cls, value):
        """
        Method to undo a parse resulted from using `cls.parse_query`.
        """
        return unquote(urlencode(value))

    @classmethod
    def parse_url(cls, value) -> object:
        """
        Method to parse an URI in a object with the following attributes:
        - scheme
        - netloc
        - path
        - params
        - query
        - fragment

        If overwritten, the return of this method should be an object with the attributes above.
        """
        return urlparse(value)

    @classmethod
    def process_path(cls, value, file_system):
        """
        This method caches the processed value to allow for dynamic programming.
        """
        search = ['filename', 'file_name', 'file']
        parsed_url = cls.parse_url(value)
        filename = None

        # Remove filename, file_name or file from URI query
        if any(x in parsed_url.query for x in search):
            queries = cls.parse_query(parsed_url.query)

            filename_index = None

            for index, item in enumerate(queries):
                if item[0] in search:
                    filename_index = index
                    break

            if filename_index:
                filename = queries.pop(filename_index)

                # Remove filename index from from url
                value = value.replace(parsed_url.query, cls.unparse_query(queries))

        # Remove separator from URI converting it to path
        path = cls.uri_separator.sub(file_system.sep, value)

        # Remove filename if there is any (Filename are defined with . in its name)
        if not filename:
            possible_filename = file_system.get_filename_from_path(path)

            if '.' in possible_filename:
                filename = possible_filename
                path = file_system.get_directory_from_path(path)

        # Sanitize path
        directory = file_system.sanitize_path(path)

        # Save in cache
        cls.cache[value] = cls.Cache(
            directory=directory,
            filename=filename
        )

    @classmethod
    def get_processed_uri(cls, value):
        """
        Method to return from cache the processed URI dictionary.
        """
        return cls.cache.get(value, None) if cls.cache else None

    @classmethod
    def get_paths(cls, value, file_system) -> list:
        """
        Method to return a list of paths found in URI.
        This method convert the URI to path keeping filename if there is any.
        This method uses dynamic programming to not process a already seeing URI.
        The return as this method when a path is found is a list of objects containing
        the following attributes:
        - directory (directory generate from url)
        - processed_uri (url registered at cache)
        """
        paths = []

        for uri in cls.separate_uris(value):
            # Remove fragments from URI
            processed_uri = cls.remove_fragments(uri)

            # Remove scheme from URI
            processed_uri = cls.uri_scheme.sub('', processed_uri)

            if processed_uri not in cls.cache:
                cls.process_path(processed_uri, file_system)

            paths.append(cls.Path(cls.cache[processed_uri].directory, processed_uri))

        return paths

    @classmethod
    def get_filenames(cls, value, file_system) -> list:
        """
        Method to return a list of filenames found in URI.
        This method try to find a filename in path if there is any.
        This method uses dynamic programming to not process a already seeing URI.
        The return as this method when a path is found is a list of objects containing
        the following attributes:
        - filename (filename generate from url)
        - processed_uri (url registered at cache)
        """
        filenames = []

        for uri in cls.separate_uris(value):
            # Remove fragments from URI
            processed_uri = cls.remove_fragments(uri)

            # Remove scheme from URI
            processed_uri = cls.uri_scheme.sub('', processed_uri)

            if processed_uri not in cls.cache:
                cls.process_path(processed_uri, file_system)

            if cls.cache[processed_uri].filename:
                filenames.append(cls.Path(cls.cache[processed_uri].filename, processed_uri))

        return filenames

    @classmethod
    def separate_uris(cls, value: str) -> list:
        """
        Method to return list of URI separated by scheme.
        What define scheme in this method is a word (a-z,A-Z,0-9,_,-) followed by `://`.
        """
        possible_uris = list(reversed(cls.uri_scheme.split(value)))

        return [
            element[index + 1] + element
            for index, element in enumerate(possible_uris)
            if element and ':' not in element
        ]
