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

import inspect
from datetime import time, datetime
from importlib import import_module
from io import IOBase
from typing import Any, Type, TYPE_CHECKING

import pytz
from dill import dumps, loads, HIGHEST_PROTOCOL

from ..storage import LinuxFileSystem

if TYPE_CHECKING:
    from .storage import Storage
    from json_tricks import hashodict


__all__ = [
    'PickleSerializer',
    'JSONSerializer'
]


class PickleSerializer:
    """
    Class that allow handling of Serialization/Deserialization from object to pickle and from it to object.
    """

    @classmethod
    def serialize(cls, source: Any) -> Any:
        """
        Method to serialize the input `source` using dill as extension to `pickle`.
        """
        return dumps(source, protocol=HIGHEST_PROTOCOL, recurse=True)

    @classmethod
    def deserialize(cls, source: Any) -> Any:
        """
        Method to deserialize the input `source` using dill as extension to `pickle`.
        """
        return loads(source, protocol=HIGHEST_PROTOCOL, recurse=True)


class JSONSerializer:
    """
    Class that allow handling of Serialization/Deserialization from object to json string and from it to object.
    """

    @classmethod
    def serialize(cls, source: Any) -> str:
        """
        Method to serialize the input `source` using json_tricks as extension to `json`.
        This method implements internal functions to handle custom types available in Handler that should be
        encoded. Those internal functions will be applied for each list, tuple and dict elements automatically by
        `json.encoder`.
        """
        from json_tricks import hashodict, dumps as json_dumps

        # List object to use as cache to allow retrieving ids already processed.
        cache: list = []

        def json_date_time_encode(obj: object, primitives: bool = False) -> object | hashodict:
            """
            Internal function to solve a problem with the original encoder where `obj.tzinfo.zone` results in attribute
            error.
            """
            if isinstance(obj, datetime):
                if primitives:
                    return obj.isoformat()

                dct = hashodict([('__datetime__', None), ('year', obj.year), ('month', obj.month),
                                 ('day', obj.day), ('hour', obj.hour), ('minute', obj.minute),
                                 ('second', obj.second), ('microsecond', obj.microsecond)])

                if obj.tzinfo:
                    dct['tzinfo'] = getattr(obj.tzinfo, 'zone', None) or str(obj.tzinfo)

            elif isinstance(obj, time):
                if primitives:
                    return obj.isoformat()

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

        def json_class_encode(obj: object, primitives: bool = False) -> object | str | hashodict:
            """
            Internal function to encode a class reference.
            """
            if inspect.isclass(obj):
                if primitives:
                    return f"{obj.__module__}.{obj.__name__}"

                return hashodict([('__class__', None), ('module', obj.__module__), ('name', obj.__name__)])

            return obj

        def json_buffer_encode(obj: object, primitives: bool = False) -> object | str | hashodict:
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
                        ('name', getattr(obj, 'name', "")),
                        ('mode', getattr(obj, 'mode', "")),
                        ('storage', json_class_encode(default_storage_class, primitives)),
                    ]
                )

            return obj

        def json_self_reference_encode(obj: object, primitives: bool = False) -> object | tuple | hashodict:
            """
            Internal function to encode a BaseFile or any class that inherent from source and has `__serialize__`
            property.
            """
            if id(obj) in cache:
                if primitives:
                    return id(obj)

                return hashodict(
                    [
                        ('__self__', None), ('class', json_class_encode(obj.__class__, primitives)), ('id', id(obj))
                    ]
                )

            elif hasattr(obj, '__serialize__') and not callable(obj.__serialize__):
                object_id = id(obj)
                cache.append(object_id)

                if primitives:
                    return json_class_encode(obj.__class__, primitives), obj.__serialize__, object_id

                return hashodict(
                    [
                        ("__object__", None),
                        ("class", json_class_encode(obj.__class__, primitives)),
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
    def deserialize(cls, source: Any) -> dict[str, Any]:
        """
        Method to deserialize the input `source` using json_tricks as extension to `json`.
        """

        # Create cache dictionary to fix __self__ reference. The dictionary will have a numeric key with
        # instance as value. The `done` list will be used when fixing reference for related objects.
        cache: dict[str, list] = {"done": []}

        def json_date_time_hook(dct) -> dict | datetime | time | None:
            """
            Internal function to parse the __datetime__ and __time__ dictionary.
            This function solves a problem with the original decoder where importing pytz results in attribute error.
            """
            def get_tz(dct):
                """
                Internal function to process the tzinfo key from dictionary to be a tzinfo object.
                """
                if 'tzinfo' not in dct:
                    return None

                return pytz.timezone(dct['tzinfo'])

            if not isinstance(dct, dict):
                return dct

            if '__time__' in dct:
                tzinfo = get_tz(dct)
                return time(hour=dct.get('hour', 0), minute=dct.get('minute', 0), second=dct.get('second', 0),
                            microsecond=dct.get('microsecond', 0), tzinfo=tzinfo)

            elif '__datetime__' in dct:
                tzinfo = get_tz(dct)
                dt = datetime(year=dct.get('year', 0), month=dct.get('month', 0), day=dct.get('day', 0),
                              hour=dct.get('hour', 0), minute=dct.get('minute', 0), second=dct.get('second', 0),
                              microsecond=dct.get('microsecond', 0))
                if tzinfo is None:
                    return dt

                return tzinfo.localize(dt)

            return dct

        def json_class_hook(dct: object) -> dict | object:
            """
            Internal function to parse the __class__ dictionary.
            """
            if not isinstance(dct, dict):
                return dct

            if "__class__" in dct:
                return getattr(import_module(dct['module']), dct['name'])

            return dct

        def json_buffer_hook(dct: object) -> dict | object:
            """
            Internal function to parse the __buffer__ dictionary.
            """
            if not isinstance(dct, dict):
                return dct

            if "__buffer__" in dct:
                storage: Type[Storage] = json_class_hook(dct.get('storage'))

                name: str | None = dct.get("name")

                if name and storage.exists(name):
                    return storage.open_file(path=name, mode=dct["mode"])

                return None

            return dct

        def json_object_hook(dct: object) -> dict | object:
            """
            Internal function to parse the __object__ dictionary.
            """
            if not isinstance(dct, dict):
                return dct

            if "__object__" in dct and dct.get("id"):
                class_instance: Type[Any] = dct.get('class')
                parsed_object: Any = class_instance(**dct.get('attributes'))

                cache[dct.get('id')] = parsed_object

                return parsed_object

            elif "__self__" in dct:
                try:
                    return cache[dct.get("id")]
                except KeyError:
                    return dct

            return dct

        def fix_self_reference(instance: Any) -> None:
            """
            Internal function to fix the references present in instance source that were not able to be
            converted in decoder to allow the deserialization to finish.
            """
            # Add the instance id to cache of inspections concluded to avoid calling fix_self_reference
            # again for object already inspect.
            cache["done"].append(id(instance))

            def fix_iterator_value(listing):
                """
                Internal function to recursively to process list, tuple, and dict that could have an object with
                __serialize__ property.
                """
                for index, item in listing:
                    if isinstance(item, dict) and "__self__" in item:
                        listing[index] = cache[item["id"]]
                    elif hasattr(item, "__serialize__") and not callable(item) and id(item) not in cache["done"]:
                        fix_self_reference(item)
                    elif isinstance(item, dict):
                        fix_iterator_value(item.items())
                    elif isinstance(item, (list, tuple)):
                        fix_iterator_value(enumerate(item))

            for attribute, value in instance.__serialize__.items():
                if isinstance(value, dict) and "__self__" in value:
                    setattr(instance, attribute, cache[value["id"]])

                elif isinstance(value, dict):
                    fix_iterator_value(value.items())

                elif isinstance(value, (list, tuple)):
                    fix_iterator_value(enumerate(value))

                elif hasattr(value, "__serialize__") and not callable(value) and id(value) not in cache["done"]:
                    fix_self_reference(value)

        from json_tricks import loads as json_loads

        # Prepare content to be parsed
        deserialized_object: dict = json_loads(source, preserve_order=False, extra_obj_pairs_hooks=(
            json_date_time_hook, json_class_hook, json_buffer_hook, json_object_hook
        ))

        # Fix self reference. This need to be done after creating the instances.
        fix_self_reference(instance=deserialized_object)

        return deserialized_object
