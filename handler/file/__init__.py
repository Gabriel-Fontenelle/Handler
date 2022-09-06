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

# first-party
from io import IOBase, StringIO, BytesIO
from os import name

# modules
from .action import FileActions
from .descriptor import InternalFilesDescriptor, LoadedDescriptor, CacheDescriptor
from .name import FileNaming
from .state import FileState
from ..exception import (
    ImproperlyConfiguredFile,
    NoInternalContentError,
    OperationNotAllowed,
    ReservedFilenameError,
    SerializerError,
    ValidationError,
)
from ..handler import URI
from ..mimetype import LibraryMimeTyper
from ..pipelines import Pipeline
from ..pipelines.renamer import UniqueRenamer
from ..serializer import JSONSerializer
from ..storage import LinuxFileSystem, WindowsFileSystem

__all__ = [
    'BaseFile',
    'ContentFile',
    'File',
    'StreamFile'
]


class FileMetadata:
    """
    Class that store file instance metadata.
    """

    packed = False
    """
    Indicate whether an object was packed in a container or not. As example: .rar, .epub, .tar. 
    """
    compressed = False
    """
    Indicate whether an object was compressed or not. Different from packed, an object can the packed and not 
    compressed or it could be both packed and compressed.
    """
    lossless = False
    """
    Indicate whether an object was lossless compressed or not. 
    """
    hashable = True
    """
    Indicate whether an object can have its hash saved or not. Internal packed files cannot have hash saved to file, 
    it can be generate just not saved in the package.
    """

    # Hasher files
    # loaded = None
    """
    Indicate whether an object is a hash file loaded from a file or not.
    This is mostly used for hash files created with hasher and will be set up only in those files.
    """
    # checksum = None
    """
    Indicate whether an object is a hash file named CHECKSUM.hasher_name file (contains multiple files) or not.
    This is mostly used for hash files created with hasher and will be set up only in those files.
    """

    def __init__(self, **kwargs):
        """
        Method to create the current object using the keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key) or key in {"checksum", "loaded"}:
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

    @property
    def __serialize__(self):
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """

        attributes = {
            "packed",
            "compressed",
            "lossless",
            "hashable"
        }
        optional_attributes = {
            "checksum",
            "loaded"
        }

        class_vars = {key: getattr(self, key) for key in attributes}

        for attribute in optional_attributes:
            if hasattr(self, attribute):
                class_vars[attribute] = getattr(self, attribute)

        return class_vars


class FileHashes:
    """
    Class that store file instance digested hashes.
    """

    _cache = CacheDescriptor()
    """
    Descriptor to storage the digested hashes for the file instance.
    """
    _loaded = LoadedDescriptor()
    """
    Descriptor to storage the digested hashes that were loaded from external source. 
    """

    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes.
    """

    def __init__(self, **kwargs):
        """
        Method to create the current object using the keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

    def __setitem__(self, hasher_name, value):
        """
        Method to set up values for file hash as dict item.
        This method expects a tuple as value to set up the hash hexadecimal value and hash file related
        to the hasher.
        """
        hex_value, hash_file, processor = value

        # Make code independent of instance File.
        if "BaseFile" not in [hash_class.__name__ for hash_class in hash_file.__class__.__mro__]:
            raise ImproperlyConfiguredFile("Tuple for hashes must be the Hexadecimal value and a File Object for the "
                                           "hash.")

        self._cache[hasher_name] = hex_value, hash_file, processor

        if hasattr(hash_file.meta, 'loaded') and hash_file.meta.loaded is True:
            # Add `hash_file` loaded from external source in a list for easy retrieval of loaded hashes.
            self._loaded.append(hasher_name)

    def __getitem__(self, hasher_name):
        """
        Method to get the hasher value and file associated saved in self._cache.
        """
        return self._cache[hasher_name]

    def __iter__(self):
        """
        Method to return iterable from self._cache instead of current class.
        """
        return iter(self._cache)

    def __bool__(self):
        """
        Method to check if there is any hash saved in self._cache.
        """
        return bool(self._cache)

    @property
    def __serialize__(self):
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes = {"_cache", "_loaded", "related_file_object"}

        return {key: getattr(self, key) for key in attributes}

    def rename(self, new_filename):
        """
        This method will rename file for each hash file existing in _caches.
        This method don`t save files, only prepare the filename and content to be correct before saving it.
        """
        for hasher_name, value in self._cache.items():
            hex_value, hash_file, processor = value

            if not hash_file.meta.checksum:
                # Rename filename if is not `checksum.hasher_name`
                # complete_filename is a property that will set up additional action to rename the file`s filename if
                # it was already saved before.
                hash_file.complete_filename = new_filename, hasher_name

            # Load content from generator.
            # First we set up content of type binary or string.
            content = b"" if hash_file.is_binary else ""

            # Then we load content from generator using a loop.
            for block in hash_file.content:
                content += block

            # Change file`s filename inside content of hash file.
            content = content.replace(f"{hash_file.filename}.{hasher_name}", f"{new_filename}.{hasher_name}")

            # Set-up new content after renaming and specify that hash_file was not saved yet.
            hash_file.content = content
            hash_file._actions.to_save()

    def validate(self, force=False):
        """
        Method to validate the integrity of file comparing hashes`s hex value with file content.
        This method will only check the first hex value from files loaded, or any cached hash if no hash loaded from
        external source is available, for efficient sake. If desire to check all hashes in loaded set `force` to True.
        """
        if not (self._loaded or self._cache):
            raise ValueError(f"There is no hash available to compare for file {self.related_file_object}.")

        for hash_name in self._loaded or self._cache.keys():
            hex_value, hash_file, processor = self._cache[hash_name]
            # Compare content with hex_value
            result = processor.check_hash(object=self.related_file_object, compare_to_hex=hex_value)

            if not result:
                raise ValidationError(f"File {self.related_file_object} don`t pass the integrity check with "
                                      f"{hash_name}!")

            if not force:
                break

    def save(self, overwrite=False):
        """
        Method to save all hashes files if it was not saved already.
        """
        if not self.related_file_object:
            raise ImproperlyConfiguredFile("A related file object must be specified for hashes before saving.")

        for hex_value, hash_file, processor in self._cache.values():
            if hash_file._actions.save:
                if hash_file.meta.checksum:
                    # If file is CHECKSUM.<hasher_name> we not allow to overwrite.
                    hash_file.save(overwrite=False, allow_update=overwrite)
                else:
                    hash_file.save(overwrite=overwrite, allow_update=overwrite)


class FileContent:
    """
    Class that store file instance content.
    """
    # Properties
    is_binary = False
    """
    Type of stream used in buffer for content. 
    """

    # Buffer handles
    buffer = None
    """
    Stream for file`s content.
    """
    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes and other data.
    """
    _block_size = 256
    """
    Block size of file to be loaded in each step of iterator.
    """
    _buffer_encoding = 'utf-8'
    """
    Encoding default used to convert the buffer to string.
    """

    # Cache handles
    cache_content = False
    """
    Whether the content should be cached.
    """
    cache_in_memory = True
    """
    Whether the cache will be made in memory.
    """
    cache_in_file = False
    """
    Whether the cache will be made in filesystem.
    """
    cached = False
    """
    Whether the content as whole was cached. Being True the current buffer will point to a stream
    of `_cached_buffer`.
    """
    _cached_buffer = None
    """
    Stream for file`s content cached.
    """
    _cached_path = None
    """
    Complete path for temporary file used as cache. 
    """

    def __init__(self, raw_value, force=False, **kwargs):
        """
        Initial method that set up the buffer to be used.
        The parameter `force` when True will force usage of cache even if is IO is seekable.
        """
        # Process kwargs before anything, because buffer can be already set up in kwargs, as this
        # init can be used for serialization and deserialization.
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

        if "buffer" in kwargs:
            # We already set up buffer, so we don't need to set up it from raw_value
            return

        if not raw_value:
            raise ValueError(f"Value pass to FileContent must not be empty!")

        if isinstance(raw_value, (str, bytes)):
            try:
                raw_value = StringIO(raw_value)
            except TypeError:
                raw_value = BytesIO(raw_value)

        elif not isinstance(raw_value, IOBase):
            raise ValueError(f"parameter `value` informed in FileContent is not a valid type"
                             f" {type(raw_value)}! We were expecting str, bytes or IOBase.")

        # Set attribute is_binary based on instance type.
        self.is_binary = isinstance(raw_value, BytesIO) or 'b' in getattr(raw_value, 'mode', '')

        # Add content (or content converted to Stream) as buffer
        self.buffer = raw_value

        # Set content to be cached.
        if not self.buffer.seekable() or force:
            self.cache_content = True
            self.cached = False

        # Default buffer for cache
        self._cached_buffer = None

    def __iter__(self):
        """
        Method to return current object as iterator. As it already implements __next__ we just return the current
        object.
        """
        return self

    def __next__(self):
        """
        Method that defines the behavior of iterable blocks of current object.
        This method has the potential to double the memory size of current object storing
        the whole buffer in memory.

        This method will cache content in file or in memory depending on value of `cache_content`, `cache_in_memory` and
        `cache_in_file`. For caching in file, it will generate a unique filename in a temporary directory.
        """
        block = self.buffer.read(self._block_size)

        # This end the loop if block is None, b'' or ''.
        if not block and block != 0:
            # Change buffer to be cached content
            if self.cache_content and not self.cached:
                if self.cache_in_memory:
                    class_name = BytesIO if self.is_binary else StringIO
                    self.buffer = class_name(self._cached_buffer)
                    self.cached = True
                elif self.cache_in_file:
                    # Buffer receive stream from file
                    mode = 'r' if self.is_binary else 'rb'
                    self.buffer = self.related_file_object.storage.open_file(self._cached_path, mode=mode)
                    self.cached = True

            # Reset buffer to begin from first position
            if self.buffer.seekable():
                self.buffer.seek(0)

            raise StopIteration()

        # Cache content
        if self.cache_content and not self.cached:
            # Cache content in memory only
            if self.cache_in_memory:
                if self._cached_buffer is None:
                    self._cached_buffer = block
                else:
                    self._cached_buffer += block
            # Cache content in temporary file
            elif self.cache_in_file:
                if not self._cached_path:
                    # Create new temporary file using renamer pipeline to obtain
                    # a unique filename for temporary file.
                    temp = self.related_file_object.storage.get_temp_directory()
                    filename, extension = UniqueRenamer.get_name(
                        directory_path=temp,
                        filename=self.related_file_object.filename,
                        extension=self.related_file_object.extension
                    )
                    formatted_extension = f'.{extension}' if extension else ''
                    if temp[-1] != self.related_file_object.storage.sep:
                        temp += self.related_file_object.storage.sep

                    self._cached_path = temp + filename + formatted_extension

                # Open file, append block to file and close file.
                write_mode = 'b' if self.is_binary else ''
                self.related_file_object.storage.save_file(self._cached_path, block, file_mode='a',
                                                           write_mode=write_mode)

        return block

    @property
    def __serialize__(self):
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes = {
            "is_binary",
            "buffer",
            "related_file_object",
            "_block_size",
            "_buffer_encoding",
            "cache_content",
            "cache_in_memory",
            "cache_in_file",
            "cached",
            "_cached_buffer",
            "_cached_path",
        }

        return {key: getattr(self, key) for key in attributes}

    @property
    def should_load_to_memory(self):
        """
        Method to indicate whether the current buffer is seekable or not. Not seekable object should
        """
        return not self.buffer.seekable() and not self.cached

    @property
    def content(self):
        """
        Method to load in memory the content of the file.
        This method uses the buffer cached, if the file wasn't cached before this method will cache it, and load
        the data in memory from the cache returning the content.
        """
        old_cache_in_memory = self.cache_in_memory
        old_cache_in_file = self.cache_in_file

        # Set cache to load in memory
        if not (self.cache_in_memory or self.cache_in_file):
            self.cache_in_memory = True
            self.cache_in_file = False

        if self._cached_buffer is None or self._cached_path is None:
            # Consume content if not loaded
            while True:
                try:
                    next(self)
                except StopIteration:
                    break

        # Content in case that it was loaded in memory. If not, it will be None and override below.
        content = self._cached_buffer

        # Override `content` with content from file.
        if self.cache_in_file:
            mode = 'rb' if self.is_binary else 'r'
            buffer = self.related_file_object.storage.open_file(self._cached_path, mode=mode)
            content = buffer.read()
            self.related_file_object.storage.close_file(buffer)

        self.cache_in_memory = old_cache_in_memory
        self.cache_in_file = old_cache_in_file

        return content

    @property
    def content_as_buffer(self):
        """
        Method to obtain the content as a buffer, loading it in memory if it is allowed and is not loaded already.
        """
        if self.should_load_to_memory:
            # We should load the current buffer to memory before using it.
            # Load content to memory with `self.content` and return the adequate buffer.
            buffer_class = BytesIO if self.is_binary else StringIO
            return buffer_class(self.content)
        else:
            # Should not reach here if object is not seekable, but
            # to avoid problems with override of `should_load_to_memory` property
            # we check before using seek to reset the content.
            if self.buffer.seekable():
                self.buffer.seek(0)

            return self.buffer


class FilePacket:
    """
    Class that store internal files from file instance content.
    """

    _internal_files = InternalFilesDescriptor()
    """
    Dictionary used for storing the internal files data. Each file is reserved through its <directory>/<name> inside
    the package.
    """

    history = None
    """
    Storage internal files to allow browsing old ones for current BaseFile.
    """

    # Pipelines
    extract_data_pipeline = Pipeline(
        'handler.pipelines.extractor.SevenZipCompressedFilesFromContentExtractor',
        'handler.pipelines.extractor.RarCompressedFilesFromContentExtractor',
        'handler.pipelines.extractor.ZipCompressedFilesFromContentExtractor',
    )
    """
    Pipeline to extract data from multiple sources. For it to work, its classes should implement stopper as True.
    """

    def __init__(self, **kwargs):
        """
        Method to create the current object using the keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

    def __getitem__(self, item):
        """
        Method to serve as shortcut to allow return of item in _internal_files in instance of FilePacket.
        """
        return self._internal_files[item]

    def __contains__(self, item):
        """
        Method to serve as shortcut to allow verification if item contains in _internal_files in instance of FilePacket.
        """
        return item in self._internal_files

    def __setitem__(self, key, value):
        """
        Method to serve as shortcut to allow adding an item in _internal_files in instance of FilePacket.
        """
        self._internal_files[key] = value

    def __len__(self):
        """
        Method that defines the size of current object. We will consider the size as being the same of
        `_internal_files`
        """
        return len(self._internal_files)

    def __iter__(self):
        """
        Method to return current object as iterator. As it already implements __next__ we just return the current
        object.
        """
        return iter(self._internal_files.items())

    @property
    def __serialize__(self):
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes = {"_internal_files", "extract_data_pipeline", "history"}

        return {key: getattr(self, key) for key in attributes}

    def clean_history(self):
        """
        Method to clean the history of internal_files.
        The data will still be in memory while the Garbage Collector don't remove it.
        """
        self.history = []

    def files(self):
        """
        Method to obtain the list of objects File stored at `_internal_files`.
        """
        return self._internal_files.values()

    def names(self):
        """
        Method to obtain the list of names of internal files stored at `_internal_files`.
        """
        return self._internal_files.keys()

    def reset(self):
        """
        Method to clean the internal files keeping a historic of changes.
        """
        if self.history is None:
            self.history = []

        # Add current internal files to memory
        self.history.append(self._internal_files)

        # Reset the internal files
        self._internal_files = {}


class BaseFile:
    """
    Base class for handle File. This class will be used in Files of type Image, Rar, etc.
    This class will behave like Django Model with methods save(), delete(), etc.

    TODO: Add support to moving and copying file avoiding conflict on moving or copying.
    """

    # Filesystem data
    id = None
    """
    File`s id in the File System.
    """
    filename = None
    """
    Name of file without extension.
    """
    extension = None
    """
    Extension of file.
    """
    create_date = None
    """
    Datetime when file was created.
    """
    update_date = None
    """
    Datetime when file was updated.
    """
    _path = None
    """
    Full path to file including filename. This is the raw path partially sanitized.
    BaseFile.sanitize_path is available through property.
    """
    _save_to = None
    """
    Path of directory to save file. This path will be use for mixing relative paths.
    This path should be accessible through property `save_to`.
    """
    relative_path = None
    """
    Relative path to save file. This path will be use for generating whole path together with save_to and 
    complete_filename (e.g save_to + relative_path + complete_filename). 
    """

    # Metadata data
    length = 0
    """
    Size of file content.
    """
    mime_type = None
    """
    File`s mime type.
    """
    type = None
    """
    File's type (e.g. image, audio, video, application).
    """
    _meta = None
    """
    Additional metadata info that file can have. Those data not always will exist for all files.
    """
    hashes = None
    """
    Checksum information for file.
    It can be multiples like MD5, SHA128, SHA256, SHA512.
    """

    # Initializer data
    _keyword_arguments = None
    """
    Additional attributes data passed to `__init__` method. This information is important to be able to 
    reload data from disk correctly.
    """

    # Handler
    storage = None
    """
    Storage or file system currently in use for File.
    It can be LinuxFileSystem, WindowsFileSystem or a custom one.
    """
    serializer = JSONSerializer
    """
    Serializer available to make the object portable. 
    This can be changed to any class that implements serialize and deserialize method.
    """
    mime_type_handler = LibraryMimeTyper()
    """
    Mimetype handler that defines the source of know Mimetypes.
    This is used to identify mimetype from extension and vice-verse.
    """
    uri_handler = URI
    """
    URI handler that defines methods to parser the URL.
    """

    # Pipelines
    extract_data_pipeline = None
    """
    Pipeline to extract data from multiple sources. This should be override at child class. This pipeline can be 
    non-blocking and errors that occur in it will be available through attribute `errors` at 
    `extract_data_pipeline.errors`.
    """
    compare_pipeline = Pipeline(
        'handler.pipelines.comparer.TypeCompare',
        'handler.pipelines.comparer.SizeCompare',
        'handler.pipelines.comparer.BinaryCompare',
        'handler.pipelines.comparer.HashCompare',
        'handler.pipelines.comparer.DataCompare'
    )
    """
    Pipeline to compare two files.
    """
    hasher_pipeline = Pipeline(
        ('handler.pipelines.hasher.MD5Hasher', {'full_check': True}),
        ('handler.pipelines.hasher.SHA256Hasher', {'full_check': True}),
    )
    """
    Pipeline to generate hashes from content.
    """
    rename_pipeline = Pipeline(
        'handler.pipelines.renamer.WindowsRenamer'
    )
    """
    Pipeline to rename file when saving. This pipeline can be 
    non-blocking and errors that occur in it will be available through attribute `errors` at 
    `extract_data_pipeline.errors`.
    """

    # Behavior controller for file
    _state = None
    """
    Controller for state of file. The file will be set-up with default state before being loaded or create from stream.
    """
    _actions = None
    """
    Controller for pending actions that file must run. The file will be set-up with default (empty) actions.
    """
    _naming = None
    """
    Controller for renaming restrictions that file must adopt.
    """
    _content = None
    """
    Controller for how the content of file will be handled. 
    """
    _content_files = None
    """
    Controller for how the internal files packet in content of file will be handled.
    """

    # Common Exceptions shortcut
    ImproperlyConfiguredFile = ImproperlyConfiguredFile
    """
    Exception to throw when a required configuration is missing or misplaced.
    """
    ValidationError = ValidationError
    """
    Exception to throw when a required attribute to be save is missing or improperly configured.
    """
    OperationNotAllowed = OperationNotAllowed
    """
    Exception to throw when a operation is no allowed to be performed due to how the options are set-up in `save` 
    method.
    """
    NoInternalContentError = NoInternalContentError
    """
    Exception to throw when file was no internal content or being of wrong type to have internal content.
    """
    ReservedFilenameError = ReservedFilenameError
    """
    Exception to throw when a file is trying to be renamed, but there is already another file with the filename 
    reserved. 
    """

    @classmethod
    def deserialize(cls, source):
        """
        Class method to deserialize the source and return the instance object.
        """
        return cls.serializer.deserialize(source=source)

    def __init__(self, **kwargs):
        """
        Method to instantiate BaseFile. This method can be used for any child class, ony needing
        to change the extract_data_pipeline to be suited for each class.

        Keyword argument `storage` allow to specify a custom file system handler.
        Keyword argument `extract_data_pipeline` allow to specify a custom file extractor pipeline.
        """
        # In order to allow multiple versions of the serialized object to be correctly parsed with
        # the last version we should make conversions of attributes here.
        version = kwargs.pop("__version__", None)
        if version == "1":
            """Do nothing, as version 1 don't have incompatibility with this class version."""

        # Set up storage with default based on operational system
        if not self.storage:
            self.storage = WindowsFileSystem if name == 'nt' else LinuxFileSystem

        additional_kwargs = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                additional_kwargs[key] = value

        # Validate class creation
        if self.extract_data_pipeline is None:
            raise self.ImproperlyConfiguredFile(
                f"{self.__class__.__name__} object must set up a pipeline for data`s extraction."
            )

        # Set up resources used for `save` and `update` methods.
        if not self._actions:
            self._actions = FileActions()

        # Set up resources used for controlling the state of file.
        if not self._state:
            self._state = FileState()

        # Set up metadata of file
        if not self._meta:
            self._meta = FileMetadata()

        # Set up resources used for handling internal files
        if not self._content_files:
            self._content_files = FilePacket()

        # Set up resources used for handling hashes and hash files.
        if not self.hashes:
            self.hashes = FileHashes()
            self.hashes.related_file_object = self

        # Set up resources used for filename renaming control.
        if not self._naming:
            self._naming = FileNaming()
            self._naming.history = []
            self._naming.related_file_object = self

        # Get option to run pipeline.
        run_extractor = additional_kwargs.pop('run_extractor', True)

        # Set up keyword arguments to be used in processor.
        self._keyword_arguments = additional_kwargs

        # Process extractor pipeline. We only run the pipeline if the criterion below is accomplished:
        # It should not come from the serializer (don't have version)
        # and option run_extractor should not be false.
        if version is None and run_extractor:
            self.refresh_from_pipeline()

    def __len__(self):
        """
        Method to inform function `len()` where to extract the information of length from.
        When calling `len(BaseFile())` it will return the size of file in bytes.
        """
        return self.length

    def __lt__(self, other_instance):
        """
        Method to allow comparison < to work between BaseFiles.
        TODO: Compare metadata resolution for when type is image, video and bitrate when type
         is audio and sequence when type is chemical.
        """
        # Check if size is lower than.
        return len(self) < len(other_instance)

    def __le__(self, other_instance):
        """
        Method to allow comparison <= to work between BaseFiles.
        """
        return self.__lt__(other_instance) or self.__eq__(other_instance)

    def __eq__(self, other_instance):
        """
        Method to allow comparison == to work between BaseFiles.
        `other_instance` can be an object or a list of objects to be compared.
        """
        # Run compare pipeline
        try:
            return self.compare_to(other_instance) or False

        except ValueError:
            return False

    def __ne__(self, other_instance):
        """
        Method to allow comparison not equal to work between BaseFiles.
        """
        return not self.__eq__(other_instance)

    def __gt__(self, other_instance):
        """
        Method to allow comparison > to work between BaseFiles.
        TODO: Compare metadata resolution for when type is image, video and bitrate when type
         is audio and sequence when type is chemical.
        """
        # Check if size is greater than.
        return len(self) > len(other_instance)

    def __ge__(self, other_instance):
        """
        Method to allow comparison >= to work between BaseFiles.
        """
        return self.__gt__(other_instance) or self.__eq__(other_instance)

    @property
    def __version__(self):
        """
        Method to indicate the current version of BaseFile in order to allow changes between serialization
        to be handled by `__init__()`
        """
        return "1"

    @property
    def __serialize__(self):
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes = {
            "id",
            "filename",
            "extension",
            "create_date",
            "update_date",
            "_path",
            "_save_to",
            "relative_path",
            "length",
            "mime_type",
            "type",
            "_meta",
            "hashes",
            "_keyword_arguments",
            "storage",
            "serializer",
            "mime_type_handler",
            "uri_handler",
            "extract_data_pipeline",
            "compare_pipeline",
            "hasher_pipeline",
            "rename_pipeline",
            "_state",
            "_actions",
            "_naming",
            "_content_files",
            "__version__"
        }

        return {key: getattr(self, key) for key in attributes}

    @property
    def complete_filename(self):
        """
        Method to return as attribute the complete filename from file.
        """
        return self.filename if not self.extension else f"{self.filename}.{self.extension}"

    @complete_filename.setter
    def complete_filename(self, value):
        """
        Method to set complete_filename attribute. For this method
        to work value must be a tuple of <filename, extension>.
        """
        new_filename, new_extension = value

        # Add current values to history
        if self.filename or self.extension:
            if new_filename == self.filename and new_extension == self.extension:
                # Don`t change filename and extension
                return

            # Remove old filename from reserved filenames
            self._naming.remove_reserved_filename(self.complete_filename)

            # Add old filename to history
            self._naming.history.append((self.filename, self.extension))

        # Set-up new filename (only if it is different from previous one).
        self.filename, self.extension = new_filename, new_extension

        # Only set-up renaming of file if it was saved already.
        if not self._state.adding:
            self._actions.to_rename()

    @property
    def content(self):
        """
        Method to return as attribute the content that can be previous loaded from content,
        or a stream_content or need to be load from file system.
        This method can be override in child class, and it should always return a generator.
        """
        if self._content is None:
            return None

        return iter(self._content)

    @content.setter
    def content(self, value):
        """
        Method to set content attribute. This method can be override in child class.
        This method can receive value as string, bytes or buffer.
        """

        # Storage information if content is being loaded to generator for the first time
        loading_content = self._content is None

        try:
            self._content = FileContent(value, related_file_object=self)

        except ValueError:
            return

        # Update file state to changing only if not adding.
        # Because new content can be changed multiple times, and we not care about
        # how many times it was changed before saving.
        if not self._state.adding and not loading_content:
            self._state.changing = True

        # Update file actions to be saved and hashed.
        self._actions.to_save()
        self._actions.to_hash()

        if self.meta.packed:
            # Update file action to be listed only if file allow listing of content.
            self._actions.to_list()

    @property
    def buffer(self):
        """
        Method to return the current content as buffer to be used for extraction or other code
        that require IO objects.
        """
        if self._content is None:
            return None

        return self._content.content_as_buffer

    @property
    def files(self):
        """
        Method to return as attribute the internal files that can be present in content.
        This method can be override in child class, and it should always return a generator.
        """
        if self._actions.list:
            # Reset internal files' dictionary while keeping historic.
            self._content_files.reset()

            # Extract data from content
            self._content_files.extract_data_pipeline.run(object_to_process=self)

            # Mark as concluded the was_listed option
            self._actions.listed()

        return iter(self._content_files)

    @property
    def is_binary(self) -> [bool, None]:
        """
        Method to return as attribute if file is binary or not. This information is obtained from `is_binary` from
        `FileContent` that should be set-up when data is loaded to content.

        There is no setter method, because the 'binarility' of file is determined by its content.
        """
        try:
            return self._content.is_binary
        except AttributeError:
            return None

    @property
    def is_content_wholesome(self) -> [bool, None]:
        """
        Method to check the integrity of file content given priority to hashes loaded from external source instead of
        generated one. If no hash was loaded from external source, this method will generate new hashes and compare it
        to already existing ones.
        """
        try:
            self.hashes.validate()
        except ValidationError:
            return False
        except ValueError:
            return None

        return True

    @property
    def meta(self):
        """
        Method to return as attribute the file`s metadata class.
        """
        return self._meta

    @property
    def path(self):
        """
        Method to return as attribute full path of file.
        """
        return self._path

    @path.setter
    def path(self, value):
        """
        Method to set property attribute path. This method check whether path is a directory before setting, as we only
        allow path to files to be set-up.
        """
        if value is None:
            raise ValueError("Attribute `path` informed for File cannot be None.")

        self._path = self.storage.sanitize_path(value)

        # Validate if path is really a file.
        if self.storage.is_dir(self._path):
            raise ValueError("Attribute `path` informed for File cannot be a directory.")

    @property
    def save_to(self):
        """
        Method to return as attribute directory where the file should be saved.
        """
        return self._save_to

    @save_to.setter
    def save_to(self, value):
        """
        Method to set property all attributes related to path.
        """

        # We convert the sanitized path to its absolute version to avoid problems when saving.
        self._save_to = self.storage.get_absolute_path(
            self.storage.sanitize_path(value)
        )

        # Validate if path is really a directory. `is_dir` will convert the path to its absolute form before checking
        # it to avoid a bug where `~/` is not interpreted as existing.
        if not self.storage.is_dir(self._save_to):
            raise ValueError("Attribute `save_to` informed for File must be a directory.")

    @property
    def sanitize_path(self):
        """
        Method to return as attribute full sanitized path of file.
        """
        save_to = self.save_to or ""
        relative_path = self.relative_path or ""
        complete_filename = self.complete_filename or ""

        return self.storage.join(save_to, relative_path, complete_filename)

    def add_valid_filename(self, complete_filename, enforce_mimetype=False) -> bool:
        """
        Method to add filename and extension to file only if it has a valid extension.
        This method return boolean to indicate whether a filename and extension was added or not.

        This method will set the complete filename overridden it if already exists.

        The following attributes are set for file:
        - complete_filename (filename, extension)
        - _meta (compressed, lossless, packed)

        TODO: we could change add_valid_filename to also search for extension
         in mime_type of file, case there is any, for more efficient search
         (currently the search in LibraryMimeTyper() regards of checking extension for mimetype or checking extension
         in all extensions is similar in complexity).
        """
        # Check if there is known extension in complete_filename.
        # This method break extract extension from filename and get check if it is valid, returning
        # extension only if it is registered.
        possible_extension = self.mime_type_handler.guess_extension_from_filename(complete_filename)

        if possible_extension:
            # Enforce use of extension that match mimetype if `enforce_mimetype` is True.
            # This will also override self.extension to use a new one still compatible with mimetype.
            if enforce_mimetype and self.mime_type:
                if possible_extension not in self.mime_type_handler.get_extensions(self.mime_type):
                    return False

            # Use first class Renamer declared in pipeline because `prepare_filename` is a class method from base
            # Renamer class, and we don't require any other specialized methods from Renamer children.
            self.complete_filename = self.rename_pipeline[0].prepare_filename(complete_filename, possible_extension)

            # Save additional metadata to file.
            self._meta.compressed = self.mime_type_handler.is_extension_compressed(self.extension)
            self._meta.lossless = self.mime_type_handler.is_extension_lossless(self.extension)
            self._meta.packed = self.mime_type_handler.is_extension_packed(self.extension)

            if self._meta.packed:
                self._actions.to_list()

            return True

        return False

    def compare_to(self, *files: tuple):
        """
        Method to run the pipeline, for comparing files.
        This method set-up for current file object with others.
        """
        if not files:
            raise ValueError("There must be at least one file to be compared in `BaseFile.compare_to` method.")

        # Set the objects_to_compare parameter in processors
        for processor in self.compare_pipeline:
            processor.parameters['objects_to_compare'] = files

        # Run pipeline passing objects to be compared
        self.compare_pipeline.run(object_to_process=self)

        result = self.compare_pipeline.last_result

        if result is None:
            raise ValueError("There is not enough data in files for comparison at `File.compare_to`.")

        return result

    def extract(self):
        """
        Method to extract the content of the file, only if object is packed and extractable.
        """
        if self.meta.packed:
            # Define directory location for extraction of content from path.
            location = self.storage.join(self.save_to, self.filename)
            if self.storage.exists(location):
                location = self.storage.get_renamed_path(path=location)

            # Directly run extractor pipeline by passing method `run`.
            # The method decompress in extractor determine if this package is extractable.
            for processor in self._content_files.extract_data_pipeline:
                try:
                    if processor.decompress(file_object=self, decompress_to=location):
                        return True

                except NotImplementedError:
                    continue

    def generate_hashes(self, force=False):
        """
        Method to run the pipeline, to generate hashes, set-up for the file.
        The parameter `force` will make the pipeline always generate hash from content instead of trying to
        load it from a file when there is one.
        """
        if self._actions.hash:
            # If content is being changed a new hash need to be generated instead of load from hash files.
            try_loading_from_file = False if self._state.changing or force else self._actions.was_saved

            # Reset `try_loading_from_file` in pipeline.
            for processor in self.hasher_pipeline:
                processor.parameters['try_loading_from_file'] = try_loading_from_file

            self.hasher_pipeline.run(object_to_process=self)

            self._actions.hashed()

    def refresh_from_disk(self):
        """
        This method will reset all attributes, calling the pipeline to extract data again from disk.
        Both the content and metadata will be reloaded from disk.
        """
        # Set-up pipeline to extract data from.
        pipeline = Pipeline(
            'handler.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
            'handler.pipelines.extractor.MimeTypeFromFilenameExtractor',
            'handler.pipelines.extractor.FileSystemDataExtractor',
            'handler.pipelines.extractor.HashFileExtractor'
        )

        # Run the pipeline.
        pipeline.run(object_to_process=self, overrider=True, **self._keyword_arguments)

        # Set up its processing state to False
        self._state.processing = False

    def refresh_from_pipeline(self):
        """
        This method will load all attributes, calling the pipeline to extract data. By default, this method will
        not overwrite data already loaded.
        """
        # Call pipeline with keyword_arguments saved in file object
        self.extract_data_pipeline.run(object_to_process=self, **self._keyword_arguments)

        # Mark the file object as run its pipeline for extraction.
        # Set up its processing state to False
        self._state.processing = False

    def save(self, **options):
        """
        Method to save file to file system. In this method we do some validation and verify if file can be saved
        following some options informed through parameter `options`.

        Options available:
        - overwrite (bool) - If file with same filename exists it will be overwritten.
        - save_hashes (bool) - If hash generate for file should also be saved.
        - allow_search_hashes (bool) - Allow hashes to be obtained from hash`s files already saved.
        - allow_update (bool) - If file exists its content will be overwritten.
        - allow_rename (bool) - If renaming a file and a file with the same name exists a new one will be created
        instead of overwriting it.
        - create_backup (bool) - If file exists and its content is being updated the old content will be backup
        before saving.

        This method basically do three things:
        1. Create file and its hashes files (if exists option `overwrite` must be `True`).
        2. Update content if was changed (`allow_update` or `create_backup` must be `True` for this method
        to overwrite the content).
        3. Rename filename and its hashes filenames (if new filename already exists in filesystem, `allow_rename`
        must be `True` for this method to change the renaming state).
        """
        # Validate if file has the correct attributes to be saved, because incomplete BaseFile will not be
        # able to be saved. This should verify if there is name, path and content before saving.
        self.validate()

        # Extract options like `overwrite=bool` file, `save_hashes=False`.
        overwrite = options.pop('overwrite', False)
        save_hashes = options.pop('save_hashes', False)
        allow_search_hashes = options.pop('allow_search_hashes', True)
        allow_update = options.pop('allow_update', True)
        allow_rename = options.pop('allow_rename', False)
        allow_extension_change = options.pop('allow_extension_change', True)
        create_backup = options.pop('create_backup', False)

        # If overwrite is False and file exists a new filename must be created before renaming.
        file_exists = self.storage.exists(self.sanitize_path)

        # Verify which actions are allowed to perform while saving.
        if self._state.adding and file_exists and not overwrite:
            raise self.OperationNotAllowed("Saving a new file is not allowed when there is a existing one in path "
                                           "and `overwrite` is set to `False`!")

        if not self._state.adding and self._state.changing and not (allow_update or create_backup):
            raise self.OperationNotAllowed("Update a file content is not allowed when there is a existing one in path "
                                           "and `allow_update` and `create_backup` are set to `False`!")

        if self._state.renaming and file_exists and not (allow_rename or overwrite):
            raise self.OperationNotAllowed("Renaming a file is not allowed when there is a existing one in path "
                                           "and `allow_rename` and `overwrite` is set to `False`!")

        # Check if extension is being change, raise exception if it is.
        if (
                self._state.renaming
                and self._naming.previous_saved_extension is not None
                and self._naming.previous_saved_extension != self.extension
                and not allow_extension_change
        ):
            raise self.OperationNotAllowed("Changing a file extension is not allowed when `allow_extension_change` is "
                                           "set to `False`!")

        # Create new filename to avoid overwrite if allow_rename is set to `True`.
        if self._state.renaming:
            self._naming.on_conflict_rename = allow_rename
            self._naming.rename()

        # Copy current file to be .bak before updating content.
        if self._state.changing and create_backup:
            self.storage.backup(self.sanitize_path)

        # Save file using iterable content if there is content to be saved
        if self._state.adding or self._state.changing:
            self.write_content(self.sanitize_path)

        if save_hashes:
            # Generate hashes, this will only generate hashes if there is a change in content
            # or if it is a new file. If the file was saved before,
            # we will try to find it in a `.<hasher_name>` file instead of generating one.
            self.generate_hashes(force=not allow_search_hashes)
            self.hashes.save(overwrite=True)

        # Get id after saving.
        if not self.id:
            self.id = self.storage.get_path_id(self.sanitize_path)

        # Update BaseFile internal status and controllers.
        self._actions.saved()
        self._actions.renamed()
        self._state.adding = False
        self._state.changing = False
        self._state.renaming = False
        self._naming.previous_saved_extension = self.extension

    def serialize(self):
        """
        Method to serialize the current object using the serializer declared in attribute `serializer`.
        """
        return self.serializer.serialize(source=self)

    def validate(self):
        """
        Method to validate if minimum attributes of file were set to allow saving.
        TODO: This method should be changed to allow more easy override similar to how Django do with `clean`.
        """
        # Check if there is a filename or extension
        if not self.filename and not self.extension:
            raise self.ValidationError("The attribute `filename` or `extension` must be set for the file!")

        # Raise if not save_to is provided.
        if not self.save_to:
            raise self.ValidationError("The attribute `save_to` must be set for the file!")

        # Raise if not content provided.
        if self.content is None:
            raise self.ValidationError("The attribute `content` must be set for the file!")

        # Check if mimetype is compatible with extension
        if self.extension and self.extension not in self.mime_type_handler.get_extensions(self.mime_type):
            raise self.ValidationError("The attribute `extension` is not compatible with the set-up mimetype for the "
                                       "file!")

    def write_content(self, path):
        """
        Method to write content to a given path.
        This method will truncate the file before saving content to it.
        """
        write_mode = 'b' if self.is_binary else 't'

        self.storage.save_file(path, self.content, file_mode='w', write_mode=write_mode)


class ContentFile(BaseFile):
    """
    Class to create a file from an in memory content.
    It can load a file already saved as BaseFile allow it, but is recommended to use `File` instead
    because it will have a more complete pipeline for data extraction.
    a new one from memory using `ContentFile`.
    """

    extract_data_pipeline = Pipeline(
        'handler.pipelines.extractor.FilenameFromMetadataExtractor',
        'handler.pipelines.extractor.MimeTypeFromFilenameExtractor',
        'handler.pipelines.extractor.MimeTypeFromContentExtractor',
    )
    """
    Pipeline to extract data from multiple sources.
    """


class StreamFile(BaseFile):
    """
    Class to create a file from an HTTP stream that has a header with metadata.
    """

    extract_data_pipeline = Pipeline(
        'handler.pipelines.extractor.FilenameFromMetadataExtractor',
        'handler.pipelines.extractor.FilenameFromURLExtractor',
        'handler.pipelines.extractor.MimeTypeFromFilenameExtractor',
        'handler.pipelines.extractor.MimeTypeFromContentExtractor',
        'handler.pipelines.extractor.MetadataExtractor'
    )
    """
    Pipeline to extract data from multiple sources.
    """


class File(BaseFile):
    """
    Class to create a file from an already saved path in filesystem.
    It can create a new file as BaseFile allow it, but is recommended to create
    a new one from memory using `ContentFile`.
    """

    extract_data_pipeline = Pipeline(
        'handler.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
        'handler.pipelines.extractor.MimeTypeFromFilenameExtractor',
        'handler.pipelines.extractor.FileSystemDataExtractor',
        'handler.pipelines.extractor.HashFileExtractor',
    )
    """
    Pipeline to extract data from multiple sources.
    """
