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
    'FileActions',
]


class FileActions:
    """
    Class that store file instance actions to be performed.
    """

    save: bool = False
    """
    Indicate whether an object should be saved or not.
    """
    extract: bool = False
    """
    Indicate whether an object should be extracted or not.
    File inside another file should be extract and not saved.
    """
    rename: bool = False
    """
    Indicate whether an object should be renamed or not.
    """
    hash: bool = False
    """
    Indicate whether an object should be hashed or not.
    """
    list: bool = False
    """
    Indicate whether an object should have its internal content listed or not.
    """
    preview: bool = False
    """
    Indicate whether an object should have its preview image processed.
    """
    thumbnail: bool = False
    """
    Indicate whether an object should have its thumbnail image processed.
    """

    was_saved: bool = False
    """
    Indicate whether an object was successfully saved.
    """
    was_extracted: bool = False
    """
    Indicate whether an object was successfully extracted.
    """
    was_renamed: bool = False
    """
    Indicate whether an object was successfully renamed.
    """
    was_hashed: bool = False
    """
    Indicate whether an object was successfully hashed.
    """
    was_listed: bool = False
    """
    Indicate whether an object was its internal content listed.
    """
    was_previewed: bool = False
    """
    Indicate whether an object has successfully generate its preview image.
    """
    was_thumbnailed: bool = False
    """
    Indicate whether an object has successfully generate its thumbnail image.
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
        attributes: set[str] = {
            "extract",
            "hash",
            "rename",
            "save",
            "was_extracted",
            "was_hashed",
            "was_renamed",
            "was_saved",
        }

        return {key: getattr(self, key) for key in attributes}

    def to_extract(self) -> None:
        """
        Method to set up the action of save file.
        """
        self.extract = True
        self.was_extracted = False

    def extracted(self) -> None:
        """
        Method to change the status of `to extract` to `extracted` file.
        """
        self.extract = False
        self.was_extracted = True

    def to_save(self) -> None:
        """
        Method to set up the action of save file.
        """
        self.save = True
        self.was_saved = False

    def saved(self) -> None:
        """
        Method to change the status of `to save` to `saved` file.
        """
        self.save = False
        self.was_saved = True

    def to_rename(self) -> None:
        """
        Method to set up the action of rename file.
        """
        self.rename = True
        self.was_renamed = False

    def renamed(self) -> None:
        """
        Method to change the status of `to rename` to `renamed` file.
        """
        self.rename = False
        self.was_renamed = True

    def to_hash(self) -> None:
        """
        Method to set up the action of generate hash for file.
        """
        self.hash = True
        self.was_hashed = False

    def hashed(self) -> None:
        """
        Method to change the status of `to hash` to `hashed` file.
        """
        self.hash = False
        self.was_hashed = True

    def to_list(self) -> None:
        """
        Method to set up the action of generate hash for file.
        """
        self.list = True
        self.was_listed = False

    def listed(self) -> None:
        """
        Method to change the status of `to hash` to `hashed` file.
        """
        self.list = False
        self.was_listed = True

    def to_preview(self) -> None:
        """
        Method to set up the action of generate preview image for file.
        """
        self.preview = True
        self.was_previewed = False

    def previewed(self) -> None:
        """
        Method to change the satus of `to preview` to `previewed` file.
        """
        self.preview = False
        self.was_previewed = True

    def to_thumbnail(self) -> None:
        """
        Method to set up the action of generate thumbnail image for file.
        """
        self.thumbnail = True
        self.was_thumbnailed = False

    def thumbnailed(self) -> None:
        """
        Method to change the satus of `to thumbnail` to `thumbnailed` file.
        """
        self.thumbnail = False
        self.was_thumbnailed = True
