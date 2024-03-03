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
from ..exception import SerializerError

__all__ = [
    "FileMetadata"
]


class FileMetadata:
    """
    Class that store file instance metadata.
    """

    packed = False
    """
    Indicate whether an object was packed in a container or not. As example: .rar, .epub, .tar. 
    """
    compressed = False
    """
    Indicate whether an object was compressed or not. Different from packed, an object can the packed and not 
    compressed or it could be both packed and compressed.
    """
    lossless = False
    """
    Indicate whether an object was lossless compressed or not. 
    """
    hashable = True
    """
    Indicate whether an object can have its hash saved or not. Internal packed files cannot have hash saved to file, 
    it can be generate just not saved in the package.
    """
    internal = False
    """
    Indicate whether an object is a file from a packed container or not.
    """

    # Hasher files
    # loaded = None
    """
    Indicate whether an object is a hash file loaded from a file or not.
    This is mostly used for hash files created with hasher and will be set up only in those files.
    """
    # checksum = None
    """
    Indicate whether an object is a hash file named CHECKSUM.hasher_name file (contains multiple files) or not.
    This is mostly used for hash files created with hasher and will be set up only in those files.
    """

    # Thumbnail files
    # preview = None
    """
    Indicate whether an object is a preview file or not.
    This is mostly used for animated thumbnail created with render and will be set up only in those files.
    """
    # thumbnail = None
    """
    Indicate whether an object is a thumbnail file or not.
    This is mostly used for thumbnail created with render and will be set up only in those files.
    """

    def __init__(self, **kwargs):
        """
        Method to create the current object using the keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key) or key in {"checksum", "loaded", "thumbnail"}:
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

    @property
    def __serialize__(self):
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """

        attributes = {
            "packed",
            "compressed",
            "lossless",
            "hashable"
        }
        optional_attributes = {
            "checksum",
            "loaded",
            "preview",
            "thumbnail",
        }

        class_vars = {key: getattr(self, key) for key in attributes}

        for attribute in optional_attributes:
            if hasattr(self, attribute):
                class_vars[attribute] = getattr(self, attribute)

        return class_vars
