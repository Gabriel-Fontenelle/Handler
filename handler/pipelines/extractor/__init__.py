from .extractor import Extractor
from .external_data import (
    FileSystemDataExtractor,
    FilenameAndExtensionFromPathExtractor,
    FilenameFromMetadataExtractor,
    HashFileExtractor,
    MetadataExtractor,
    MimeTypeFromFilenameExtractor,
    FilenameFromURLExtractor,
    PathFromURLExtractor
)
from .content import (
    MimeTypeFromContentExtractor,
    AudioMetadataFromContentExtractor
)

from .package import (
    PackageExtractor,
    SevenZipCompressedFilesFromPackageExtractor,
    RarCompressedFilesFromPackageExtractor,
    ZipCompressedFilesFromPackageExtractor,
    TarCompressedFilesFromPackageExtractor,
)

__all__ = [
    # Parent classes
    "Extractor",
    "PackageExtractor",
    # Parsing from storage
    "FileSystemDataExtractor",
    "FilenameAndExtensionFromPathExtractor",
    "MimeTypeFromFilenameExtractor",
    "HashFileExtractor",
    # Parsing from URL
    "FilenameFromURLExtractor",
    "PathFromURLExtractor",
    # Parsing from Metadata
    "FilenameFromMetadataExtractor",
    "MetadataExtractor",
    # Parsing from Content
    "AudioMetadataFromContentExtractor",
    "MimeTypeFromContentExtractor",
    # Parsing from Package
    "SevenZipCompressedFilesFromPackageExtractor",
    "RarCompressedFilesFromPackageExtractor",
    "TarCompressedFilesFromPackageExtractor",
    "ZipCompressedFilesFromPackageExtractor"
]
