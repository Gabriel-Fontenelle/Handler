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

from typing import Any, TYPE_CHECKING

from ..exception import SerializerError, ReservedFilenameError, ImproperlyConfiguredFile

if TYPE_CHECKING:
    from . import BaseFile

__all__ = [
    "FileNaming"
]


class FileNaming:
    """
    Class that store file instance filenames and related names content.
    """

    reserved_filenames: dict[str, dict[str, BaseFile]] = {}
    """
    Dict of reserved filenames so that the correct file can be renamed
    avoiding overwriting a new file that has the same name as the current file in given directory.
    {<directory>: {<current_filename>: <base_file_object>}}
    """
    reserved_index: dict[str, dict[BaseFile, dict[str, BaseFile]]] = {}
    """
    Dict of reference of reserved filenames so that a filename can be easily removed from `reserved_filenames` dict.
    {<filename>: {<base_file_object>: <reference to reserved_index[filename][base_file_object]>}}}
    """

    history: list[tuple]
    history = None
    """
    Storage filenames to allow browsing old ones for current BaseFile.
    """
    on_conflict_rename: bool = False
    """
    Option that control behavior of renaming filename.  
    """
    related_file_object: BaseFile
    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes.
    """
    previous_saved_extension: str | None = None
    """
    Storage the previous saved extension to allow `save` method of file to verify if its changing its `extension`. 
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

        # We avoid storing information from `reserved_index` and `reserved_filenames` as those should reflect
        # the runtime and can be extensive.
        attributes = {
            "history",
            "on_conflict_rename",
            "related_file_object",
            "previous_saved_extension"
        }

        return {key: getattr(self, key) for key in attributes}

    def remove_reserved_filename(self, old_filename: str) -> None:
        """
        This method remove old filename from list of reserved filenames.
        """
        dictionary_of_files: dict[BaseFile, dict[str, BaseFile]] = self.reserved_index.get(old_filename, {})
        reference: dict[str, BaseFile] | None  = dictionary_of_files.get(self.related_file_object, None)

        # Remove from `reserved_filename` and current `reserved_index`.
        if reference:
            del reference[old_filename]
            del dictionary_of_files[self.related_file_object]

    def rename(self) -> None:
        """
        Method to rename `related_file_object` according to its own rename pipeline.
        TODO: Change how this method used `reserved_filenames` to allow moving or copying of file.
        TODO: Check if save_to exists before doing rename.
        """
        save_to: str | None = self.related_file_object.save_to
        complete_filename: str | None = self.related_file_object.complete_filename

        if save_to is None or not complete_filename:
            raise ImproperlyConfiguredFile("Renaming a file without a directory set at `save_to` and without a "
                                           "`complete_filename` is not supported.")

        reserved_folder: dict[str, BaseFile] = self.reserved_filenames.get(save_to, {})
        object_reserved: BaseFile | None = reserved_folder.get(complete_filename, None)

        # Check if filename already reserved name. Reserved names cannot be renamed even if overwrite is used in save,
        # so the only option is to have a new filename created, but only if `on_conflict_rename` is `True`.
        if reserved_folder and object_reserved and object_reserved is not self.related_file_object:
            if not self.on_conflict_rename:
                raise ReservedFilenameError(f"Rename cannot be made, because the filename {complete_filename} is "
                                            f"already reserved for object {object_reserved} and not for "
                                            f"{self.related_file_object}!")
            else:
                # Prepare reserved names to be set-up in `rename_pipeline`
                reserved_names: list[str] = [filename for filename in reserved_folder.keys()]

                # Generate new name based on file_system and reserved names calling the rename_pipeline.
                # The pipeline will update `complete_filename` of file to reflect new one. We shouldn`t change `path`
                # of file; `complete_filename` will add the new filename to `history` and remove the old one from
                # `reserved_filenames`.
                # Inform `path_attribute` and `reserved_names` to pipeline.
                self.related_file_object.rename_pipeline.run(
                    object_to_process=self.related_file_object,
                    **{
                        **self.related_file_object._get_kwargs_for_pipeline("rename_pipeline"),
                        "path_attribute": "save_to",
                        "reserved_names": reserved_names
                    })

                # Rename hash_files if there is any. This method not save the hash files giving the responsibility to
                # `save` method.
                self.related_file_object.hashes.rename(self.related_file_object.complete_filename)

        # Update reserved dictionary to reserve current filename.
        if not reserved_folder:
            self.reserved_filenames[save_to] = {complete_filename: self.related_file_object}
        elif not object_reserved:
            self.reserved_filenames[save_to][complete_filename] = self.related_file_object

        # Update reserved index to current filename. This allows for easy finding of filename and object at
        # `self.reserved_filenames`.
        if complete_filename not in self.reserved_index:
            # Pass reference of dict `save_to` to index of reserved names.
            self.reserved_index[complete_filename] = {self.related_file_object: self.reserved_filenames[save_to]}
        else:
            self.reserved_index[complete_filename][self.related_file_object] = self.reserved_filenames[save_to]

    def clean_history(self) -> None:
        """
        Method to clean the history of internal_files.
        The data will still be in memory while the Garbage Collector don't remove it.
        """
        self.history = []
