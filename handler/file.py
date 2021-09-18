# first-party
import inspect
from io import IOBase
from os import name

from handler.mimetype import LibraryMimeTyper
from handler.pipelines.comparer import (
    BinaryCompare,
    DataCompare,
    HashCompare,
    SizeCompare,
    TypeCompare
)
# modules
from handler.pipelines.extracter import (
    ContentFromSourceExtracter,
    FileSystemDataExtracter,
    FilenameAndExtensionFromPathExtracter,
    FilenameFromMetadataExtracter,
    FilenameFromURLExtracter,
    HashFileExtracter,
    MetadataExtracter,
    MimeTypeFromContentExtracter,
    MimeTypeFromFilenameExtracter,
)
from handler.pipelines.hasher import (
    MD5Hasher,
    SHA256Hasher
)
from .exception import (
    ImproperlyConfiguredFile,
    NoInternalContentError,
    OperationNotAllowed,
    ValidationError
)
from .handler import LinuxFileSystem, WindowsFileSystem, URI
from .pipelines import Pipeline
from .pipelines.renamer import WindowsRenamer, Renamer


__all__ = [
    'ContentFile',
    'DownloadFile',
    'File',
    'StreamFile'
]


class CacheDescriptor:
    """
    Descriptor class to storage data for instance`s cache.
    This class is used for FileHashes._cache.
    """

    def __get__(self, instance, cls=None):
        """
        Method `get` to automatically set-up empty values in a instance.
        """
        if instance is None:
            return self

        res = instance.__dict__['_cache'] = {}
        return res


class FileState:
    """
    Class that store file instance state.
    """

    adding = True
    """
    Indicate whether an object was already saved or not. If true, we will consider this a new, unsaved
    object in the current file`s filesystem.
    """
    renaming = False
    """
    Indicate whether an object is schedule to being renamed in the current file`s filesystem.
    """
    changing = False
    """
    Indicate whether an object has changed or not. If true, we will consider that the current content was
    changed but not saved yet.  
    """


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


class FileActions:
    """
    Class that store file instance actions to be performed.
    """

    save = False
    """
    Indicate whether an object should be saved or not.
    """
    extract = False
    """
    Indicate whether an object should be extracted or not.
    File inside another file should be extract and not saved.
    """
    rename = False
    """
    Indicate whether an object should be renamed or not.
    """
    hash = False
    """
    Indicate whether an object should be hashed or not.
    """
    was_saved = False
    """
    Indicate whether an object was successfully saved.
    """
    was_extracted = False
    """
    Indicate whether an object was successfully extracted.
    """
    was_renamed = False
    """
    Indicate whether an object was successfully renamed.
    """
    was_hashed = False
    """
    Indicate whether an object was successfully hashed.
    """

    def to_extract(self):
        """
        Method to set-up the action of save file.
        """
        self.extract = True
        self.was_extracted = False

    def extracted(self):
        """
        Method to change the status of `to extract` to `extracted` file.
        """
        self.extract = False
        self.was_extracted = True

    def to_save(self):
        """
        Method to set-up the action of save file.
        """
        self.save = True
        self.was_saved = False

    def saved(self):
        """
        Method to change the status of `to save` to `saved` file.
        """
        self.save = False
        self.was_saved = True

    def to_rename(self):
        """
        Method to set-up the action of rename file.
        """
        self.rename = True
        self.was_renamed = False
        pass

    def renamed(self):
        """
        Method to change the status of `to rename` to `renamed` file.
        """
        self.rename = False
        self.was_renamed = True

    def to_hash(self):
        """
        Method to set-up the action of generate hash for file.
        """
        self.hash = True
        self.was_hashed = False

    def hashed(self):
        """
        Method to change the status of `to hash` to `hashed` file.
        """
        self.hash = False
        self.was_hashed = True


class FileHashes:
    """
    Class that store file instance digested hashes.
    """

    _cache = CacheDescriptor()
    """
    Descriptor to storage the digested hashes for the file instance.
    """
    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes.
    """

    def __setitem__(self, hasher_name, value):
        """
        Method to set-up values for file hash as dict item.
        This method expects a tuple as value to set-up the hash hexadecimal value and hash file related
        to the hasher.
        """
        hex_value, hash_file = value

        if not isinstance(hash_file, File):
            raise ImproperlyConfiguredFile("Tuple for hashes must be the Hexadecimal value and a File Object for the "
                                           "hash.")

        self._cache[hasher_name] = hex_value, hash_file

    def __getitem__(self, hasher_name):
        """
        Method to get the hasher value and file associated saved in self._cache.
        """
        return self._cache[hasher_name]

    def rename(self, new_filename):
        """
        This method will rename file for each hash file existing in _caches.
        This method don`t save files, ony prepare the filename and content to be correct before saving it.
        """
        for hasher_name, value in self._cache.items():
            hex_value, hash_file = value

            if not hash_file._meta.checksum:
                # Rename filename if is not `checksum.hasher_name`
                # complete_filename is a property that will set-up additional action to rename the file`s filename if
                # it was already saved before.
                hash_file.complete_filename = new_filename, hasher_name

            # Load content from generator.
            # First we set-up content of type binary or string.
            content = b"" if hash_file.is_binary else ""

            # Then we load content from generator using a loop.
            for block in hash_file.content:
                content += block

            # Change file`s filename inside content of hash file.
            content = content.replace(f"{hash_file.filename}.{hasher_name}", f"{new_filename}.{hasher_name}")

            # Set-up new content after renaming and specify that hash_file was not saved yet.
            hash_file.content = content
            hash_file._actions.to_save()

    def save(self, overwrite=False):
        """
        Method to save all hashes files if it was not saved already.
        """
        if not self.related_file_object:
            raise ImproperlyConfiguredFile("A related file object must be specified for hashes before saving.")

        for hex_value, hash_file in self._cache.values():
            if hash_file._actions.save:
                if hash_file._meta.checksum:
                    # If file is CHECKSUM.<hasher_name> we not allow overwrite.
                    hash_file.save(overwrite=False, allow_update=overwrite)
                else:
                    hash_file.save(overwrite=overwrite, allow_update=overwrite)


class FileNaming:

    reserved_filenames = {}
    """
    Dict of reserved filenames so that the correct file can be renamed
    avoiding overwriting a new file that has the same name as the current file.
    {<directory>:{<current_filename: old_filename>}}
    """

    history = None

    previous_saved_path = None

    _cache = CacheDescriptor()

    on_conflict_rename = False

    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes.
    """

    def rename(self, generate_new_name=False):
        # Get last saved path

        # Check if reserved name. Reserved names cannot be renamed even if overwrite is used in save.

        pass
        # Check if extension is being change, raise if its

        # Set to rename=True

        # Use property to set and get filename, this logic of rename should
        # be inside the set filename and get filename should return the last name.
        # Add a lock and dict that reserves the name for all objects of BaseFile.

        # Rename hash_files if there is any.

        # Apply rename if there is a rename to be made (not saved and file exists on path).
        # Rename also in hashes.

        # Update path of file to reflect new one.


class FileInternalContent:
    _content_list = None
    pass


class BaseFile:
    """
    Base class for handle File. This class will be used in Files of type Image, Rar, etc.
    This class will behave like Django Model with methods save(), delete(), etc.
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

    # Content data
    _block_size = 256
    """
    Block size of file to be loaded in each step of iterator.
    """
    _content_generator = None
    """
    Loaded generator to content of file.
    """
    _binary_content = False
    """
    Content's flag to indicate if is binary or not.
    """
    _internal_content = None
    """
    Descriptor for items in compressed files.
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
    linux_file_system_handler = LinuxFileSystem
    """
    FileSystem for Linux.
    """
    windows_file_system_handler = WindowsFileSystem
    """
    FileSystem for Windows.
    """
    file_system_handler = None
    """
    FileSystem currently in use for File.
    It can be LinuxFileSystem, WindowsFileSystem or a custom one.
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
    Pipeline to extract data from multiple sources. This should be override at child class.
    """
    compare_pipeline = Pipeline(
        TypeCompare.to_processor(stopper=True, stop_value=False),
        SizeCompare.to_processor(stopper=True, stop_value=False),
        BinaryCompare.to_processor(stopper=True, stop_value=False),
        HashCompare.to_processor(stopper=True, stop_value=(True, False)),
        DataCompare.to_processor(stopper=True, stop_value=(True, False))
    )
    """
    Pipeline to compare two files.
    """
    hasher_pipeline = Pipeline(
        MD5Hasher.to_processor(),
        SHA256Hasher.to_processor()
    )
    """
    Pipeline to generate hashes from content.
    """
    rename_pipeline = Pipeline(
        WindowsRenamer.to_processor(stopper=True)
    )
    """
    Pipeline to rename file when saving.
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

    def __init__(self, **kwargs):
        """
        Method to instantiate BaseFile. This method can be used for any child class, ony needing
        to change the extract_data_pipeline to be suited for each class.

        Keyword argument `file_system_handler` allow to specified a custom file system handler.
        Keyword argument `extract_data_pipeline` allow to specified a custom file extractor pipeline.
        """
        # Validate class creation
        if self.extract_data_pipeline is None and not 'extract_data_pipeline' in kwargs:
            raise self.ImproperlyConfiguredFile("File object must set-up a pipeline for data`s extraction.")

        # Set-up current file system.
        self.file_system_handler = kwargs.pop('file_system_handler')

        if not self.file_system_handler:
            self.file_system_handler = (
                self.windows_file_system_handler
                if name == 'nt'
                else self.linux_file_system_handler
            )

        new_kwargs = {}
        # Set-up attributes from kwargs like `file_system_handler` or `path`
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                new_kwargs[key] = value
        self._keyword_arguments = new_kwargs

        # Set-up resources used for `save` and `update` methods.
        self._actions = FileActions()

        # Set-up resources used for controlling the state of file.
        self._state = FileState()

        # Set-up metadata of file
        self._meta = FileMetadata()

        # Set-up resources used for handling hashes and hash files.
        self.hashes = FileHashes()
        self.hashes.related_file_object = self

        # Set-up resources used for filename renaming control.
        self._naming = FileNaming()
        self._naming.history = []
        self._naming.related_file_object = self

        # Set-up resources used for handling internal content.
        self._internal_content = FileInternalContent()

        # Process extractor pipeline
        extract_data_pipeline = kwargs.pop('extract_data_pipeline')
        if extract_data_pipeline:
            self.extract_data_pipeline = extract_data_pipeline

        self.extract_data_pipeline.run(object=self, **new_kwargs)

    def __len__(self):
        """
        Method to inform function `len()` where to extract the information of length from.
        When calling `len(BaseFile())` it will return the size of file in bytes.
        """
        return self.length

    def __lt__(self, other_instance):
        """
        Method to allow comparison < to work between BaseFiles.
        """
        # Check if size is lower than. (or image resolution if Image file or video)
        pass

    def __le__(self, other_instance):
        """
        Method to allow comparison <= to work between BaseFiles.
        """
        return self.__lt__(other_instance) or self.__eq__(other_instance)

    def __eq__(self, other_instance):
        """
        Method to allow comparison == to work between BaseFiles.
        """
        # Run compare pipeline
        try:
            return self.compare_to(other_instance)

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
        """
        # Check if size is greater than. (or image resolution if Image file or video)
        pass
        #getattr(self._meta, self.type.compare)

    def __ge__(self, other_instance):
        """
        Method to allow comparison >= to work between BaseFiles.
        """
        return self.__gt__(other_instance) or self.__eq__(other_instance)

    @property
    def complete_filename(self):
        """
        Method to return as attribute the complete filename from file.
        """
        return self.filename if not self.extension else f"{self.filename}.{self.extension}"

    @complete_filename.setter
    def set_complete_filename(self, value):
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

            self._naming.history.append((self.filename_history, self.extension))

        # Set-up new filename (only if it is different from previous one).
        self.filename, self.extension = value

        # Only set-up renaming of file if it was saved already.
        if not self._state.adding:
            self._actions.to_rename()

    @property
    def content(self):
        """
        Method to return as attribute the content that can be previous loaded from content,
        or a stream_content or need to be load from file system.
        This method can be override in child class and it should always return a generator.
        """
        if not self._content_generator:
            raise ValueError(f"There is no content to use for file {self}.")

        return self._content_generator

    @content.setter
    def set_content(self, value):
        """
        Method to set content attribute. This method can be override in child class.
        This method can receive value as string, bytes or buffer.
        """
        def generator_string_or_bytes(raw_value):
            """
            Generator method to load from memory a string or byte data.
            """
            i = 0

            while i < len(raw_value):
                yield raw_value[i:i+self._block_size]
                i += self._block_size

        def generator_buffer_io(raw_value):
            """
            """
            # Read content in blocks until end of file and return blocks as iterable elements
            while True:
                block = raw_value.read(self._block_size)

                if block is None or block == b'':
                    break

                yield block

            # Reset pointer to initial position in value
            pass

        # Storage information if content is being loaded to generator for the first time
        loading_content = self._content_generator is None

        if isinstance(value, (str, bytes)):
            # Add content as whole value
            self._content_generator = generator_string_or_bytes(value)
            self._binary_content = isinstance(value, bytes)  # Maybe remove it from here.

        elif isinstance(value, IOBase):
            # Add content as buffer
            self._content_generator = generator_buffer_io(value)

        elif inspect.isgenerator(value):
            # Add content as generator
            self._content_generator = value

        else:
            raise ValueError(f"parameter `value` informed in property content is not a valid type {type(value)}")

        # Update file state to changing only if not adding.
        # Because new content can be changed multiple times, and we not care about
        # how many times it was changed before saving.
        if not self._state.adding and not loading_content:
            self._state.changing = True

        # Update file actions to be saved and hashed.
        self._actions.to_save()
        self._actions.to_hash()

    @property
    def is_binary(self) -> bool:
        """
        Method to return as attribute if file is binary or not. This information is obtain from `_binary_content`
        that should be set-up when data is loaded to content.
        """
        return self._binary_content

    @is_binary.setter
    def is_binary(self, value):
        """
        Method to set property attribute is_binary. This information is obtain should be set-up when data is loaded to content.
        """
        self._binary_content = value

    @property
    def path(self):
        """
        Method to return as attribute full path of file.
        """
        return self._path

    @path.setter
    def set_path(self, value):
        """
        Method to set property attribute path. This method check whether path is a directory before setting, as we only
        allow path to files to be set-up.
        """
        self._path = self.file_system_handler.sanitize_path(value)

        # Validate if path is really a file.
        if self.file_system_handler.is_dir(self._path):
            raise ValueError("Attribute `path` informed for File cannot be a directory.")

    @property
    def save_to(self):
        """
        Method to return as attribute directory where the file should be saved.
        """
        return self._save_to

    @save_to.setter
    def set_save_to(self, value):
        """
        Method to set property all attributes related to path.
        """
        self._save_to = self.file_system_handler.sanitize_path(value)

        # Validate if path is really a directory.
        if not self.file_system_handler.is_dir(self._save_to):
            raise ValueError("Attribute `save_to` informed for File must be a directory.")

    @property
    def sanitize_path(self):
        """
        Method to return as attribute full sanitized path of file.
        """
        return self.file_system_handler.sep.join((self.save_to, self.relative_path, self.complete_filename))

    def add_valid_filename(self, complete_filename, enforce_mimetype=False) -> bool:
        """
        Method to add filename and extension to file only if it has a valid extension.
        This method return boolean to indicate whether a filename and extension was added or not.

        This method will set the complete filename overridden it if already exists.

        The following attributes are set for file:
        - complete_filename (filename, extension)
        - _meta (compressed, lossless)

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

            # Use base class Renamer because prepare_filename is a class method and we don't require any other
            # specialized methods from Renamer children.
            self.complete_filename = Renamer.prepare_filename(complete_filename, possible_extension)

            # Save additional metadata to file.
            self._meta.compressed = self.mime_type_handler.is_extension_compressed(self.extension)
            self._meta.lossless = self.mime_type_handler.is_extension_lossless(self.extension)

            return True

        return False

    def compare_to(self, *files):
        """
        Method to run the pipeline, to compare files, set-up for current file object.
        """
        # Add current object to be compared mixed with others in files
        files.append(self)
        # Pass objects to be compared in pipeline
        self.compare_pipeline.run(objects=files)
        result = self.compare_pipeline.last_result

        if result is None:
            raise ValueError("There is not enough data in files for comparison at `File.compare_to`.")

        return result

    def generate_hashes(self):
        """
        Method to run the pipeline, to generate hashes, set-up for the file.
        """
        self.hasher_pipeline.run(object=self, try_loading_from_file=self.was_saved)







    def get_internal_content(self):
        raise NoInternalContentError(f"This file {repr(self)} don't have a internal content.")




    def rename_file(self):
        # Set file to be rename, but don`t rename the actual file
        # until apply is
        pass

    def _rename_file(self):
        pass
        # Rename file with new name
        # Set current_filename to renamed name
        # Add old filename to list of renamers.

        # Rename hashes.

    def _rename_hashes(self):
        pass

    def _save_file(self):
        pass
        # Save file using iterable content to avoid using too much memory.

    def _save_hashes(self):
        pass



    def rename(self, filename, extension=None):
        pass
        # Check if extension is being change, raise if its

        # Set to rename=True

        # Use property to set and get filename, this logic of rename should
        # be inside the set filename and get filename should return the last name.
        # Add a lock and dict that reserves the name for all objects of BaseFile.


    def save(self, options=[]):
        # Options like `overwrite=bool` file, `save_hashes=False`.

        pass
        # Verify if there is name, path and content before saving.
        # Raise exception otherwise.


        # Don`t try to save if file already save (has id) and content not changed.
        # If content changed raise exception to indicate to use update instead of saving.

        # Apply rename if there is a rename to be made (not saved and file exists on path).

        # Save file using iterable content if there is content to be saved

        # Generate hashes from pipeline if hashes are None, else uses hash from hashes.
        # Save hash if there is one and it wasn`t save before
        # Remove from pipeline hashes already settled for file.

        # Get id after saving.

        # Raise if not save_to provided.

        # Raise if extension is None

    def validate(self):
        pass
        # Check if mimetype condiz with extension

        # Check if hashers registered are really the same for file.

    def update(self):
        # Update content overwritten it, path must exist else raise error.
        # Before updating rename file to .bak and create new file with new content.s
        pass

    def refresh_from_disk(self):
        # Similar to refresh_from_db of Django.
        # it will reload content and metadata from disk.

        # Process FileSystemExtracter

        pass


class ContentFile(BaseFile):
    # Changing between type of file should be made by controler.

    extract_data_pipeline = Pipeline(
        FilenameFromMetadataExtracter.to_processor(),
        MimeTypeFromFilenameExtracter.to_processor(),
        MimeTypeFromContentExtracter.to_processor(),
        MetadataExtracter.to_processor()
    )
    """
    Pipeline to extract data from multiple sources.
    """


class StreamFile(BaseFile):

    extract_data_pipeline = Pipeline(
        FilenameFromMetadataExtracter.to_processor(),
        MimeTypeFromFilenameExtracter.to_processor(),
        MimeTypeFromContentExtracter.to_processor(),
        MetadataExtracter.to_processor()
    )
    """
    Pipeline to extract data from multiple sources.
    """


class File(BaseFile):

    extract_data_pipeline = Pipeline(
        FilenameAndExtensionFromPathExtracter.to_processor(),
        MimeTypeFromFilenameExtracter.to_processor(),
        FileSystemDataExtracter.to_processor(),
        HashFileExtracter.to_processor(),
    )
    """
    Pipeline to extract data from multiple sources.
    """

    # This save must overwrite file.

    # Stream or content are for downloading files.
