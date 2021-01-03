# first-party
from os import name
from os.path import (
    basename,
    dirname,
    join
)

from handler.mimetype import LibraryMimeTyper
from handler.pipelines.comparer import (
    DataCompare,
    HashCompare,
    SizeCompare
)
# modules
from handler.pipelines.extracter import (
    FileSystemDataExtracter,
    FilenameAndExtensionFromPathExtracter,
    FilenameFromMetadataExtracter,
    HashFileExtracter,
    MetadataExtracter,
    MimeTypeFromContentExtracter,
    MimeTypeFromFilenameExtracter,
)
from handler.pipelines.hasher import (
    MD5Hasher,
    SHA256Hasher
)
from .exception import NoInternalContentError
from .handler import LinuxFileSystem, WindowsFileSystem
from .pipelines import Pipeline
from .pipelines.renamer import WindowsRenamer


class BaseFile:
    """
    Base class for handle File. This class will be used in Files of type Image, Rar, etc.
    This class will behave like Django Model with methods save(), delete(), etc.
    """

    # Filesystem data
    id = None
    """
    File`s id in the File System
    """
    filename = None
    """
    Name of file without extension
    """
    extension = None
    """
    Extension of file
    """
    path = None
    """
    Full path to file including filename
    """
    create_date = None
    """
    Datetime when file was created
    """
    update_date = None
    """
    Datetime when file was updated
    """

    # Content data
    _block_size = 256
    """
    Block size of file to be loaded in each step of iterator. 
    """
    _content = None
    """
    Loaded content of file
    """
    _stream_content = None
    """
    Streamer pointer of content
    """
    _pointer_content = None
    """
    Filesystem pointer of content
    """
    _list_internal_content = None
    """
    list of items in compressed file
    """

    # Metadata data
    length = 0
    """
    size of file content
    """
    mime_type = None
    """
    File`s mime type
    """
    type = None
    """
    File's type (e.g. image, audio, video, application)
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

    # Handler
    linux_file_system_handler = LinuxFileSystem
    """
    FileSystem for Linux
    """
    windows_file_system_handler = WindowsFileSystem
    """
    FileSystem for Windows
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





    filename_history = None
    """
    list of filename previously associated with file
    """
    to_rename = None



    # Pipelines
    # Pipeline to extract data
    # Pipeline to compact or extract file
    extract_data_pipeline = None
    """
    Pipeline to extract data from multiple sources. This should be override at child class.
    """
    compare_pipeline = Pipeline(
        SizeCompare.to_processor(),
        HashCompare.to_processor(stopper=True),
        DataCompare.to_processor(stopper=True)
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

    # Behavior controller for save
    should_be_extracted = False # File inside another file should be extract and not saved.
    move_file = False
    save_file = False
    save_hash = False
    rename_file = False
    rename_hash = False
    name_reserves = {}
    """
    Dict of reserved filenames so that the correct file can be renamed
    avoiding overwriting a new file that has the same name as the current file.
    {<directory>:{<current_filename: old_filename>}}
    """

    def __init__(self, *args, **kwargs):
        """
        Method to instantiate BaseFile. This method can be used for any child class, ony needing
        to change the extract_data_pipeline to be suited for each class.

        Keyword argument `file_system_handler` allow to specified a custom file system handler.
        """
        # Set-up current file system.
        self.file_system_handler = kwargs.pop('file_system_handler')

        # Set-up attributes from kwargs
        pass

        if not self.file_system_handler:
            self.file_system_handler = (
                self.windows_file_system_handler
                if name == 'nt'
                else self.linux_file_system_handler
            )

        # Process extractor pipeline
        self.extract_data_pipeline.run(object=self, *args, **kwargs)

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
        self.filename, self.extension = value

    @property
    def complete_file_path(self):
        """
        Method to return as attribute the complete path to file.
        """
        return join(self.path, self.complete_filename)

    @property
    def content(self):
        """
        Method to return as attribute the content that can be previous loaded from content,
        or a stream_content or need to be load from file system.
        This method should be override in child class.
        """
        raise NotImplementedError("Property content should be declared in child class.")

    @content.setter
    def set_content(self, value):
        """
        Method to set content attribute. This method should be override in child class.
        """
        raise NotImplementedError("Setter of property content should be declared in child class.")

    @property
    def is_packed(self):
        # Check if extension is in compressed file list or there are items in _list_internal_content
        pass

    def add_metadata(self, key, value):
        """
        Method to add a value to a key. It will replace existing key in metadata attribute `_meta`.
        """
        if self._meta is None:
            self._meta = {key: value}
            return

        self._meta[key] = value


    def get_size(self):
        raise NotImplementedError()

    def get_content(self):
        raise NotImplementedError()

    def get_iterable_content(self):
        raise NotImplementedError()

    def get_binary_content(self):
        raise NotImplementedError()

    def get_internal_content(self):
        raise NoInternalContentError(f"This file {repr(self)} don't have a internal content.")

    def rename_file(self):
        # Set file to be rename, but don`t rename the actual file
        # until apply is
        pass



    def generate_hashes(self):
        pass

    def compare_file_to(self, file_to_compare):
        pass

    def extract_file(self):
        pass

    def compact_file(self):
        pass

    def rename_file(self):
        pass
        # Rename file with new name
        # Set current_filename to renamed name
        # Add old filename to list of renamers.

    def rename_hashes(self):
        pass

    def save_file(self):
        pass
        # Save file using iterable content to avoid using too much memory.

    def save_hashes(self):
        pass

    def rename(self, filename, extension=None):
        # Check if extension is being change, raise if its

        # Set to rename=True

        # Use property to set and get filename, this logic of rename should
        # be inside the set filename and get filename should return the last name.
        # Add a lock and dict that reserves the name for all objects of BaseFile.


    def save(self, hashes=None):
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

    def validate(self):
        # Check if mimetype condiz with extension

        # Check if hashers registered are really the same for file.

    def update(self):
        # Update content overwritten it, path must exist else raise error.
        # Before updating rename file to .bak and create new file with new content.s
        pass

    def refresh_from_disk(self):
        # Similar to refresh_from_db of Django.
        # it will reload content and metadata from disk.

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

    @property
    def content(self):
        """
        Method to return as attribute the content previously loaded from content.
        """
        if self._content is not None:
            pass

    @content.setter
    def set_content(self, value):
        """
        Method to set content attribute from memory. `value` should be the content in memory or reference to it.
        """
        self._content = value


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

    @property
    def content(self):
        """
        Method to return as attribute the content previously loaded from a stream_content.
        """
        if self._stream_content is not None:
            pass


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

    @property
    def content(self):
        """
        Method to return as attribute the content previously loaded from file system.
        """
        if self._pointer_content is not None:
            pass

    @content.setter
    def set_content(self, value):
        """
        Method to set content attribute from file system. `value` should be a file's pointer.
        """
        pass




class File2:
    """
        TODO:
            [ ] Allow creation of file from remote file system?
    """
    #complete_filename
    #filename
    #extension
    #mimetype

    #filename_renamed
    #complete_filename_renamed

    # Compressed
    # Lossless

    #length
    #hashes = {}
    #request #Request object

    #path
    #relative_path
    #complete_path
    #complete_path_renamed

    #file_pointer
    #hash_instance = {}

    use_relative_path = False

    def __extract_data_from_request(self):
        extractor = RequestExtractor(self.request)

        self.complete_filename = extractor.get_complete_filename()
        self.filename = extractor.get_filename()
        self.extension = extractor.get_extension()
        self.mimetype = extractor.get_mime_type()
        self.relative_path = extractor.get_path()
        self.set_hash('md5', self.request.get_MD5())
        self.length = self.request.get_length()


    def set_initial_data(self):
        self.request = None
        self.write_mode = 'wb'

    def get_write_mode(self):
        return self.write_mode

        return self.filename_renamed

    def get_file_pointer(self):
        return self.file_pointer

    def get_relative_path(self):
        return self.relative_path

    def set_hashes(self, hashes):
        if not isinstance(hashes, dict):
            raise ValueError("hashes must be a instance of dict on set_hashes()")

        self.hashes = hashes

    def set_hash(self, hash_type, value):
        self.hashes[hash_type] = value

    def set_use_relative_path(self, value):
        self.use_relative_path = value is True

    def set_new_filename(self, value):
        self.filename_renamed = value

        self.complete_filename_renamed = "{}.{}".format(value, self.extension)

        if not self.complete_basename:
            self.process_path()

        self.complete_path_renamed = self.complete_basename + self.complete_filename_renamed

    def set_hash_instance(self, hashes):
        if not isinstance(hashes, dict):
            raise ValueError("hashes in set_hash_instance must be a dict.")

        self.hash_instance = hashes

    def set_write_mode(self, mode):
        self.write_mode = mode

    def was_renamed(self):
        return self.filename_renamed is True


class CompactFile(File):
    pass

class Image(File):
    pass
