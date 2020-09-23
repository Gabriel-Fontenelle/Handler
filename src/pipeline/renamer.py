# -*- coding: utf-8 -*-

# Python internals
from uuid import uuid4

# core modules
from src.pipeline.pipeline import ProcessorMixin
from ..core.regex import (
    PatternFile
)

# modules
from src.handler import FileSystem


# TODO: Change to be for File class and not file system.


class Renamer(ProcessorMixin):
    """
    Base class to be inherent to define class to be used on
    renamer pipeline.
    """

    old_complete_name = None
    old_filename = None
    extension = None

    file_system_class = FileSystem
    
    @classmethod
    def set_filename(cls, filename, extension=None):
        """
        Method to separated extension from filename if extension
        not informed and save on class.
        """
        # Remove
        if extension and filename[-len(extension):] == extension:
            cls.old_complete_name = filename
            filename = filename[:-len(f".{extension}")]
            cls.extension = extension

        cls.old_filename = filename

    @classmethod
    def get_name(cls, directory_path):
        """
        Method to get the new generated name.
        """
        raise NotImplementedError("Method get_name must be overwrite on child class.")

    @classmethod
    def process(self, *args, **kwargs):
        """
        Method used to run this class on Processor`s Pipeline.
        This method and to_processor() is not need to compare files
        outside a pipeline.
        """
        pass


class WindowsRenamer(Renamer):

    @staticmethod
    def get_name(cls, directory_path):
        """
        Method to get the new generated name.
        If there is a duplicated name the new name will follow
        the style of Windows: `new name (1).ext`
        """
        #Remove enumeration from filename
        filename = PatternFile.pattern_enumeration.sub('', filename)

        i = 0
        while cls.file_system_class.exists(path + filename + "." + extension):
            i += 1
            filename = PatternFile.pattern_enumeration.sub(' (' + str(i) + ')', filename)

        return filename


class LinuxRenamer(Renamer):

    @staticmethod
    def get_name(cls, directory_path):
        """
        Method to get the new generated name.
        If there is a duplicated name the new name will follow
        the style of Linux: `new name - 1.ext`
        """


class UniqueRenamer(Renamer):

    @staticmethod
    def get_name(cls, directory_path):
        """
        Method to get the new generated name. The new name will be the UUID version 4.
        This method will throw a BlockingIOError if there is more then
        100 tries to generate a unique UUID4.
        """
        extension = f".{cls.extension}" if cls.extension else ""

        #Generate Unique filename
        filename = uuid4()

        i = 0
        while cls.file_system_class.exists(directory_path + filename + extension) and i < 100:
            i += 1
            #Generate Unique filename
            filename = uuid4()

        if i == 100:
            raise BlockingIOError("Too many files being handler simultaneous")

        return filename
