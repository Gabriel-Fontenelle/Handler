# first-party
from io import BufferedIOBase
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
    _content_buffer = None
    """
    Loaded buffer to content of file
    """
    _binary_content = False
    """
    Content's flag to indicate if is binary or not. 
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

        if self._content and self._content_buffer:
            raise ReferenceError("Couldn't determine which content to use, both `_content` and `_content_buffer` are "
                                 "available.")

        if not (self._content and self._content_buffer):
            raise ValueError("There is no content to use, both `_content` and `_content_buffer` are empty.")

        if self._content:

            for block in iter(self._content):
                yield block

        elif self._content_buffer:

            # Read content in blocks until end of file and return blocks as iterable elements
            while True:
                block = self._content_buffer.read(self._block_size)

                if block is None or block is b'':
                    break

                yield block

    @content.setter
    def set_content(self, value):
        """
        Method to set content attribute. This method can be override in child class.
        This method can receive value as string, bytes or buffer.
        """
        if isinstance(value, (str, bytes)):
            # Add content as whole value
            self._content = value
            self._binary_content = isinstance(value, bytes)

        elif isinstance(value, BufferedIOBase):
            # Add content as buffer
            self._content_buffer = value

        else:
            raise ValueError(f"parameter `value` informed in property content is not a valid type {type(value)}")

    @property
    def is_packed(self):
        """
        Method to return as attribute if file is compressed or is a package with other files within.
        """
        return self._meta.get('compressed', False) or bool(self._list_internal_content)

    @property
    def is_binary(self):
        """
        Method to return as attribute if file is binary or not. This information is obtain from `_binary_content`
        that should be set-up when data is loaded to content.
        """
        return self._binary_content

    def add_metadata(self, key, value):
        """
        Method to add a value to a key. It will replace existing key in metadata attribute `_meta`.
        """
        if self._meta is None:
            self._meta = {key: value}
            return

        self._meta[key] = value






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
        pass
        # Check if extension is being change, raise if its

        # Set to rename=True

        # Use property to set and get filename, this logic of rename should
        # be inside the set filename and get filename should return the last name.
        # Add a lock and dict that reserves the name for all objects of BaseFile.


    def save(self, hashes=None):
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
