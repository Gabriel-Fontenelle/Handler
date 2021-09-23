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

__all__ = [
	'ImproperlyConfiguredFile',
	'NoInternalContentError',
	'OperationNotAllowed',
	'ValidationError',
	'ReservedFilenameError'
]


class NoInternalContentError(Exception):
	"""
	Exception that defines errors for when no internal content is found in file.
	Meaning that the file is not a container or compacted file.
	"""


class ImproperlyConfiguredFile(Exception):
	"""
	Exception that defines error for when a File was a missing configuration.
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
