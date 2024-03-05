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
from typing import Any

from ..exception import SerializerError

__all__ = [
    "FileState"
]


class FileState:
    """
    Class that store file instance state.
    """

    adding: bool = True
    """
    Indicate whether an object was already saved or not. If true, we will consider this a new, unsaved
    object in the current file`s filesystem.
    """
    renaming: bool = False
    """
    Indicate whether an object is schedule to being renamed in the current file`s filesystem.
    """
    changing: bool = False
    """
    Indicate whether an object has changed or not. If true, we will consider that the current content was
    changed but not saved yet.  
    """
    processing: bool = True
    """
    Indicate whether an object has already run its pipeline of extraction or not. If true, we will consider 
    this a new object that needs to be process its pipeline.
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
    def __serialize__(self) -> dict[str, bool]:
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes: set = {"adding", "renaming", "changing", "processing"}

        return {key: getattr(self, key) for key in attributes}
