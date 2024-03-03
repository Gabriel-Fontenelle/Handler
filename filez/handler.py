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
import re
from collections import namedtuple
from datetime import datetime
from filecmp import cmp
from glob import iglob
from shutil import copyfile
from sys import version_info

from os import (
    makedirs,
    popen,
    sep as os_sep, remove, fsync,
    stat
)
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
    'System',
    'URI'
]


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
    Path = namedtuple('RelativePath', ['directory', 'processed_uri'])
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
    def unparser_query(cls, value):
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
                value = value.replace(parsed_url.query, cls.unparser_query(queries))

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
