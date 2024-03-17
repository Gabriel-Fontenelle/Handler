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
from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Any

from .extractor import Extractor
from ...image import WandImage
from ...video import MoviePyVideo

if TYPE_CHECKING:
    from fitz import Document
    from ...file import BaseFile


__all__ = [
    'AudioMetadataFromContentExtractor',
    'DocumentMetadataFromContentExtractor',
    'MimeTypeFromContentExtractor',
    'VideoMetadataFromContentExtractor',
]


class VideoMetadataFromContentExtractor(Extractor):
    """
    Extractor class created for extracting metadata contained in videos using MoviePy.
    This class don't validate any extensions to see if it's video, so any exception that this class output will
    be caught only in stack above.
    """

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> None:
        """
        Method to extract additional metadata information from content.
        """
        # Use MoviePy to get additional metadata.
        if not file_object.content:
            raise ValueError(
                "Attribute `content` or `content_as_buffer` must be settled before calling "
                "`VideoMetadataFromContentExtractor.extract`!"
            )
        if not len(file_object):
            raise ValueError(
                "Length for file's object must set before calling `VideoMetadataFromContentExtractor.extract`!"
            )

        if isinstance(file_object.content_as_buffer, StringIO):
            raise ValueError(
                "Buffer for file's object must be from a stream of Bytes and not String for "
                "`VideoMetadataFromContentExtractor.extract` to work!"
            )

        buffer = file_object.content_as_buffer

        if buffer:
            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            video: MoviePyVideo = MoviePyVideo(buffer=buffer)

            for attribute, value in video.metadata:
                setattr(file_object.meta, attribute, value)


class ImageMetadataFromContentExtractor(Extractor):
    """
    Extractor class created for extracting metadata contained in images using Wand.
    This class don't validate any extensions to see if it's image, so any exception that this class output will
    be caught only in stack above.
    """

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> None:
        """
        Method to extract additional metadata information from content.
        """
        # Use Wand to get additional metadata.
        if not file_object.content:
            raise ValueError(
                "Attribute `content` or `content_as_buffer` must be settled before calling "
                "`VideoMetadataFromContentExtractor.extract`!"
            )
        if not len(file_object):
            raise ValueError(
                "Length for file's object must set before calling `VideoMetadataFromContentExtractor.extract`!"
            )

        buffer = file_object.content_as_buffer

        if buffer:
            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            image: WandImage = WandImage(buffer=buffer)

            for attribute, value in image.metadata:
                setattr(file_object.meta, attribute, value)


class DocumentMetadataFromContentExtractor(Extractor):
    """
    Extractor class created for extracting metadata contained in PDF, ePub and other documents that
    pyMuPDF can open.
    This class don't validate any extensions to see if it's document, so any exception that this class output will
    be caught only in stack above.
    """

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> None:
        """
        Method to extract additional metadata information from content.
        """
        # Use fitz to get additional metadata.
        if not file_object.content:
            raise ValueError(
                "Attribute `content` or `content_as_buffer` must be settled before calling "
                "`DocumentMetadataFromContentExtractor.extract`!"
            )
        if not len(file_object):
            raise ValueError(
                "Length for file's object must set before calling `DocumentMetadataFromContentExtractor.extract`!"
            )

        buffer = file_object.content_as_buffer

        if buffer:
            # Local import to avoid longer time to load FileZ library.
            import fitz

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            # We use fitz (PyMuPDF) to open the document.
            # Because BufferedReader (default return for file_system.open) is not accept
            # we need to consume to get its bytes as bytes are accepted as stream.
            doc: Document = fitz.open(
                stream=buffer.read(),
                filetype=file_object.extension,
            )

            for attribute, value in doc.metadata:
                setattr(file_object.meta, attribute, value)


class AudioMetadataFromContentExtractor(Extractor):
    """
    Extractor class created for extracting metadata contained audio files that can be opened through
    TinyTag.
    This class don't validate any extensions to see if it's audio, so any exception that this class output will
    be caught only in stack above.
    """

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> None:
        """
        Method to extract additional metadata information from content.
        """
        # Use tinytag to get additional metadata.
        if not file_object.content:
            raise ValueError(
                "Attribute `content` or `content_as_buffer` must be settled before calling "
                "`AudioMetadataFromContentExtractor.extract`!"
            )
        if not len(file_object):
            raise ValueError(
                "Length for file's object must set before calling `AudioMetadataFromContentExtractor.extract`!"
            )

        # Local import to avoid longer time to load FileZ library.
        from tinytag import TinyTag

        # We don't need to reset the buffer before calling it, because it will be reset
        # if already cached. The next time property buffer is called it will reset again.
        tinytag: TinyTag = TinyTag(file_object.content_as_buffer, len(file_object))
        tinytag.load(tags=True, duration=True, image=False)
        # Same as code in tinytag, it turn default dict into dict so that it can throw KeyError
        tinytag.extra = dict(tinytag.extra)

        attributes_to_extract: set[str] = {
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
        }
        for attribute in attributes_to_extract:
            tinytag_attribute = getattr(tinytag, attribute, None)
            if tinytag_attribute and (not getattr(file_object.meta, attribute, None) or overrider):
                setattr(file_object.meta, attribute, tinytag_attribute)


class MimeTypeFromContentExtractor(Extractor):
    pass
