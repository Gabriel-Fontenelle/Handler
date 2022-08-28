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
`handler <at> gabrielfontenelle.com` can be used.
"""
from tinytag import TinyTag

from .extractor import Extractor

__all__ = [
    'AudioMetadataFromContentExtractor',
    'CompressedFilesFromContentExtractor',
]


class MastrokaFilesFromContentExtractor(Extractor):
    stopper = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """


class PSDLayersFromContentExtractor(Extractor):
    stopper = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """


class CompressedFilesFromContentExtractor(Extractor):
    stopper = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        pass

        # Add internal file as File object to file. The content will be obtained from in memory file content.
        hash_file = object_to_process.__class__(
            path=f"{file_system.join(directory_path, hash_filename)}",
            extract_data_pipeline=Pipeline(
                'handler.pipelines.extracter.FilenameAndExtensionFromPathExtractor',
                'handler.pipelines.extracter.MimeTypeFromFilenameExtractor',
                'handler.pipelines.extracter.FileSystemDataExtractor'
            ),
            file_system_handler=file_system
        )

        file_object.meta.packed = True


class VideoMetadataFromContentExtractor(Extractor):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract additional metadata information from content.
        """


class ImageMetadataFromContentExtractor(Extractor):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract additional metadata information from content.
        """


class AudioMetadataFromContentExtractor(Extractor):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract additional metadata information from content.
        """
        # Use tinytag to get additional metadata.
        if not file_object.content:
            raise ValueError(
                "Attribute `content` must be settled before calling `AudioMetadataFromContentExtractor.extract`!"
            )
        if not len(file_object):
            raise ValueError(
                "Length for file's object must set before calling `AudioMetadataFromContentExtractor.extract`!"
            )

        # Reset buffer to initial location
        if file_object._content.buffer.seekable():
            file_object._content.buffer.seek(0)

        tinytag = TinyTag(file_object._content.buffer, len(file_object))
        tinytag.load(tags=True, duration=True, image=False)
        # Same as code in tinytag, it turn default dict into dict so that it can throw KeyError
        tinytag.extra = dict(tinytag.extra)

        attributes_to_extract = [
            'album',
            'albumartist',
            'artist',
            'audio_offset',
            'bitrate',
            'channels',
            'comment',
            'composer',
            'disc',
            'disc_total',
            'duration',
            'extra',
            'genre',
            'samplerate',
            'title',
            'track',
            'track_total',
            'year'
        ]
        for attribute in attributes_to_extract:
            tinytag_attribute = getattr(tinytag, attribute, None)
            if tinytag_attribute and (not getattr(file_object.meta, attribute, None) or overrider):
                setattr(file_object.meta, attribute, tinytag_attribute)

        # Reset buffer to initial location
        if file_object._content.buffer.seekable():
            file_object._content.buffer.seek(0)
