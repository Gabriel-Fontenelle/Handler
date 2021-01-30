# first-party
import mimetypes
from os.path import dirname, realpath, join

__all__ = [
    'LibraryMimeTyper',
    'APIMimeTyper'
]


class BaseMimeTyper:
    """
    Base class for handle MimeType. This call works mostly as common interface that must be overwritten to allow easy
    abstraction of methods to get extensions and mimetypes from distinct sources. Those sources can be from a library
    that save data on files, API or direct from databases.
    """

    @property
    def lossless_mimetypes(self):
        """
        Method to return as attribute the mimetypes that are for lossless encoding.
        This method should be override in child class.
        """
        raise NotImplementedError("lossless_mimetypes() method must be overwritten on child class.")

    @property
    def lossless_extensions(self):
        """
        Method to return as attribute the extensions that are for lossless encoding.
        This method should be override in child class.
        """
        raise NotImplementedError("lossless_extensions() method must be overwritten on child class.")

    @property
    def compressed_mimetypes(self):
        """
        Method to return as attribute the mimetypes that are for containers of compression.
        This method should be override in child class.
        """
        raise NotImplementedError("compressed_mimetypes() method must be overwritten on child class.")

    @property
    def compressed_extensions(self):
        """
        Method to return as attribute the extensions that are for containers of compression.
        This method should be override in child class.
        """
        raise NotImplementedError("compressed_extensions() method must be overwritten on child class.")

    def get_extensions(self, mimetype):
        """
        Method to get all registered extensions for given mimetype.
        This method should be override in child class.
        """
        raise NotImplementedError("get_extensions() method must be overwritten on child class.")

    def get_mimetype(self, extension):
        """
        Method to get registered mimetype for given extension.
        This method should be override in child class.
        """
        raise NotImplementedError("get_mimetype() method must be overwritten on child class.")

    def get_type(self, mimetype=None, extension=None):
        """
        Method to get the associated type for the given mimetype or extension.
        This method should be override in child class.
        """
        raise NotImplementedError("get_mimetype() method must be overwritten on child class.")

    def guess_extension_from_mimetype(self, mimetype):
        """
        Method to get the best extension for given mimetype in case there are more than one extension
        available.
        This method should be override in child class.
        """
        raise NotImplementedError("guess_extension() method must be overwritten on child class.")

    def guess_extension_from_filename(self, filename):
        """
        Method to get the best extension for given filename in case there are more than one extension
        available using as base the filename that can or not have a registered extension in it.
        This method should be override in child class.
        """
        raise NotImplementedError("guess_extension_and_mimetype() method must be overwritten on child class.")

    def is_extension_registered(self, extension):
        """
        Method to check if a extension is registered or not in list of mimetypes and extensions.
        This method should be override in child class.
        """
        raise NotImplementedError("is_extension_registered() method must be overwritten on child class.")

    def is_extension_lossless(self, extension):
        """
        Method to check if a extension is related to a lossless file type or not.
        """
        return extension in self.lossless_extensions

    def is_mimetype_lossless(self, mimetype):
        """
        Method to check if a mimetype is related to a lossless file type or not.
        """
        return mimetype in self.lossless_mimetypes

    def is_extension_compressed(self, extension):
        """
        Method to check if a extension is related to a file that is container of compression or not.
        """
        return extension in self.compressed_extensions

    def is_mimetype_compressed(self, mimetype):
        """
        Method to check if a mimetype is related to a file that is container of compression or not.
        """
        return mimetype in self.compressed_mimetypes


class LibraryMimeTyper(BaseMimeTyper):
    """
    Class for handling MimeTypes using the mimetypes library of python. This class will load its mimetype
    from an updated `mime.types` file in data directory.
    """

    _known_mimetypes_file = join(dirname(realpath(__file__)), 'data', 'mime.types')
    """
    Path of file `mime.types` to be loaded of known mimetypes.
    """

    def __init__(self):
        """
        Method that instantiate the mimetype library and load to it the file of known mimetypes.
        It will output a IOError, that must be caught in stack above, if file don't exists.
        """
        mimetypes.init()
        mimetypes.read(self._known_mimetypes_file, strict=True)

    @property
    def lossless_mimetypes(self):
        """
        Method to return as attribute the mimetypes that are for lossless encoding.
        """
        return [
            'audio/mp4',
            'audio/x-caf',
            'audio/x-flac',
            'audio/x-ms-wma',
            'audio/x-oma',
            'audio/x-pn-realaudio',
            'audio/x-wav',
            'image/raw',
            'video/raw',
        ]

    @property
    def lossless_extensions(self):
        """
        Method to return as attribute the extensions that are for lossless encoding.
        """
        return [
            '3fr',
            'aa3',
            'ari',
            'arw',
            'at3',
            'at9',
            'avif',
            'bay',
            'braw',
            'bz2',
            'caf',
            'cap',
            'cr2',
            'cr3',
            'crw',
            'data',
            'dcr',
            'dcs',
            'dng',
            'drf',
            'eip',
            'erf',
            'fff',
            'flac',
            'flif',
            'gpr',
            'iiq',
            'k25',
            'kdc',
            'm4a',
            'mdc',
            'mef',
            'mlp',
            'mos',
            'mp4a',
            'mrw',
            'nef',
            'nrw',
            'obm',
            'oma',
            'orf',
            'osq',
            'pef',
            'ptx',
            'pxn',
            'r3d',
            'raf',
            'raw',
            'rw2',
            'rwl',
            'rwz',
            'sr2',
            'srf',
            'srw',
            'tif',
            'wav',
            'x3f',
        ]

    @property
    def compressed_mimetypes(self):
        """
        Method to return as attribute the mimetypes that are for containers of compression.
        """
        return [
            'application/cz',
            'application/epub+zip',
            'application/gzip',
            'application/java-archive',
            'application/rar',
            'application/vnd.apple.installer+xm',
            'application/vnd.ezpix-album',
            'application/vnd.ezpix-package',
            'application/x-cbr',
            'application/x-debian-package',
            'application/x-dgc-compressed',
            'application/x-gtar',
            'application/x-gzip',
            'application/x-rar',
            'application/x-rar-compressed',
            'application/x-tar',
            'application/zip',
            'application/zlib',
        ]

    @property
    def compressed_extensions(self):
        """
        Method to return as attribute the extensions that are for containers of compression.
        """
        return [
            'abr',
            'cb7',
            'cba',
            'cbr',
            'cbt',
            'cbz'
            'cz',
            'deb',
            'dgc',
            'ez2',
            'ez3',
            'gtar',
            'gz',
            'jar',
            'mpkg',
            'msi',
            'rar',
            'tar',
            'zip',
        ]

    def get_extensions(self, mimetype):
        """
        Method to get all registered extensions for given mimetype.
        Because mimetypes.guess_all_extensions return extensions with dot in the begin we should remove it from
        extensions.
        """
        return [extension[1:] for extension in mimetypes.guess_all_extensions(mimetype, False)]

    def get_mimetype(self, extension):
        """
        Method to get registered mimetype for given extension.
        """
        return mimetypes.types_map.get('.' + extension, None)

    def get_type(self, mimetype=None, extension=None):
        """
        Method to get the associated type for the given mimetype or extension.
        """
        if not (mimetype and extension):
            raise ValueError("mimetype or extension must be informed at LibraryMimeTyper.get_type.")

        # Set-up list of types available from file `mime.types` as a set.
        known_types = set(
            [
                'application',
                'audio',
                'binary',
                'chemical',
                'image',
                'interface',
                'message',
                'model',
                'multipart',
                'text',
                'video',
                'x-conference',
            ]
        )
        if extension and not mimetype:
            mimetype = self.get_mimetype(extension)

        if not mimetype:
            return None

        # Get set from mimetype using a list of first element before `/` in mimetype.
        possible_type = set(mimetype.split('/', 1)[:1])

        return possible_type[0] if possible_type.intersection(known_types) else None

    def guess_extension_from_mimetype(self, mimetype):
        """
        Method to get the best extension for given mimetype in case there are more than one extension
        available.
        As extensions are getted from file that storage ony extensions and mimetype there is way to tell
        which one if better suited for the mimetype, so we return the first one. Except for jpg, we return it instead
        of jpe and alternatives.
        """
        extensions = self.get_extensions(mimetype)

        if not extensions:
            return None

        # Fix for jpe being returned instead of jpg.
        if 'jpg' in extensions:
            return 'jpg'
        if 'mp4' in extensions:
            return 'mp4'

        return extensions[0]

    def guess_extension_from_filename(self, filename):
        """
        Method to get the best extension for given filename in case there are more than one extension
        available using as base the filename that can or not have a registered extension in it.
        """
        splitted = filename.rsplit('.', 1)
        maybe_extension = splitted[int(len(splitted) == 2)]

        if maybe_extension and self.is_extension_registered(maybe_extension):
            return maybe_extension

        return None

    def is_extension_registered(self, extension):
        """
        Method to check if a extension is registered or not in list of mimetypes and extensions.
        """
        return bool(self.get_mimetype(extension))


class APIMimeTyper(BaseMimeTyper):
    """
    Class for handling MimeTypes using an external API. This class should use a cache to avoid consuming the API
    every time that a mimetype or extension must be guessed.

    TODO: Override BaseMimeTyper methods with methods that call a external API.
    """
