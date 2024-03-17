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
from inspect import isclass
from typing import Any, TYPE_CHECKING, Iterator, Type

from ..exception import ValidationError, PipelineError, ImproperlyConfiguredFile
from ..file.option import FileOption

if TYPE_CHECKING:
    from ..file import BaseFile


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

    @classmethod
    def import_class(cls, dotted_path: str) -> object:
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

    @classmethod
    def instantialize(self, processor: object, parameters: dict[str, Any]) -> object:
        """
        Method to set initial parameters required for processor to work.
        Current parameters: stopper <False>, stop_value <True>.
        """
        # Add parameters to processor for the pipeline to work: stopper, stop_value.
        # Don`t have stop value, so we consider the default `True`.
        processor = self._set_default_attributes(object_to_set=processor, attributes={
            'stopper': False,
            'stop_value': True
        })
        return processor

    @classmethod
    def validate(self, processor: object):
        """
        Method to validate if the processor object has the necessary attributes to allow the pipeline to be run.
        """
        # Check if processor has stop_value, stopper, process
        if not hasattr(processor, 'stop_value') or not isinstance(processor.stop_value, (bool, list, tuple, set)):
            raise ValidationError(
                f"Class {processor.__class__.__name__} should implement the attribute `stop_value` and it should be "
                "of type bool, list, tuple or set."
            )

        if not hasattr(processor, 'stopper') or not isinstance(processor.stopper, bool):
            raise ValidationError(
                f"Class {processor.__class__.__name__} should implement the attribute `stopper` and it should be "
                "of type bool."
            )

        # Validate if processor has the method `process` to allow it to be used in pipeline.
        if not hasattr(processor, 'process'):
            raise ValidationError(f"Class {processor.__class__.__name__} should implement the method `process` to be a "
                                  f"valid processor class.")

    @staticmethod
    def _set_default_attributes(object_to_set: object, attributes: dict[str, Any]) -> object:
        """
        Static method to set attributes for object. Only attributes that don`t exists are set-up.
        This method returns the object as a design choice, as it could just changing its attributes through reference.
        """
        for attribute, value in attributes.items():
            if not hasattr(object_to_set, attribute):
                setattr(object_to_set, attribute, value)

        return object_to_set

class Pipeline:
    """
    Class to initiate a pipelines with given processors to be run.
    The processors to be run will only be evaluated at running time when `__serialize__` or `run` are called.
    """
    processor: Type[Processor] = Processor

    def __init__(self, *processors_candidate: Any, **kwargs: Any) -> None:
        """
        This method can receive a single path to a class in string format that implement methods
        for processing the pipeline or a list, or tuple, of class` paths and parameters that will be passed to those
        class.

        Examples:
            Pipeline(
                "module.class",
                ("module.class", **kwargs),
                Object(),
            )
        """
        if not processors_candidate and "processors_candidate" not in kwargs:
            raise ValueError("A processor candidate must be informed for pipeline to be initialized")

        self.processors_ran: int = 0
        """
        Variable to register the amount of processors ran for this pipelines.
        """
        self.last_result: bool | None = None
        """
        Variable to register the last result obtained from pipeline.
        """
        self.pipeline_processors: list[object] = []
        """
        Variable to register the available processors for the current pipeline object.
        """
        self.errors: list = []
        """
        Variable to register the errors found by processors for the current pipeline object.
        """
        self.processors_candidate = kwargs.get("processors_candidate", processors_candidate)
        """
        Variable to register the original input that instantiate the Pipeline`s object.
        """

    def __getitem__(self, item: int) -> object:
        """
        Method to allow extraction of processor class from pipeline_processors directly from Pipeline object.
        """
        if not self.pipeline_processors:
            self.load_processor_candidates()

        return self.pipeline_processors[item]

    def __iter__(self) -> Iterator:
        """
        Method to allow direct usage of `pipeline_processors` in loops from Pipeline object.
        """
        if not self.pipeline_processors:
            self.load_processor_candidates()

        return iter(self.pipeline_processors)

    @property
    def __serialize__(self) -> dict[str, Any]:
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.

        This method only return processors_candidate because the pipeline should be clean before serializing and reset
        before being used from a deserialization.

        This method evaluate the processors.
        """
        if not self.pipeline_processors:
            self.load_processor_candidates()

        return {
            "processor": self.processor,
            "processors_candidate": self.processors_candidate
        }

    def load_processor_candidates(self):
        """
        Method to convert the processors candidates, informed at the class instantiator, to processors ready for use
        in the run method.
        The method accepts both string of a class` path and the class directly as the candidate for processor.

        This method will add attributes for the pipeline in the processor and validate if processor has the
        required attributes and methods for using it at `run`.
        """
        processor = self.processor

        for candidate in self.processors_candidate:
            # Get parameters if there is any besides processor in list or tuple.
            if isinstance(candidate, (tuple, list)):
                if len(candidate) > 2:
                    raise ImproperlyConfiguredPipeline(f"Invalid processor candidate {candidate}. "
                                                       "The processor candidate should not have more than two position"
                                                       " element.")

                parameters_to_override, candidate_path = candidate[1], candidate[0]
            else:
                parameters_to_override, candidate_path = {}, candidate

            # Check if a class was informed instead of path.
            if isclass(candidate_path):
                candidate_class = candidate_path
            else:
                # Convert the dotted path to a class type.
                candidate_class = processor.import_class(candidate_path)

            # Add additional attributes with option to override some parameters.
            processor_object = processor.instantialize(candidate_class, parameters=parameters_to_override)

            # Validate that all attributes and methods required for `run` exist in the class.
            # A ValidationError will be raised if there is a problem.
            processor.validate(processor_object)

            # Add the finished processor to the pipeline.
            self.pipeline_processors.append(processor_object)

    def run(self, object_to_process: BaseFile, **parameters: Any) -> None:
        """
        Method to run the entire pipelines.
        The processor will define if method will stop or not the pipelines.

        Not all pipelines are required to run this method, as example, Hasher Pipeline avoid
        its use when loading hashes from files.

        This method evaluate the processors.
        """

        if not hasattr(object_to_process, '_option') or not issubclass(object_to_process._option.__class__, FileOption):
            raise ImproperlyConfiguredFile(f"Object {type(object_to_process)} don`t have a option attribute of instance"
                                           "FileOption to allow the pipeline to run properly.")

        pipeline_raises_exception = object_to_process._option.pipeline_raises_exception

        # For each processor
        ran: int = 0
        result: bool | None = None
        errors_found: list = []

        if not self.pipeline_processors:
            self.load_processor_candidates()

        # Using iter here allow for override of __iter__ to affect the running process.
        for processor in self.__iter__():
            try:
                result = processor.process(object_to_process=object_to_process, **parameters)
                ran += 1

                if processor.stopper:
                    # If processor is a step that should stop the whole pipeline
                    # we verify if we reach the condition to it stop. By default, that
                    # condition is True, but can be any value set-up in stop_value and
                    # returned by processor.
                    stop_value: bool | list | tuple | set = processor.stop_value

                    should_stop: bool = (
                        result in stop_value
                        if isinstance(stop_value, (list, tuple, set))
                        else result == stop_value
                    )

                    if should_stop:
                        break

            except Exception as e:
                if pipeline_raises_exception:
                    raise PipelineError(f"An error ocurred while running process {type(processor)}: {e}") from e

                errors_found.append(e)

        # register statical data about pipelines.
        self.processors_ran = ran
        self.last_result = result
        self.errors = errors_found
