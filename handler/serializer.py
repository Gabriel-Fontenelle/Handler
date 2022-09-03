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
import inspect
from io import IOBase
from importlib import import_module

from dill import dumps, loads, HIGHEST_PROTOCOL
from json_tricks import loads as json_loads, dumps as json_dumps


__all__ = [
    'PickleSerializer',
    'JSONSerializer'
]


class PickleSerializer:
    """
    Class that allow handling of Serialization/Deserialization from object to pickle and from it to object.
    """

    @classmethod
    def serialize(cls, source):
        """
        Method to serialize the input `source` using dill as extension to `pickle`.
        """
        return dumps(source, protocol=HIGHEST_PROTOCOL, recurse=True)

    @classmethod
    def deserialize(cls, source):
        """
        Method to deserialize the input `source` using dill as extension to `pickle`.
        """
        return loads(source, protocol=HIGHEST_PROTOCOL, recurse=True)


class JSONSerializer:
    """
    Class that allow handling of Serialization/Deserialization from object to json string and from it to object.
    """

    @classmethod
    def _prepare_element(cls, source, cache=None):
        """
        Method to prepare the source converting it to a dict where class and objects are encoded as dictionaries to
        allow serialization.

        This method does not serialize class attributes for classes due to the fact that only the import is
        serialized.
        """
        # Set up initial cache, parameter used for controlling the objects' reference for serializing __self__.
        if cache is None:
            cache = {}

        object_id = id(source)
        cache.append(object_id)

        serialized_content = {}

        for key, element in source.__serialize__.items():
            if id(element) in cache:
                # Serialize reference to previous encountered object.
                serialized_content[key] = {"__self__": id(element)}

            elif hasattr(element, "__serialize__"):
                # Serialize supported object that has __serialize__ property.
                serialized_content[key] = cls._prepare_element(source=element, cache=cache)

            elif inspect.isclass(element):
                # Serialize class
                serialized_content[key] = {
                    "__class__": "{module}.{name}".format(module=element.__module__, name=element.__name__)
                }

            elif isinstance(element, IOBase):
                # Serialize buffer
                serialized_content[key] = {
                    "__buffer__": "{module}.{name}".format(module=element.__module__, name=element.__name__),
                    "__class__":  "{module}.{name}".format(module=element.__module__, name=element.__name__)
                }

            else:
                serialized_content[key] = element

        return {
            "__object__": "{module}.{name}".format(module=source.__class__.__module__, name=source.__class__.__name__),
            "__attribute__": serialized_content,
            "__id__": object_id
        }

    @classmethod
    def _instantiate_element(cls, source, cache):
        """
        Method to prepare the source converting it to objects decoding the dictionaries in source to
        allow deserialization.

        This method does not deserialize class attributes for classes due to the fact that it is instantiated a new one.
        """
        deserialized_content = {}

        # Get class and module for object
        modulename, classname = source["__object__"].rsplit(".", 1)

        # Load class
        class_instance = getattr(import_module(modulename), classname)

        for key, element in source["__attribute__"].items():
            if isinstance(element, dict):
                if "__object__" in element:
                    # Convert element to object
                    deserialized_content[key] = cls._instantiate_element(source=element, cache=cache)

                elif "__buffer__" in element:
                    # Convert element to buffer
                    pass

                elif "__class__" in element:
                    # Convert element to class
                    modulename, classname = element["__class__"].rsplit(".", 1)

                    # Import class
                    deserialized_content[key] = getattr(import_module(modulename), classname)

                else:
                    deserialized_content[key] = element
            else:
                deserialized_content[key] = element

        # Instantiate the current object
        instance = class_instance(**deserialized_content)

        # Register reference in cache
        cache[source["__id__"]] = instance

        return instance

    @classmethod
    def _fix_self_reference(cls, source, cache):
        """
        Method to fix the references present in instance source that were not able to be converted in
        _instantiate_element to allow deserialization to finish.
        """
        # Add the instance id to cache of inspections concluded to avoid calling fix_self_reference
        # again for object already inspect.
        cache["done"].append(id(source))

        for attribute, value in inspect.getmembers(source):
            # Ignore special attributes
            if attribute[0:2] == "__" and attribute[-2:] == "__":
                continue

            # Ignore non object
            elif (
                    inspect.isclass(value)
                    or inspect.ismethod(value)
                    or inspect.isdatadescriptor(value)
                    or inspect.isfunction(value)
                    or inspect.ismemberdescriptor(value)
                    or inspect.isgenerator(value)
            ):
                continue

            if isinstance(value, dict) and "__self__" in value:
                setattr(source, attribute, cache[value["__self__"]])

            elif hasattr(value, "__serialize__") and not callable(value) and id(value) not in cache["done"]:
                cls._fix_self_reference(value, cache)

    @classmethod
    def serialize(cls, source):
        """
        Method to serialize the input `source` using json_tricks as extension to `json`.
        """
        # Prepare content from __serialize__ with new dictionary for the cache
        serialized_content = cls._prepare_element(source, cache=[])

        # Convert to JSON.
        return json_dumps(serialized_content)

    @classmethod
    def deserialize(cls, source):
        """
        Method to deserialize the input `source` using json_tricks as extension to `json`.
        """
        # Prepare content to be parsed
        dictionary_content = json_loads(source, preserve_order=False)

        # Create cache dictionary to fix __self__ reference. The cache will be a
        # dictionary with pair id: instance and one special pair string: list for controlling
        # recursion.
        cache = {"done": []}

        # Convert elements of dictionary to objects
        instance = cls._instantiate_element(source=dictionary_content, cache=cache)

        # Fix self reference. This need to be done after creating the instances.
        cls._fix_self_reference(source=instance, cache=cache)

        return instance
