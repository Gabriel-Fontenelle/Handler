"""
Module with declaration of baseline class for the pipeline and its inherent class.
This module should only keep the pipeline class for comparing Files.
"""
from typing import Union

from handler.pipelines.__init__ import ProcessorMixin


class Comparer(ProcessorMixin):
    
    file_system_handler = FileSystem

    @classmethod
    def compare(cls, *args, **kwargs):
        """
        Method to compare if two items are the same. In this method the object to be compared can be
        two files, two hashes or any other value that args and kwargs can assume.
        This method is used internally in is_the_same, thus both must be overwrite on child class.
        This method must be overwrite on child class to work correctly.
        """
        raise NotImplementedError("The method is_the_same needs to be overwrite on child class.")

    @classmethod
    def is_the_same(cls, file_1, file_2):
        """
        Method used to check if two files are the same in memory using the File object.
        This method must be overwrite on child class to work correctly.
        """
        raise NotImplementedError("The method is_the_same needs to be overwrite on child class.")

    @classmethod
    def process(cls, *args, **kwargs):
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
            if not cls.is_the_same(first, element):
                return False

        return True

