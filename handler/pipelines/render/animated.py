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

from .. import Pipeline
from .static import StaticRender

__all__ = [
    'AnimatedRender'
]


class AnimatedRender(StaticRender):
    """
    Render class with focus to processing information from file's content to create an animated representation of it.
    """

    @classmethod
    def create_file(cls, object_to_process, content):
        """
        Method to create a file structured for the animated image on same class as object_to_process.
        """
        defaults = object_to_process._thumbnail.defaults

        # Create file object for image, change filename from parent to use
        # the new format as base for extension.
        animated_file = object_to_process.__class__(
            path=f"{object_to_process.sanitize_path}.{defaults.format_extension}",
            extract_data_pipeline=Pipeline(
                'handler.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
                'handler.pipelines.extractor.MimeTypeFromFilenameExtractor',
            ),
            file_system_handler=object_to_process.storage
        )

        # Set content from buffer.
        animated_file.content = content

        # Set metadata for file object of preview.
        animated_file.meta.preview = True

        return animated_file

