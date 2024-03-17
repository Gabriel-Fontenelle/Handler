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

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...file import BaseFile

__all__ = [
    'Extractor',
]


class Extractor:
    """
    Base class to be inherent to define class to be used on Extractor pipeline.
    """

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> None | bool:
        """
        Method to extract the information necessary from a file_object.
        This method must be override in child class.
        """
        raise NotImplementedError("Method extract must be overwritten on child class.")

    @classmethod
    def process(cls, **kwargs: Any) -> bool:
        """
        Method used to run this class on Processor`s Pipeline for Extracting info from Data.
        This method and to_processor() is not need to extract info outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        This method can throw ValueError and IOError when trying to extract data from content.
        The `Pipeline.run` method will catch those errors.
        """
        object_to_process: BaseFile = kwargs.pop('object_to_process')
        # Pipeline argument has priority for overrider configuration.
        overrider: bool = kwargs.pop('overrider', object_to_process._option.allow_override)

        cls.extract(file_object=object_to_process, overrider=overrider, **kwargs)

        return True
