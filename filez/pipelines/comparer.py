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

if TYPE_CHECKING:
    from ..file import BaseFile


__all__ = [
    'Comparer',
    'BinaryCompare',
    'DataCompare',
    'HashCompare',
    'LousyNameCompare',
    'MimeTypeCompare',
    'NameCompare',
    'SizeCompare',
    'TypeCompare'
]


class Comparer:
    """
    Base class to be inherent to define classes for use on Comparer pipeline.
    """

    stopper: bool = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> None | bool:
        """
        Method used to check if two files are the same in memory using the File object.
        This method must be overwrite on child class to work correctly.
        """
        raise NotImplementedError("The method is_the_same needs to be overwrite on child class.")

    @classmethod
    def process(cls, **kwargs: Any) -> None | bool:
        """
        Method used to run this class on Processor`s Pipeline for Files.
        This method and to_processor() is not need to compare files outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for comparer uses only one list of objects that must be settled through first argument
        or through key work `objects`.

        This processor return boolean whether files are the same, different of others processors that return boolean
        to indicate that process was ran successfully.
        """
        object_to_process: BaseFile = kwargs.pop('object_to_process')
        objects_to_compare: list | tuple = kwargs.pop('objects_to_compare')

        if not objects_to_compare or not isinstance(objects_to_compare, (list, tuple)):
            raise ValueError("There must be at least one object to compare at `objects_to_compare`s kwargs for "
                             "`Comparer.process`.")

        for element in objects_to_compare:
            is_the_same = cls.is_the_same(object_to_process, element)
            if not is_the_same:
                # This can return None or False
                return is_the_same

        return True


class DataCompare(Comparer):
    """
    Class that define comparing of data between two Files for use in Comparer Pipeline.
    """

    stop_value: tuple[bool, bool] = (True, False)
    """
    Variable that define if this class used as processor should stop the pipeline when resulting in stop_value`s values.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> bool | None:
        """
        Method used to check if two files are the same.
        This method check byte by byte.
        This method assumes that data has the same size and both has the same value
        to is_binary, thus use it after SizeCompare and BinaryCompare.

        Because the content buffers can have difference in sizes, we should make use
        of a additional buffer to save parts of content to compare. Using the lower size of buffer
        between the two files.
        """
        def compare_buffer():
            """
            Internal function to compare two buffer's data.
            This function will compare the buffer extracting from it the content of same size, usually
            the lowest buffer size between those buffers.
            """
            # Compare same size buffer
            if buffer_1[:buffer_size] != buffer_2[:buffer_size]:
                raise StopIteration()

            # Normalize buffer returning modified buffer (after comparing above)
            return buffer_1[buffer_size:], buffer_2[buffer_size:]

        try:
            # Check if there is a content so we don't compare empty content. It is checked by property content of
            # BaseFile when calling .content
            content_1 = file_1.content_as_iterator
            content_2 = file_2.content_as_iterator

            # Comparing data between binary and string should return False, they are not the same anyway.
            if file_1.is_binary != file_2.is_binary:
                return False

            # Set-up initial data for additional buffer
            value_1: str | bytes | None
            value_2: str | bytes | None
            buffer_1: str | bytes | None
            buffer_2: str | bytes | None

            if file_1.is_binary:
                value_1 = buffer_1 = b''
                value_2 = buffer_2 = b''
            else:
                value_1 = buffer_1 = ''
                value_2 = buffer_2 = ''

            # Normalize buffer size to be the minimum denominator between buffers
            buffer_size = min(file_1._content._block_size, file_2._content._block_size)

        except ValueError:
            return None

        try:
            # Loop through content adding to new buffer to allow comparison between normalized sizes.
            while not (value_1 is None and value_2 is None):
                # We should avoid raising StopIteration so we define a default value to return instead.
                value_1 = next(content_1, None)
                value_2 = next(content_2, None)

                if value_1 is not None:
                    # Add data to buffer
                    buffer_1 += value_1

                if value_2 is not None:
                    # Add data to buffer
                    buffer_2 += value_2

                if len(buffer_1) >= buffer_size and len(buffer_2) >= buffer_size:
                    # Normalize buffer (after comparing above)
                    # compare_buffer will raise StopIterator case the comparison is False.
                    buffer_1, buffer_2 = compare_buffer()

            # If there is still buffer to verify, check buffer data
            while max(len(buffer_1), len(buffer_2)) >= buffer_size:
                # Normalize buffer (after comparing above)
                # compare_buffer will raise StopIterator case the comparison is False.
                buffer_1, buffer_2 = compare_buffer()

            return True

        except StopIteration:
            # Case StopIteration as raised the comparison is false.
            return False


class SizeCompare(Comparer):
    """
    Class that define comparing of size of content between two Files for use in Comparer Pipeline.
    """

    stop_value: bool = False
    """
    Variable that define if this class used as processor should stop the pipeline when resulting in stop_value`s values.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> bool | None:
        """
        Method used to check if two files are the same.
        This method check the if sizes are the same.
        """
        if not len(file_1) or not len(file_2):
            return None

        return len(file_1) == len(file_2)


class HashCompare(Comparer):
    """
    Class that define comparing of hash between two Files for use in Comparer Pipeline.
    """

    stop_value: tuple[bool, bool] = (True, False)
    """
    Variable that define if this class used as processor should stop the pipeline when resulting in stop_value`s values.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> bool | None:
        """
        Method used to check if two files are the same.
        This method check the if hashes are the same.
        """
        if not file_1.hashes or not file_2.hashes:
            return None

        for hash_name in set(file_1.hashes.keys()).intersection(set(file_2.hashes.keys())):
            if file_1.hashes[hash_name] != file_2.hashes[hash_name]:
                return False

        return True


class LousyNameCompare(Comparer):
    """
    Class that define comparing of filename between two Files for use in Comparer Pipeline.
    """

    stop_value: bool = False
    """
    Variable that define if this class used as processor should stop the pipeline when resulting in stop_value`s values.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> bool | None:
        """
        Method used to check if two files are the same.
        This method check the if the names are lousily the same.
        """
        if not file_1.filename or not file_2.filename:
            return None

        # Compare filenames and extension, but we assume that being the same mime_type it can have different
        # extension if those are valid and registered
        # to mime type.
        extension = True
        if file_1.extension and file_2.extension:
            extension = file_1.mime_type_handler.get_mimetype(
                file_1.extension
            ) == file_2.mime_type_handler.get_mimetype(file_2.extension)

        return file_1.complete_filename == file_2.complete_filename and extension


class NameCompare(Comparer):
    """
    Class that define comparing of filename between two Files for use in Comparer Pipeline.
    """

    stop_value: bool = False
    """
    Variable that define if this class used as processor should stop the pipeline when resulting in stop_value`s values.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> bool | None:
        """
        Method used to check if two files are the same.
        This method check the if complete filename are the same.
        """
        if not file_1.filename or not file_2.filename:
            return None

        return file_1.complete_filename == file_2.complete_filename


class MimeTypeCompare(Comparer):
    """
    Class that define comparing of mimetype between two Files for use in Comparer Pipeline.
    """

    stop_value: bool = False
    """
    Variable that define if this class used as processor should stop the pipeline when resulting in stop_value`s values.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> bool | None:
        """
        Method used to check if two files are the same.
        This method check the if mimetypes are the same.
        """
        if file_1.mime_type is None or file_2.mime_type is None:
            return None

        return file_1.mime_type == file_2.mime_type


class BinaryCompare(Comparer):
    """
    Class that define comparing of binary attribute between two Files for use in Comparer Pipeline.
    """

    stop_value: bool = False
    """
    Variable that define if this class used as processor should stop the pipeline when resulting in stop_value`s values.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> bool | None:
        """
        Method used to check if two files are the same.
        This method check the if attribute binary are the same.
        """
        file_1_is_binary = file_1.is_binary
        file_2_is_binary = file_2.is_binary

        if file_1_is_binary is None or file_2_is_binary is None:
            return None

        return file_1_is_binary == file_2_is_binary


class TypeCompare(Comparer):
    """
    Class that define comparing of type between two Files for use in Comparer Pipeline.
    """

    stop_value: bool = False
    """
    Variable that define if this class used as processor should stop the pipeline when resulting in stop_value`s values.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> bool | None:
        """
        Method used to check if two files are the same.
        This method check the if attribute binary are the same.
        """
        if file_1.type is None or file_2.type is None:
            return None

        return file_1.type == file_2.type
