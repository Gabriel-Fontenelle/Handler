from handler.pipelines.renamer import Renamer

from handler.pipelines import ProcessorMixin


__all__ = [
    'FileSystemDataExtracter',
    'FilenameAndExtensionFromPathExtracter',
    'HashFileExtracter',
    'MimeTypeFromFilenameExtracter',
]


class Extracter(ProcessorMixin):
    """
    Base class to be inherent to define class to be used on Extracter pipeline.
    """

    @classmethod
    def extract(cls, file_object):
        """
        Method to extract the information necessary from a file_object.
        This method must be override in child class.
        """
        raise NotImplementedError("Method extract must be overwritten on child class.")

    @classmethod
    def process(cls, *args, **kwargs):
        """
        Method used to run this class on Processor`s Pipeline for Extracting info from Data.
        This method and to_processor() is not need to extract info outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        """
        object_to_process = kwargs.pop('object', args[0])

        try:
            cls.extract(file_object=object_to_process)
        except (ValueError, IOError):
            return False

        return True


class FilenameAndExtensionFromPathExtracter(Extracter):
    """
    Class that define the extraction of data from `path` defined in file_object.
    """

    @classmethod
    def extract(cls, file_object):
        """
        Method to extract the filename and extension information from attribute `path` of file_object.

        This method will required that the following attributes be set-up in `file_object`:
        - path

        This method will save data in the following attributes of `file_object`:
        - path (sanitized path)
        - filename
        - extension
        """
        if not file_object.path:
            raise ValueError(
                "Attribute `path` must be settled before calling `FilenameAndExtensionFromPathExtracter.extract`."
            )

        file_system_handler = file_object.file_system_handler

        # Sanitize path
        file_object.path = file_system_handler.sanitize_path(file_object.path)

        # Get complete filename from path
        complete_filename = file_system_handler.get_filename_from_path(file_object.path)

        # Check if there is any extension in complete_filename
        if '.' in complete_filename:
            # Check if there is known extension in complete_filename
            possible_extension = file_object.mime_type_handler.guess_extension_from_filename(complete_filename)
            if possible_extension:
                # Use base class Renamer because prepare_filename is a class method and we don't require any other
                # specialized methods from Renamer children.
                file_object.filename, file_object.extension = Renamer.prepare_filename(complete_filename,
                                                                                       possible_extension)

                return

        # No extension registered found, so we set extension as empty.
        file_object.filename = complete_filename
        file_object.extension = ''


class FileSystemDataExtracter(Extracter):

    @classmethod
    def extract(cls, file_object):
        """
        Method to extract the file system information related a file_object.

        This method will required that the following attributes be set-up in `file_object`:
        - path

        This method will save data in the following attributes of `file_object`:
        - id
        - length
        - create_date
        - update_date
        - content (_content_buffer)
        """
        if not file_object.path:
            raise ValueError("Attribute `path` must be settled before calling `FileSystemDataExtracter.extract`.")

        file_system_handler = file_object.file_system_handler

        # Check if path exists
        if not file_system_handler.exists(file_object.path):
            raise IOError("There is no file following attribute `path` in the file system.")

        # Check if path is directory, it should not be
        if file_system_handler.is_dir(file_object.path):
            raise ValueError("Attribute `path` in `file_object` must be a file not directory.")

        # Get path id
        file_object.id = file_system_handler.get_path_id(file_object.path)

        # Get path size
        file_object.length = file_system_handler.get_size(file_object.path)

        # Get created date
        file_object.create_date = file_system_handler.get_created_date(file_object.path)

        # Get last modified date
        file_object.update_date = file_system_handler.get_modified_date(file_object.path)

        # Get content buffer
        file_object.content = file_system_handler.open_file(file_object.path)


class HashFileExtracter(Extracter):
    """
    Class that define the extraction of data from hash files for hashers' processors defined in file_object.
    """

    @classmethod
    def extract(cls, file_object, *args, **kwargs):
        """
        Method to extract the hash information from a hash file related to file_object.

        This method use as kwargs `full_check: bool` that determine if `CHECKSUM` file should
        also be searched.

        This method will required that the following attributes be set-up in `file_object`:
        - path

        This method will save data in the following attributes of `file_object`:
        - hasher
        """
        if not file_object.path:
            raise ValueError("Attribute `path` must be settled before calling `HashFileExtracter.extract`.")

        full_check = kwargs.pop('full_check', False)

        for processor in file_object.hasher_pipeline:
            hasher = processor.classname

            # Extract from hash file and save to hasher if hash file content found.
            hasher.process_from_file(object=file_object, full_check=full_check)


class MimeTypeFromFilenameExtracter(Extracter):
    """
    Class that define the extraction of mimetype data from filename defined in file_object.
    """

    @classmethod
    def extract(cls, file_object):
        """
        Method to extract the mimetype information from a file_object.

        This method will required that the following attributes be set-up in `file_object`:
        - extension

        This method will save data in the following attributes of `file_object`:
        - mime_type
        - type
        - _meta (compressed, lossless)
        """
        # Check if already is a extension and mimetype, if exists do nothing.
        if file_object.mime_type:
            return

        # Check if there is a extension for file else is not possible to extract metadata from it.
        if not file_object.extension:
            raise ValueError(
                "Attribute `extension` must be settled before calling `MimeTypeFromFilenameExtracter.extract`."
            )

        # Save in file_object mimetype and type obtained from mime_type_handler.
        file_object.mime_type = file_object.mime_type_handler.get_mimetype(file_object.extension)
        file_object.type = file_object.mime_type_handler.get_type(file_object.mime_type, file_object.extension)

        # Save additional metadata to file.
        file_object.add_metadata(
            'compressed',
            file_object.mime_type_handler.is_extension_compressed(file_object.extension)
        )
        file_object.add_metadata(
            'lossless',
            file_object.mime_type_handler.is_extension_lossless(file_object.extension)
        )

