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

__all__ = [
    "CacheDescriptor",
    "LoadedDescriptor",
    "InternalFilesDescriptor",
]


class CacheDescriptor:
    """
    Descriptor class to storage data for instance`s cache.
    This class is used for FileHashes._cache.
    """

    def __get__(self, instance, owner):
        """
        Method `get` to automatically set-up empty values in an instance.
        """
        if instance is None:
            return self

        res = instance.__dict__['_cache'] = {}
        return res


class LoadedDescriptor:
    """
    Descriptor class to storage data for instance`s loaded.
    This class is used for FileHashes._loaded.
    """

    def __get__(self, instance, owner):
        """
        Method `get` to automatically set-up empty values in an instance.
        """
        if instance is None:
            return self

        res = instance.__dict__['_loaded'] = []
        return res


class InternalFilesDescriptor:
    """
    Descriptor class to storage data for instance`s internal files' dictionary.
    This class is used for FileHashes._loaded.
    """

    def __get__(self, instance, owner):
        """
        Method `get` to automatically set-up empty values in an instance.
        """
        if instance is None:
            return self

        res = instance.__dict__['_internal_files'] = {}
        return res
