# first-party
from os import name
from os.path import (
    basename,
    dirname,
    join
)

# modules
from handler.pipelines.extracter import (
    ExtensionAndMimeTypeFromContentExtracter,
    ExtensionAndMimeTypeFromFilenameExtracter,
    FileSystemDataExtracter,
    HashFileExtracter,
    MetadataExtracter,
)

from handler.mimetype import LibraryMimeTyper
from handler.pipelines.comparer import (
    DataCompare,
    HashCompare,
    SizeCompare
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
    content = None
    """
    Loaded content of file
    """
    _stream_content = None
    """
    Streamer pointer of content
    """
    list_internal_content = None
    """
    list of items in compressed file
    """

    # Metadata data
    length = 0
    """
    size of file content
    """
    list_internal_content_length = None
    """
    list of length for items in compressed file
    """
    mimetype = None
    """
    File`s mime type
    """
    _meta = None
    """
    Additional metadata info that file can have
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

    filename_history = None
    """
    list of filename previously associated with file
    """
    to_rename = None


    # Meta data

    hashes = None
    """
    file generated or loaded hashes
    """

    # Processors
    file_system_handler = FileSystem
    """
    File system handler to be used for most of files.
    """
    mimetype_handler = FileMimeTypeGuesser
    """
    Mimetype handler that defines the source of know Mimetypes.
    This is used to identify mimetype from extension and vice-verse.
    """

    # Pipeline to rename (Validate if class inherent from Renamer)
    # Pipeline to comparer
    # Pipeline for hashes (Generate hashes from content)
    # Pipeline to extract data
    # Pipeline to compact or extract file
    # Pipelines
    extract_data_pipeline = Pipeline(

    )
    rename_pipeline = Pipeline(
        WindowsRenamer.to_processor(stopper=True)
    )
    compare_pipeline = Pipeline(
        SizeCompare.to_processor(),
        HashCompare.to_processor(),
        DataCompare.to_processor()
    )
    hasher_pipeline = Pipeline(

    )

    # Behavior controler for save
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

    def __init__(self, file_system_handler=None, **kwargs):
        """

        """

        if not file_system_handler:
            # Choose file system from os.plataform
            pass

        # Set attributes from kwargs.

            # If content is not a stream, convert to stream and add to _stream_content.

            # If path provided user should use from_disk to load, else save will save with new name

            # attributes will be in two list, hashes` list or __dict__

        # Set behavior from attributes.

    # TODO: Create magic method to set hashes

    @classmethod
    def from_content(cls):
        pass

    @classmethod
    def from_disk(cls):
        pass

    @property
    def complete_filename(self):
        """
        Method to return as attribute the complete filename from file.
        """
        return self.filename if self.extension is None else f"{self.filename}.{self.extension}"

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
    def filename(self):
        pass




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
        ExtensionAndMimeTypeFromFilenameExtracter.to_processor(),
        ExtensionAndMimeTypeFromContentExtracter.to_processor(),
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
        pass


class StreamFile(BaseFile):

    extract_data_pipeline = Pipeline(
        ExtensionAndMimeTypeFromFilenameExtracter.to_processor(),
        ExtensionAndMimeTypeFromContentExtracter.to_processor(),
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

    @content.setter
    def set_content(self, value):
        """
        Method to set content attribute from stream. `value` should be stream buffer.
        """
        pass


class File(BaseFile):

    extract_data_pipeline = Pipeline(
        ExtensionAndMimeTypeFromFilenameExtracter.to_processor(),
        FileSystemDataExtracter.to_processor(),
        HashFileExtracter.to_processor(),
    )
    """
    Pipeline to extract data from multiple sources.
    """

    def __init__(self, path):
        # Init content from file system
        """

        """

        # From path check if file exists

        # populate file data as size, name, create_date, update_date

        # Check if valid extension and has mimetype

        # Populate _pointer_content

        # Extract hash from hash files if there are any.





        if not file_system_handler:
            # Choose file system from os.plataform
            pass

        # Set attributes from kwargs.

            # If content is not a stream, convert to stream and add to _stream_content.

            # If path provided user should use from_disk to load, else save will save with new name

            # attributes will be in two list, hashes` list or __dict__

        pass

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
    separator = sep

    use_relative_path = False

    def __init__(self, **kwargs):
        

        self.set_initial_data()

        if request:
            self.request = request #Request object, method __extract_data_from_request will test if request is instance of Request

            #Get attributes of file from request
            self.__extract_data_from_request()

    @classmethod
    def from_file(cls, file_path, load_hashes=[]):
        """ Method to instancialize file object from file.
            This method is a alternative init and must be used as follow:
            File.from_file(file_path)

        """
        file_object = File()  # Create file object without request
        file_object.set_complete_path(file_path)
        file_object.__extract_data_from_file_path()

        if load_hashes:
            file_handler = FileHandler(overwrite=False, rename=False)
            file_handler.load_hashes(file_object, load_hashes)

        return file_object

    @classmethod
    def from_content(cls, content, filename, extension):
        """ Method to instancialize file object from content.
            This method is a alternative init and must be used as follow:
            File.from_content(content, mime_type, extension)
        """
        file_object = File()  # Create file object without request
        file_object.__extract_data_from_content(content, filename, extension)

        return file_object

    @classmethod
    def from_request(cls, request):
        pass


    def __extract_data_from_request(self):
        extractor = RequestExtractor(self.request)

        self.complete_filename = extractor.get_complete_filename()
        self.filename = extractor.get_filename()
        self.extension = extractor.get_extension()
        self.mimetype = extractor.get_mime_type()
        self.relative_path = extractor.get_path()
        self.set_hash('md5', self.request.get_MD5())
        self.length = self.request.get_length()

    def __extract_data_from_file_path(self):
        self.complete_filename = basename(self.complete_path)

        filename = self.complete_filename.rsplit('.', 1)

        self.filename = filename[0]
        self.extension = filename[1]
        self.mimetype = MimetypeExtractor.guess_mimetype_from_extension(self.extension)
        self.path = dirname(self.complete_path)
        self.length = FileSystemHandler.get_size(self.complete_path)

        self.use_relative_path = False

        self.separator = sep

    def __extract_data_from_content(self, content, filename, extension):
        self.complete_filename = filename + '.' + extension
        self.filename = filename
        self.extension = extension

        self.length = len(content)
        self.mimetype = MimetypeExtractor.guess_mimetype_from_extension(extension)
        self.write_mode = 'w'



    def set_initial_data(self):
        self.path = None
        self.relative_path = None
        self.complete_path = None
        self.complete_path_renamed = None
        self.filename_renamed = None
        self.complete_filename_renamed = None
        self.dir_drive_name_tuple = None
        self.complete_basename = None
        self.hashes = {}
        self.hash_instance = {}
        self.file_pointer = None
        self.request = None
        self.write_mode = 'wb'

    def get_file_location(self):
        return self.path

    def get_mime_type(self):
        return self.mimetype

    def get_extension(self):
        return self.extension

    def get_write_mode(self):
        return self.write_mode

    def get_complete_path(self):
        if self.complete_path is None:

            if not self.complete_basename:
                self.process_path()

            #Add complete filename
            self.complete_path = self.complete_basename + self.complete_filename

        return self.complete_path

    def get_complete_path_updated(self):
        if self.complete_path_renamed is None:
            return self.get_complete_path()

        return self.complete_path_renamed

    def get_complete_filename(self):
        return self.complete_filename

    def get_complete_filename_updated(self):
        if self.complete_filename_renamed is None:
            return self.get_complete_filename()

        return self.complete_filename_renamed

    def get_path_with_drive_splited(self):
        if not self.dir_drive_name_tuple:
            self.process_path()

        return self.dir_drive_name_tuple

    def get_filename_updated(self):
        if self.filename_renamed is None:
            return self.get_filename()

        return self.filename_renamed

    def get_file_pointer(self):
        return self.file_pointer

    def get_hash_instance(self):
        return self.hash_instance

    def get_hash_type_from_instance(self, hash_type):
        return self.hash_instance.get(has_key, None)

    def get_relative_path(self):
        return self.relative_path

    def set_MD5(self, value):
        self.set_hash('md5', value)

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
