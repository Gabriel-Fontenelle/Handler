from calendar import timegm
from datetime import datetime
from time import strptime, mktime

from handler.pipelines import ProcessorMixin


__all__ = [
    'FileSystemDataExtracter',
    'FilenameAndExtensionFromPathExtracter',
    'FilenameFromMetadataExtracter',
    'HashFileExtracter',
    'MimeTypeFromFilenameExtracter',
]


class Extracter(ProcessorMixin):
    """
    Base class to be inherent to define class to be used on Extracter pipeline.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
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

        The processor for renamer uses only one object that must be settled through first argument
        or through key work `object`.

        """
        object_to_process = kwargs.pop('object', args.pop(0))

        try:
            cls.extract(file_object=object_to_process, *args, **kwargs)
        except (ValueError, IOError):
            return False

        return True


class FilenameAndExtensionFromPathExtracter(Extracter):
    """
    Class that define the extraction of data from `path` defined in file_object.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the filename and extension information from attribute `path` of file_object.

        This method will required that the following attributes be set-up in `file_object`:
        - path

        This method will save data in the following attributes of `file_object`:
        - path (sanitized path)
        - filename
        - extension
        - _meta (compressed, lossless)

        This method make use of overrider.
        """
        if not file_object.path:
            raise ValueError(
                "Attribute `path` must be settled before calling `FilenameAndExtensionFromPathExtracter.extract`."
            )

        # Check if has filename and it can be overwritten
        if not (file_object.filename is None or overrider):
            return

        file_system_handler = file_object.file_system_handler

        # Sanitize path
        file_object.path = file_system_handler.sanitize_path(file_object.path)

        # Get complete filename from path
        complete_filename = file_system_handler.get_filename_from_path(file_object.path)

        # Check if there is any extension in complete_filename
        if '.' in complete_filename:
            # Check if there is known extension in complete_filename

            if file_object.add_valid_filename(complete_filename):
                return

        # No extension registered found, so we set extension as empty.
        file_object.filename = complete_filename
        file_object.extension = ''


class FilenameFromMetadataExtracter(Extracter):
    """
    Class that define the extraction of filename from metadata passed to extract.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary for a file_object from metadata.
        This method will extract filename from `Content-Disposition` if there is one.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition

        This method will save data in the following attributes of `file_object`:
        - filename
        - extension
        - _meta (compressed, lossless, disposition)

        This method make use of overrider.
        """
        # Check if has filename and it can be overwritten
        if not (file_object.filename is None or overrider):
            return

        try:
            content_disposition = MetadataExtracter.get_content_disposition(kwargs['metadata'])

            if not content_disposition:
                return

            # Save metadata disposition as historic
            file_object.add_metadata('disposition', content_disposition)

            candidates = [
                content.strip()
                for content in content_disposition
                if 'filename' in content
            ]

            if not candidates:
                return

            # Make `filename*=` be priority
            candidates.sort()

            filenames = []

            for candidate in candidates:
                # Get indexes of `"`.
                begin = candidate.index('"') + 1
                end = candidate[begin:].index('"')

                # Get filename with help of those indexes.
                complete_filename = candidate[begin:end]

                # Check if filename has a valid extension
                if '.' in complete_filename and file_object.add_valid_filename(complete_filename):
                    return

                if complete_filename:
                    filenames.append(complete_filename)

            file_object.filename = filenames[0]
            file_object.extension = ""

        except KeyError:
            # kwargs has no parameter metadata
            raise ValueError('Parameter `metadata` must be informed as key argument for '
                             '`FilenameFromMetadataExtracter.extract`.')
        except IndexError:
            # filenames has no index 0, so extension was not set-up either, we just need to return.
            return


class FileSystemDataExtracter(Extracter):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the file system information related a file_object.

        This method will required that the following attributes be set-up in `file_object`:
        - path
        - type

        This method will save data in the following attributes of `file_object`:
        - id
        - length
        - create_date
        - update_date
        - content

        This method not make use of overrider. It always override data.
        """

        def generate_content(path, mode):
            """
            Internal function to return a generator for reading the file's content through the file system.
            """
            with file_object.file_system_handler.open_file(path, mode=mode) as f:

                while True:
                    block = f.read(file_object._block_size)

                    if block is None or block is b'':
                        break

                    yield block

        if not file_object.path:
            raise ValueError("Attribute `path` must be settled before calling `FileSystemDataExtracter.extract`.")

        if not file_object.type:
            raise ValueError("Attribute `type` must be settled before calling `FileSystemDataExtracter.extract`.")

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

        # Define mode from file type
        mode = 'r'

        if file_object.type != 'text':
            mode +='b'

        file_object.is_binary = file_object.type == 'text'

        # Get content generator, same as buffer but without needing to use
        # `.read(),` just loop through chunks of content.
        file_object.content = generate_content(file_object.path, mode)


class HashFileExtracter(Extracter):
    """
    Class that define the extraction of data from hash files for hashers' processors defined in file_object.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the hash information from a hash file related to file_object.

        This method use as kwargs `full_check: bool` that determine if `CHECKSUM` file should
        also be searched.

        This method will required that the following attributes be set-up in `file_object`:
        - path

        This method will save data in the following attributes of `file_object`:
        - hasher

        This method make use of overrider.
        """
        if not file_object.path:
            raise ValueError("Attribute `path` must be settled before calling `HashFileExtracter.extract`.")

        full_check = kwargs.pop('full_check', False)

        for processor in file_object.hasher_pipeline:
            hasher = processor.classname

            if hasher in file_object.hashes and file_object.hashes[hasher] and not overrider:
                continue

            # Extract from hash file and save to hasher if hash file content found.
            hasher.process_from_file(object=file_object, full_check=full_check)


class MimeTypeFromFilenameExtracter(Extracter):
    """
    Class that define the extraction of mimetype data from filename defined in file_object.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the mimetype information from a file_object.

        This method will required that the following attributes be set-up in `file_object`:
        - extension

        This method will save data in the following attributes of `file_object`:
        - mime_type
        - type

        This method make use of overrider.
        """
        # Check if already is a extension and mimetype, if exists do nothing.
        if file_object.mime_type and not overrider:
            return

        # Check if there is a extension for file else is not possible to extract metadata from it.
        if not file_object.extension:
            raise ValueError(
                "Attribute `extension` must be settled before calling `MimeTypeFromFilenameExtracter.extract`."
            )

        # Save in file_object mimetype and type obtained from mime_type_handler.
        file_object.mime_type = file_object.mime_type_handler.get_mimetype(file_object.extension)
        file_object.type = file_object.mime_type_handler.get_type(file_object.mime_type, file_object.extension)



class InternalFilesExtracter(Extracter):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        pass


class MimeTypeFromContentExtracter(Extracter):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        This method must be override in child class.
        """
        # Check if already is a extension and mimetype, if exists do nothing.

        # Check if there is a content in file_object, else is not possible to extract the mimetype and extension from
        # it.

        # Check if there is a possible extension and mimetype from content

        # Save in file_object extension and mimetype


class FilenameFromMetadataExtracter(Extracter):

    @classmethod
    def extract(cls, file_object, *args, **kwargs):
        """
        Method to extract the information necessary from a file_object.
        """
        pass
        """
        Method to extract the information necessary from a file_object.
        """
        pass


class MetadataExtracter(Extracter):

    @classmethod
    def extract(cls, file_object):
        """
        Method to extract the information necessary from a file_object.
        """
        pass


class ContentExtracter():
    pass
    # Guess extension from content
    # Guess mimetype from content
    # Get size from content
