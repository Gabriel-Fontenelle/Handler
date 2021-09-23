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

from inspect import ismethod

__all__ = [
    'Processor',
    'ProcessorMixin',
    'Pipeline'
]


class Processor:
    """
    Class to initiate a processor to be used on Pipeline.
    Processors are intermediate class between the pipelines manager (Pipeline)
    and the class with the methods to be run on pipelines.
    """

    verbose_name = None
    """
    Verbose name for processor.
    """
    classname = None
    """
    The class for the processor, this is the class that will be instantiated
    to run the processor.
    """
    method_name = None
    """
    Name of method that must be called when run this processor.
    This method must be have a @classmethod attribute.
    """
    stopper = False
    """
    If this processor stops the pipelines or not.
    """
    overrider = False
    """
    If this processor should be allow to overwritten data or not.
    """
    stop_value = True
    """
    The value that should stop the processor when stopper is True.
    """

    def __init__(self, **kwargs):
        """
        Method to instantiate the Processor object.
        """
        # Set-up attributes from kwargs like `classname` or `verbose_name`
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __getattr__(self, item):
        """
        Method to return classname.<item> if no attribute is found in current object.
        This method only work with attributes of classname, not attributes of classname object.
        """
        return getattr(self.classname, item)

    def run(self, *args, **kwargs):
        """
        Method to run method_name from classname and return boolean. Thus running the processor logic.
        For this method to work method_name should return boolean whether it as successful or not.
        """
        list_args = list(args)
        object_to_process = kwargs.pop('object', None) or list_args.pop(0)
        args = tuple(list_args)

        # Get method
        method = getattr(self.classname, self.method_name)

        # Check if method of method_name has `classmethod` decorator being bound to class
        # If not, properly instantiate the class to run the method.
        if not ismethod(method):
            class_to_use = self.classname()
            method = getattr(class_to_use, self.method_name)
            return method(object_to_process, *args, overrider=self.overrider, **kwargs)

        # Run method_name (`classmethod` or class function) passing args and kwargs to it
        # and return boolean result from processor
        return method(object_to_process, *args, overrider=self.overrider, **kwargs)


class ProcessorMixin:
    """
    Class to add required methods of pipelines to the class of processor.classname.
    """
    method_name_to_process = "process"

    @classmethod
    def to_processor(cls, stopper=False, stop_value=True, overrider=False):
        """
        Method used to return a processor from class.
        This method can be overwritten in child class. Valid return are Processor object or
        dict containing classname, verbose_name, stopper, stop_value.
        """
        processor = Processor(
            classname=cls,
            verbose_name=cls.__name__,
            stopper=stopper,
            stop_value=stop_value,
            overrider=overrider,
            method_name=cls.method_name_to_process,
        )
        return processor

    @classmethod
    def process(cls, *args, **kwargs):
        """
        Method used to run this class on Processor`s Pipeline.
        This method and to_processor() is not need to compare files
        outside a pipelines.
        Inside the pipeline this method will call to_processor() and run custom logic to
        process the current pipeline that could be a extracter, renamer, hasher, etc.
        """
        raise NotImplementedError("The process method must be overwrite on child class.")


class Pipeline:
    """
    Class to initiate a pipelines with given processors to be run.
    """

    def __init__(self, *processors):
        """
        This method can receive a single Processor object,
        or a list of Processor objects or a tuple with classname, verbose_name
        and stopper configuration.
        """
        self.processors_ran = 0
        """ 
        Variable to register the amount of processors ran for this pipelines.
        """
        self.last_result = None
        """
        Variable to register the last result obtained from pipeline.
        """
        self.pipeline_processors = []
        """
        Variable to register the available processors for the current pipeline object.
        """

        for processor in processors:
            # Check if processor is a dict containing classname, verbose_name and stopper
            if isinstance(processor, dict):
                if not ('classname' in processor or 'stopper' in processor):
                    raise ValueError("Processor dict for pipelines need at least classname and stopper set.")

                self.add_new_processor(
                    classname=processor.pop('classname'),
                    stopper=processor.pop('stopper'),
                    verbose_name=processor.pop('verbose_name', None),
                )

            # Check if processor is an object from Processor
            # As the code `elif isinstance(processor, Processor):` was not working, we change it to
            # be the class name.
            elif type(processor).__name__ == Processor.__name__:
                self.add_processor(processor)

            else:
                raise ValueError(f"{processor} is not a valid processor. Expecting a dict or Processor object.")

    def __getitem__(self, item):
        """
        Method to allow extraction of processor from pipeline_processors directly from Pipeline object.
        """
        return self.pipeline_processors[item]

    def add_new_processor(self, classname, verbose_name, stopper):
        """
        Method to instantiate a new processor from parameters and
        add it to list of processors.
        """
        self.pipeline_processors.append(
            Processor(
                classname=classname,
                verbose_name=verbose_name,
                stopper=stopper
            )
        )

    def add_processor(self, processor):
        """
        Method add a processor object to list of processors.
        """
        self.pipeline_processors.append(
            processor
        )

    def run(self, *args, **kwargs):
        """
        Method to run the entire pipelines.
        The processor will define if method will stop or not the pipelines.
        Either args or kwargs must have the object to be processed.

        Not all pipelines are required to run this method, as example, Hasher Pipeline avoid
        its use when loading hashes from files.

        :param args:
        :param kwargs:

        """
        # For each processor
        ran = 0
        result = None

        for processor in self.pipeline_processors:
            result = processor.run(*args, **kwargs)
            ran += 1

            if processor.stopper:
                # If processor is a step that should stop the whole pipeline
                # we verify if we reach the condition to it stop. By default that
                # condition is True, but can be any value set-up in stop_value and
                # returned by processor.
                if (
                    result in processor.stop_value
                    if isinstance(processor.stop_value, (list, tuple))
                    else result is processor.stop_value
                ):
                    break

        # register statical data about pipelines.
        self.processors_ran = ran
        self.last_result = result
