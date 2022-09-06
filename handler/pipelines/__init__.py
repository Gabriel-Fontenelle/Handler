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
from inspect import isclass
from importlib import import_module

from ..exception import ValidationError

__all__ = [
    'Processor',
    'Pipeline'
]


class Processor:
    """
    Class to initiate a processor to be used on Pipeline.
    Processors are intermediate class between the pipelines manager (Pipeline)
    and the class with the methods to be run on pipelines.
    """

    classname = None
    """
    The class for the processor, this is the class that actually run the processor`s method for pipeline.
    """
    parameters = None
    """
    The parameters informed when instantiating Processor to be passed for the processor`s method.
    """

    def __init__(self, source, **kwargs):
        """
        Method to instantiate the Processor object.
        """
        # Validate processor reference being inputted.
        if isinstance(source, str):
            self.classname = self.get_classname(source)
        elif isclass(source):
            self.classname = source
        else:
            raise ValidationError(f"Source parameter at Processor should be a string of dotted path or a class not"
                                  f" {type(source)}!")

        # Validate if classname has the method `process` to allow it to be used in pipeline.
        if not hasattr(self.classname, 'process'):
            raise ValidationError(f"Class {self.classname.__name__} should implement the method `process` to be a "
                                  f"valid processor class.")

        # Set-up attributes from kwargs like `classname` or `parameters`
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __getattr__(self, item):
        """
        Method to return classname.<item> if no attribute is found in current object.
        """
        if item in self.__dict__:
            return self.__dict__[item]

        return getattr(self.classname, item)

    @staticmethod
    def get_classname(dotted_path):
        """
        Method to obtain and import the processor`s class from the path informed at `dotted_path`.
        """
        try:
            module_path, class_name = dotted_path.rsplit('.', 1)
            module = import_module(module_path)
            return getattr(module, class_name)
        except (ValueError, AttributeError):
            raise ImportError(f"Was not possible to import processor {dotted_path}. Make sure that "
                              f"{dotted_path} is a python string with dotted path to a processor class.")


class Pipeline:
    """
    Class to initiate a pipelines with given processors to be run.
    """

    def __init__(self, *processors_candidate, **kwargs):
        """
        This method can receive multiples
        This method can receive a single path to a class in string format that implement methods
        for processing the pipeline or a list, or tuple, of class` paths and parameters that will be passed to those
         class.
        objects
        or a tuple with classname, verbose_name
        and stopper configuration.
        """
        if not processors_candidate and "processors_candidate" not in kwargs:
            raise ValueError("A processor candidate must be informed for pipeline to be initialized")

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
        self.errors = []
        """
        Variable to register the errors found by processors for the current pipeline object.
        """
        self.processors_candidate = kwargs.get("processors_candidate", processors_candidate)
        """
        Variable to register the original input that instantiate the Pipeline`s object.
        """

        for candidate in self.processors_candidate:
            try:
                # Get parameters if there is any besides processor in list or tuple.
                if isinstance(candidate, (tuple, list)):
                    parameters, processor_candidate = candidate[1], candidate[0]
                else:
                    parameters, processor_candidate = {}, candidate

                self.add_processor(Processor(source=processor_candidate, parameters=parameters))
            except ValidationError:
                continue

    def __getitem__(self, item):
        """
        Method to allow extraction of processor class from pipeline_processors directly from Pipeline object.
        """
        return self.pipeline_processors[item]

    def __iter__(self):
        """
        Method to allow direct usage of `pipeline_processors` in loops from Pipeline object.
        """
        return iter(self.pipeline_processors)

    @property
    def __serialize__(self):
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.

        This method only return processors_candidate because the pipeline should be clean before serializing and reset
        before being used from a deserialization.
        """
        return {
            "processors_candidate": self.processors_candidate
        }

    def add_processor(self, processor):
        """
        Method adds a processor object to list of processors.
        """
        self.pipeline_processors.append(processor)

    def run(self, object_to_process, **parameters):
        """
        Method to run the entire pipelines.
        The processor will define if method will stop or not the pipelines.

        Not all pipelines are required to run this method, as example, Hasher Pipeline avoid
        its use when loading hashes from files.
        """
        # For each processor
        ran = 0
        result = None
        errors_found = []

        for processor in self.pipeline_processors:
            result = processor.process(object_to_process=object_to_process, **processor.parameters, **parameters)
            ran += 1

            if hasattr(processor, 'errors') and processor.errors:
                errors_found += processor.errors

            if hasattr(processor, 'stopper') and processor.stopper:
                # If processor is a step that should stop the whole pipeline
                # we verify if we reach the condition to it stop. By default that
                # condition is True, but can be any value set-up in stop_value and
                # returned by processor.
                try:
                    stop_value = processor.stop_value
                except AttributeError:
                    # Don`t have stop value, so we consider the default `True`.
                    stop_value = True

                should_stop = result in stop_value if isinstance(stop_value, (list, tuple)) else result == stop_value

                if should_stop:
                    break

        # register statical data about pipelines.
        self.processors_ran = ran
        self.last_result = result
        self.errors = errors_found
