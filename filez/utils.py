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

from importlib import import_module
from typing import Any

__all__ = ["LazyImportClass"]


class LazyImportClass:
    """
    Class to facilitate the lazy import of modules and attributes from modules.

    """
    def __init__(self, class_name: str, from_module: str | None = None) -> None:
        """
        Method to set up the information about the module that should be imported later.
        """
        self.class_name = class_name
        self.from_module = from_module
        self.imported_class = None

    def load_imported_class(self):
        """
        Method to import the module or attribute of the module.
        """
        if self.from_module:
            self.imported_class = getattr(import_module(self.from_module), self.class_name)
        else:
            self.imported_class = import_module(self.class_name)

    def __getattr__(self, value: str) -> Any:
        """
        Method to interface the attribute from the imported module or imported module`s attribute.
        It will evaluate the import in order to retrive its attribute.
        """
        if not self.imported_class:
            self.load_imported_class()

        return getattr(self.imported_class, value)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Method to interface a call from the imported module or imported module`s attribute.
        It will evaluate the import in order to retrive its attribute.
        """
        if not self.imported_class:
            self.load_imported_class()

        return self.imported_class(*args, **kwargs)
