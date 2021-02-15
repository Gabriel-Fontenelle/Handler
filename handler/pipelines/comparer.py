"""
Module with declaration of baseline class for the pipeline and its inherent class.
This module should only keep the pipeline class for comparing Files.
"""
from typing import Union

from handler.pipelines.__init__ import ProcessorMixin

__all__ = [
    'BinaryCompare',
    'DataCompare',
    'HashCompare',
    'LousyNameCompare',
    'MimeTypeCompare',
    'NameCompare',
    'SizeCompare',
]


class Comparer(ProcessorMixin):
    """
    Base class to be inherent to define classes for use on Comparer pipeline.
    """

    @classmethod
    def is_the_same(cls, file_1, file_2) -> Union[None, bool]:
        """
        Method used to check if two files are the same in memory using the File object.
        This method must be overwrite on child class to work correctly.
        """
        raise NotImplementedError("The method is_the_same needs to be overwrite on child class.")

    @classmethod
    def process(cls, *args, **kwargs) -> Union[None, bool]:
        """
        Method used to run this class on Processor`s Pipeline for Files.
        This method and to_processor() is not need to compare files outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for comparer uses only one list of objects that must be settled through first argument
        or through key work `objects`.

        This processor return boolean whether files are the same, different of others processors that return boolean
        to indicate that process was ran successfully.
        """
        objects_to_process = kwargs.pop('objects', args.pop(0))

        if not objects_to_process or len(objects_to_process) < 2:
            raise ValueError("There must be at least two objects to compare at `objects`s kwargs for "
                             "`Comparer.process`.")

        first = objects_to_process.pop(0)

        for element in objects_to_process:
            is_the_same = cls.is_the_same(first, element)
            if not is_the_same:
                # This can return None or False
                return is_the_same

        return True


class DataCompare(Comparer):
    """
    Class that define comparing of data between two Files for use in Comparer Pipeline.
    """

    @classmethod
    def is_the_same(cls, file_1, file_2) -> Union[None, bool]:
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

        # Don't compare empty content
        if not file_1.content and not file_2.content:
            return None

        # Set-up initial data for additional buffer
        buffer_1, buffer_2 = b'', b'' if file_1.is_binary else '', ''

        # Get buffer to verify
        buffer_size = min(file_1._block_size, file_2._block_size)

        value_1 = buffer_1
        value_2 = buffer_2

        while not (value_1 is None and value_2 is None):
            value_1 = next(file_1.content, None)
            value_2 = next(file_2.content, None)

            if value_1 is not None:
                # Add data to buffer
                buffer_1 += value_1

            if value_2 is not None:
                # Add data to buffer
                buffer_2 += value_2

            if len(buffer_1) >= buffer_size and len(buffer_2) >= buffer_size:
                try:
                    # Normalize buffer (after comparing above)
                    buffer_1, buffer_2 = compare_buffer()
                except StopIteration:
                    return False

        # If there is still buffer to verify, check buffer data
        while max(len(buffer_1), len(buffer_2)) >= buffer_size:
            try:
                # Normalize buffer (after comparing above)
                buffer_1, buffer_2 = compare_buffer()
            except StopIteration:
                return False

        return True


class SizeCompare(Comparer):
    """
    Class that define comparing of size of content between two Files for use in Comparer Pipeline.
    """

    @classmethod
    def is_the_same(cls, file_1, file_2) -> Union[None, bool]:
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

    @classmethod
    def is_the_same(cls, file_1, file_2) -> Union[None, bool]:
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

    @classmethod
    def is_the_same(cls, file_1, file_2) -> Union[None, bool]:
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

    @classmethod
    def is_the_same(cls, file_1, file_2) -> Union[None, bool]:
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

    @classmethod
    def is_the_same(cls, file_1, file_2) -> Union[None, bool]:
        """
        Method used to check if two files are the same.
        This method check the if mimetypes are the same.
        """
        if not file_1.mime_type or not file_2.mime_type:
            return None

        return file_1.mime_type == file_2.mime_type


class BinaryCompare(Comparer):
    """
    Class that define comparing of binary attribute between two Files for use in Comparer Pipeline.
    """

    @classmethod
    def is_the_same(cls, file_1, file_2) -> Union[None, bool]:
        """
        Method used to check if two files are the same.
        This method check the if attribute binary are the same.
        """
        return file_1.is_binary == file_2.is_binary
