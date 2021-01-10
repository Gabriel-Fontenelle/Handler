"""
Module with declaration of baseline class for the pipeline and its inherent class.
This module should only keep the pipeline class for renaming Files.
"""
# Python internals
import re
from uuid import uuid4

# core modules
from handler.pipelines import ProcessorMixin

# modules
from handler.handler import FileSystem

__all__ = [
    'Renamer',
    'WindowsRenamer',
    'LinuxRenamer',
    'UniqueRenamer'
]


class Renamer(ProcessorMixin):
    """
    Base class to be inherent to define class to be used on Renamer pipeline.
    """

    file_system_handler = FileSystem
    enumeration_pattern = None
    
    @classmethod
    def prepare_filename(cls, filename, extension=None):
        """
        Method to separated extension from filename if extension
        not informed and save on class.
        """
        # Remove extension from filename if it was given
        if extension and filename[-len(extension):] == extension:
            filename = filename[:-len(f".{extension}")]

        return filename, extension

    @classmethod
    def get_name(cls, directory_path, filename, extension):
        """
        Method to get the new generated name.
        This class should raise BlockingIOError when a custom error should happen that will be
        caught by `process` when using Pipeline.
        """
        raise NotImplementedError("Method get_name must be overwrite on child class.")

    @classmethod
    def process(cls, *args, **kwargs):
        """
        Method used to run this class on Processor`s Pipeline for Files.
        This method and to_processor() is not need to rename files outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for renamer uses only one object that must be settled through first argument
        or through key work object.

        FUTURE CONSIDERATION: Making the pipeline multi thread or multi process only will required that
        a lock be put between usage of get_name.
        FUTURE CONSIDERATION: Multi thread will need to consider that the attribute `file_system_handler`
        is shared between the reference of the class and all object of it and will have to be change the
        code (multi process don't have this problem).
        """
        object_to_process = kwargs.pop('object', args.pop(0))

        # Prepare filename from File's object
        filename, extension = cls.prepare_filename(object_to_process.filename, object_to_process.extension)

        # Save current file system handler
        class_file_system_handler = cls.file_system_handler

        # Get new name
        # When is not possible to get new name by some problem either with file or filesystem
        # is expected BlockingIOError
        try:
            # Overwrite File System attribute with File System of File only when running in pipeline.
            # This will alter the File System for the class, any other call to this class will use the altered
            # file system.
            cls.file_system_handler = object_to_process.file_system_handler

            # Get directory from object to be processed.
            path = cls.file_system_handler.sanitize_path(object_to_process.path)

            new_filename, extension = cls.get_name(path, filename, extension)

            # Restore File System attribute to original.
            cls.file_system_handler = class_file_system_handler
        except BlockingIOError:
            return False

        # Set new name at File's object.
        # The File class should set the old name at File`s cache/history automatically,
        # filename and extension should be property functions.
        object_to_process.filename = new_filename
        object_to_process.extension = extension

        return True


class WindowsRenamer(Renamer):
    """
    Class following Windows style of renaming existing file to be used on Renamer pipelines.
    """
    enumeration_pattern = re.compile(r' ?\([0-9]+\)$|\[[0-9]+\]$|$')

    @classmethod
    def get_name(cls, directory_path, filename, extension):
        """
        Method to get the new generated name.
        If there is a duplicated name the new name will follow
        the style of Windows: `new name (1).ext`
        """
        old_filename = filename

        # Prepare filename and extension removing enumeration from filename
        # and setting up a empty string is extension is None
        filename = cls.enumeration_pattern.sub('', filename)
        extension = f'.{extension}' if extension else ''

        i = 0
        while cls.file_system_handler.exists(directory_path + filename + extension):
            i += 1
            filename = cls.enumeration_pattern.sub(f' ({i})', filename)

        return filename, extension


class LinuxRenamer(Renamer):
    """
    Class following Linux style of renaming existing file to be used on Renamer pipelines.
    """
    enumeration_pattern = re.compile(r'( +)?\- +[0-9]+$|$')

    @classmethod
    def get_name(cls, directory_path, filename, extension):
        """
        Method to get the new generated name.
        If there is a duplicated name the new name will follow
        the style of Linux: `new name - 1.ext`
        """
        old_filename = filename

        # Prepare filename and extension removing enumeration from filename
        # and setting up a empty string is extension is None
        filename = cls.enumeration_pattern.sub('', filename)
        extension = f'.{extension}' if extension else ''

        i = 0
        while cls.file_system_handler.exists(directory_path + filename + extension):
            i += 1
            filename = cls.enumeration_pattern.sub(f' - {i}', filename)

        return filename, extension


class UniqueRenamer(Renamer):

    @classmethod
    def get_name(cls, directory_path, filename, extension):
        """
        Method to get the new generated name. The new name will be the UUID version 4.
        This method will throw a BlockingIOError if there is more then
        100 tries to generate a unique UUID4.
        """
        extension = f'.{extension}' if extension else ''

        #Generate Unique filename
        filename = uuid4()

        i = 0
        while cls.file_system_handler.exists(directory_path + filename + extension) and i < 100:
            i += 1
            #Generate Unique filename
            filename = uuid4()

        if i == 100:
            raise BlockingIOError("Too many files being handler simultaneous")

        return filename, extension
