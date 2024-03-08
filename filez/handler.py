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

# Python internals
import re
from collections import namedtuple
from typing import Type, TYPE_CHECKING, NamedTuple, Pattern
# third-party
from urllib.parse import urlparse, parse_qsl, unquote, urlencode

from psutil import (
    disk_usage,
    virtual_memory,
    swap_memory
)

if TYPE_CHECKING:
    from .storage import Storage
    from urllib.parse import ParseResult


__all__ = [
    'System',
    'URI'
]


class System:
    """
    Class that standardized methods of different storage and processing systems.
    """
    
    @classmethod
    def has_available_swap(cls, reversed_data: int = 0) -> bool:
        """
        Method to verify if there is swap memory available for reserved_data.
        The default implementation uses psutil operations.
        Override this method if that's not appropriate for your system.
        """
        data = virtual_memory()
        return data.available >= reversed_data

    @classmethod
    def has_available_memory(cls, reserved_data: int = 0) -> bool:
        """
        Method to verify if there is memory available for reserved_data.
        The default implementation uses psutil operations.
        Override this method if that's not appropriate for your system.
        """
        data = swap_memory()
        return data.free >= reserved_data

    @classmethod
    def has_available_disk(cls, drive: str, reserved_data: int = 0) -> bool:
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

    uri_scheme: Pattern = re.compile(r'([A-Za-z0-9_-]*:\/\/)')
    """
    Define what is identifiable as scheme. The parentheses required to allow returning of
    capture string in `re.split()`.
    """
    uri_fragment: Pattern = re.compile(r'#[^#\/\\]+$')
    """
    Define what is identifiable as fragment. 
    e.g. `https://test.com/path/#fragment` or `https://test.com/path/test.php#fragment`.
    """
    uri_separator: Pattern = re.compile(r'\/|\\|\?[^=]+=|&[^=]+=|&amp;[^=]+=')
    """
    Define characters that separate values in URLs. 
    """
    cache: dict = {}
    """
    Dictionary to cache paths and URIs to avoid calculating it again.
    """
    Path: NamedTuple = namedtuple('Path', ['directory', 'processed_uri'])
    Filename: NamedTuple = namedtuple('Filename', ['filename', 'processed_uri'])
    Cache: NamedTuple = namedtuple('Cache', ['filename', 'directory'])

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
    def unparser_query(cls, value: list) -> str:
        """
        Method to undo a parse resulted from using `cls.parse_query`.
        """
        return unquote(urlencode(value))

    @classmethod
    def parse_url(cls, value: str) -> ParseResult:
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
    def process_path(cls, value: str, file_system: Type[Storage]) -> None:
        """
        This method caches the processed value to allow for dynamic programming.
        """
        search: set[str] = {'filename', 'file_name', 'file'}
        parsed_url: ParseResult = cls.parse_url(value)

        filename: str | None = None

        # Remove filename, file_name or file from URI query
        if any(x in parsed_url.query for x in search):
            queries = cls.parse_query(parsed_url.query)

            filename_index: int | None = None

            for index, item in enumerate(queries):
                if item[0] in search:
                    filename_index = index
                    break

            if filename_index:
                filename = queries.pop(filename_index)

                # Remove filename index from from url
                value = value.replace(parsed_url.query, cls.unparser_query(queries))

        # Remove separator from URI converting it to path
        path: str = cls.uri_separator.sub(file_system.sep, value)

        # Remove filename if there is any (Filename are defined with . in its name)
        if not filename:
            possible_filename: str = file_system.get_filename_from_path(path)

            if '.' in possible_filename:
                filename = possible_filename
                path = file_system.get_directory_from_path(path)

        # Sanitize path
        directory: str = file_system.sanitize_path(path)

        # Save in cache
        cls.cache[value] = cls.Cache(
            directory=directory,
            filename=filename
        )

    @classmethod
    def get_processed_uri(cls, value: str) -> Cache | None:
        """
        Method to return from cache the processed URI dictionary.
        """
        return cls.cache.get(value, None)

    @classmethod
    def get_paths(cls, value: str, file_system: Type[Storage]) -> list[URI.Path]:
        """
        Method to return a list of paths found in URI.
        This method convert the URI to path keeping filename if there is any.
        This method uses dynamic programming to not process a already seeing URI.
        The return as this method when a path is found is a list of objects containing
        the following attributes:
        - directory (directory generate from url)
        - processed_uri (url registered at cache)
        """
        paths: list[URI.Path] = []

        for uri in cls.separate_uris(value):
            # Remove fragments from URI
            processed_uri: str = cls.remove_fragments(uri)

            # Remove scheme from URI
            processed_uri = cls.uri_scheme.sub('', processed_uri)

            if processed_uri not in cls.cache:
                cls.process_path(processed_uri, file_system)

            paths.append(cls.Path(cls.cache[processed_uri].directory, processed_uri))

        return paths

    @classmethod
    def get_filenames(cls, value: str, file_system: Type[Storage]) -> list[URI.Filename]:
        """
        Method to return a list of filenames found in URI.
        This method try to find a filename in path if there is any.
        This method uses dynamic programming to not process a already seeing URI.
        The return as this method when a path is found is a list of objects containing
        the following attributes:
        - filename (filename generate from url)
        - processed_uri (url registered at cache)
        """
        filenames: list[URI.Filename] = []

        for uri in cls.separate_uris(value):
            # Remove fragments and scheme from URI
            processed_uri: str = cls.uri_scheme.sub('', cls.remove_fragments(uri))

            if processed_uri not in cls.cache:
                cls.process_path(processed_uri, file_system)

            if cls.cache[processed_uri].filename:
                filenames.append(cls.Filename(cls.cache[processed_uri].filename, processed_uri))

        return filenames

    @classmethod
    def separate_uris(cls, value: str) -> list[str]:
        """
        Method to return list of URI separated by scheme.
        What define scheme in this method is a word (a-z,A-Z,0-9,_,-) followed by `://`.
        """
        possible_uris: list = list(reversed(cls.uri_scheme.split(value)))

        return [
            element[index + 1] + element
            for index, element in enumerate(possible_uris)
            if element and ':' not in element
        ]
