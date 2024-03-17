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

from typing import Any

from ..exception import SerializerError

__all__ = [
    "FileOption"
]


class FileOption:
    """
    Class that store file settings to be used across package.
    """

    # Options related to saving a file
    allow_overwrite: bool = False
    """
    Variable to change the behavior of save method to allow overwrite of existing files on file system.
    """
    allow_override: bool = False
    """
    Variable to change the behavior of extraction methods used in pipeline to allow override of previous extract data.
    """
    allow_search_hashes: bool = True
    """
    Variable to change the behavior of generating and loading hashes from files to search CHECKSUM files.
    """
    allow_update: bool = True
    """
    Variable to change the behavior of save method to allow updating the content of the file on file system.
    """
    allow_rename: bool = True
    """
    Variable to change the behavior of save method to allow renaming to create a new filename if one already exists in 
    filesystem.
    """
    allow_extension_change: bool = True
    """
    Variable to change the behavior of save method to allow changing the extension when renaming a file.
    """
    create_backup: bool = True
    """
    Variable to change the behavior of save method to allow saving a file renaming the existing one to a backup instead 
     of overwriting it.
    """
    save_hashes: bool = True
    """
    Variable to change the behavior of save method to allow saving the generated hash files.
    """

    # Options related to running a pipeline
    pipeline_raises_exception = False
    """
    Variable to change the behavior of pipeline to not store the exception and raise it as it happen.
    Setting it to True can result some pipelines not fully working as expect (e.g Extractor and Compare pipelines).
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Method to create the current object using the keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

    @property
    def __serialize__(self) -> dict[str, Any]:
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """

        attributes = {
            "allow_overwrite",
            "allow_override",
            "allow_search_hashes",
            "allow_update",
            "allow_rename",
            "allow_extension_change",
            "create_backup",
            "save_hashes",
            "pipeline_raises_exception",
        }

        return {key: getattr(self, key) for key in attributes}
