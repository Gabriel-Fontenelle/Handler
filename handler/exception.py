"""
Module with custom exceptions in use at package.
"""

__all__ = [
	'ImproperlyConfiguredFile',
	'NoInternalContentError',
	'OperationNotAllowed',
	'ValidationError'
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


class ValidationError(Exception):
	"""
	Exception that defines error for when a File was a missing attribute.
	"""


class OperationNotAllowed(Exception):
	"""
	Exception that defines error for when a operation is not allowed for file.
	"""
