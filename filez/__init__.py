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

from .exception import (
    ImproperlyConfiguredFile,
    NoInternalContentError,
    OperationNotAllowed,
    ReservedFilenameError,
    ValidationError,
)
from .file import BaseFile, File, ContentFile, StreamFile
from .handler import System, URI
from .mimetype import LibraryMimeTyper, APIMimeTyper
# Module with classes that define the pipelines and its processors classes.
# A Pipeline is a sequence that loop processors to be run.
from .pipelines import Processor, Pipeline
# Module with pipeline classes for comparing Files.
from .pipelines.comparer import (
    Comparer,
    BinaryCompare,
    DataCompare,
    HashCompare,
    LousyNameCompare,
    MimeTypeCompare,
    NameCompare,
    SizeCompare,
    TypeCompare
)
# Module with pipeline classes for extracting data for files from multiple sources.
from .pipelines.extractor import (
    Extractor,
    PackageExtractor,
    FileSystemDataExtractor,
    FilenameAndExtensionFromPathExtractor,
    MimeTypeFromFilenameExtractor,
    HashFileExtractor,
    FilenameFromURLExtractor,
    PathFromURLExtractor,
    FilenameFromMetadataExtractor,
    MetadataExtractor,
    SevenZipCompressedFilesFromPackageExtractor,
    AudioMetadataFromContentExtractor,
    RarCompressedFilesFromPackageExtractor,
    ZipCompressedFilesFromPackageExtractor,
    MimeTypeFromContentExtractor
)
# Module with pipeline classes for generating or extracting hashed data related to file.
from .pipelines.hasher import Hasher, CRC32Hasher, MD5Hasher, SHA256Hasher
# Module with pipeline classes for renaming files.
from .pipelines.renamer import Renamer, WindowsRenamer, LinuxRenamer, UniqueRenamer
# Module with classes for serializing/deserializing objects.
from .serializer import PickleSerializer, JSONSerializer
from .storage import WindowsFileSystem, LinuxFileSystem, Storage

__all__ = [
    'APIMimeTyper', 'AudioMetadataFromContentExtractor', 'BaseFile', 'BinaryCompare',
    'Comparer', 'PackageExtractor', 'ContentFile', 'CRC32Hasher', 'DataCompare',
    'Extractor', 'File', 'FileSystemDataExtractor', 'FilenameAndExtensionFromPathExtractor',
    'FilenameFromMetadataExtractor', 'FilenameFromURLExtractor', 'HashCompare', 'HashFileExtractor',
    'Hasher', 'ImageEngine', 'ImproperlyConfiguredFile', 'JSONSerializer', 'LibraryMimeTyper',
    'LinuxFileSystem',  'LinuxRenamer', 'LousyNameCompare', 'MD5Hasher',
    'MetadataExtractor', 'MimeTypeCompare', 'MimeTypeFromContentExtractor',
    'MimeTypeFromFilenameExtractor', 'NameCompare', 'NoInternalContentError', 'OpenCVImage',
    'OperationNotAllowed', 'PathFromURLExtractor', 'PickleSerializer', 'PillowImage', 'Pipeline',
    'Processor', 'RarCompressedFilesFromPackageExtractor', 'Renamer', 'ReservedFilenameError',
    'SHA256Hasher', 'SevenZipCompressedFilesFromPackageExtractor',
    'SizeCompare', 'Storage', 'StreamFile', 'System', 'TypeCompare', 'URI', 'UniqueRenamer',
    'ValidationError', 'WandImage', 'WindowsFileSystem', 'WindowsRenamer',
    'ZipCompressedFilesFromPackageExtractor',
]
