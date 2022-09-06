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
`handler <at> gabrielfontenelle.com` can be used.
"""

__all__ = [
    'Extractor',
]


class Extractor:
    """
    Base class to be inherent to define class to be used on Extractor pipeline.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        This method must be override in child class.
        """
        raise NotImplementedError("Method extract must be overwritten on child class.")

    @classmethod
    def process(cls, **kwargs: dict):
        """
        Method used to run this class on Processor`s Pipeline for Extracting info from Data.
        This method and to_processor() is not need to extract info outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for renamer uses only one object that must be settled through first argument
        or through key work `object`.

        """
        object_to_process = kwargs.pop('object_to_process', None)
        overrider = kwargs.pop('overrider', False)

        try:
            cls.extract(file_object=object_to_process, overrider=overrider, **kwargs)
        except (ValueError, IOError) as e:
            if not hasattr(cls, 'errors'):
                setattr(cls, 'errors', [e])
            elif isinstance(cls.errors, list):
                cls.errors.append(e)

            return False

        return True
