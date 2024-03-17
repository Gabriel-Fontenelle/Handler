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

__all__ = [
	'EmptyContentError',
	'ImproperlyConfiguredFile',
	'ImproperlyConfiguredPipeline',
	'NoInternalContentError',
	'OperationNotAllowed',
	'ValidationError',
	'ReservedFilenameError',
	'RenderError',
	'SerializerError'
]


class SerializerError(Exception):
	"""
	Exception that defines errors for when a serialization problem occur in file.
	"""


class NoInternalContentError(Exception):
	"""
	Exception that defines errors for when no internal content is found in file.
	Meaning that the file is not a container or compacted file.
	"""


class EmptyContentError(Exception):
	"""
	Exception that defines errors for when a content was not loaded because its empty.
	"""


class ImproperlyConfiguredFile(Exception):
	"""
	Exception that defines error for when a File has a missing configuration.
	"""


class ImproperlyConfiguredPipeline(Exception):
	"""
	Exception that defines error for when a Pipeline has a missing configuration or improper configured one.
	"""


class OperationNotAllowed(Exception):
	"""
	Exception that defines error for when a operation is not allowed for file.
	"""


class ValidationError(Exception):
	"""
	Exception that defines error for when a File was a missing attribute.
	"""


class ReservedFilenameError(Exception):
	"""
	Exception that defines error for when trying to rename a file to an already reserved one.
	"""


class RenderError(Exception):
	"""
	Exception that defines error for when trying to render a file.
	"""


class PipelineError(Exception):
	"""
	Exception that defines error for when trying to render a file.
	"""
