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
from datetime import time, datetime
from io import IOBase
from importlib import import_module

from dill import dumps, loads, HIGHEST_PROTOCOL
from json_tricks import (
    loads as json_loads,
    dumps as json_dumps,
    hashodict,
)

from .storage import LinuxFileSystem

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
                    storage_module, storage_classname = element["__storage__"].rsplit(".", 1)
                    storage = getattr(import_module(storage_module), storage_classname)

                    # Convert element to buffer
                    if storage.exists(element["__buffer__"]):
                        deserialized_content[key] = storage.open_file(
                            file_path=element["__buffer__"],
                            mode=element["__mode__"]
                        )
                        break

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
        This method implements internal functions to handle custom types available in Handler that should be
        encoded. Those internal functions will be applied for each list, tuple and dict elements automatically by
        `json.encoder`.
        """

        # List object to use as cache to allow retrieving ids already processed.
        cache = []

        def json_date_time_encode(obj, primitives=False):
            """
            Internal function to solve a problem with the original encoder where `obj.tzinfo.zone` results in attribute
            error.
            """
            if primitives:
                return obj.isoformat()

            if isinstance(obj, datetime):
                dct = hashodict([('__datetime__', None), ('year', obj.year), ('month', obj.month),
                                 ('day', obj.day), ('hour', obj.hour), ('minute', obj.minute),
                                 ('second', obj.second), ('microsecond', obj.microsecond)])

                if obj.tzinfo:
                    dct['tzinfo'] = getattr(obj.tzinfo, 'zone', None) or str(obj.tzinfo)

            elif isinstance(obj, time):
                dct = hashodict([('__time__', None), ('hour', obj.hour), ('minute', obj.minute),
                                 ('second', obj.second), ('microsecond', obj.microsecond)])

                if obj.tzinfo:
                    dct['tzinfo'] = getattr(obj.tzinfo, 'zone', None) or str(obj.tzinfo)

            else:
                return obj

            # Remove empty values
            for key, val in tuple(dct.items()):
                if not key.startswith('__') and not val:
                    del dct[key]

            return dct

        def json_class_encode(obj, primitives=False):
            """
            Internal function to encode a class reference.
            """
            if inspect.isclass(obj):
                if primitives:
                    return f"{obj.__module__}.{obj.__name__}"

                return hashodict([('__class__', None), ('module', obj.__module__), ('name', obj.__name__)])

            return obj

        def json_buffer_encode(obj, primitives=False):
            """
            Internal function to encode a IO Buffer.
            To avoid circular reference error in json encoder we call json_class_encode to encode the storage's class.
            """
            default_storage_class = source.storage if hasattr(source, 'storage') and source.storage else LinuxFileSystem

            if primitives:
                return f"{obj.name}:{obj.mode}:{json_class_encode(default_storage_class, primitives)}"

            if isinstance(obj, IOBase):
                return hashodict(
                    [
                        ('__buffer__', None),
                        ('name', obj.name),
                        ('mode', obj.mode),
                        ('storage', json_class_encode(default_storage_class, primitives)),
                    ]
                )

            return obj

        def json_self_reference_encode(obj, primitives=False):
            """
            Internal function to encode a BaseFile or any class that inherent from source and has `__serialize__`
            property.
            """
            if id(obj) in cache:
                if primitives:
                    return id(obj)

                return hashodict([('__self__', None), ('id', id(obj))])

            elif isinstance(obj, source.__class__) and hasattr(obj, '__serialize__'):
                object_id = id(obj)
                cache.append(object_id)

                if primitives:
                    return (json_class_encode(source.__class__, primitives), obj.__serialize__, object_id)

                return hashodict(
                    [
                        ("__object__", None),
                        ("class", json_class_encode(source.__class__, primitives)),
                        ("attributes", obj.__serialize__),
                        ("id", object_id)
                    ]
                )

            return obj

        # Convert to JSON.
        # We don't check for circular reference because we should resolve it in `json_self_reference_encode`.
        return json_dumps(source, extra_obj_encoders=(
            json_self_reference_encode, json_date_time_encode, json_class_encode, json_buffer_encode,
        ), check_circular=False)

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
