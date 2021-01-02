from handler.pipelines.renamer import Renamer

from handler.pipelines import ProcessorMixin


__all__ = [
    'HashFileExtracter',
    'FilenameAndExtensionFromPathExtracter',
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
        except ValueError:
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


