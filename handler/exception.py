"""
Module with custom exceptions in use at package.
"""

__all__ = [
	'NoInternalContentError'
]


class NoInternalContentError(Exception):
	"""
	Exception that defines errors for when no internal content is found in file.
	Meaning that the file is not a container or compacted file.
	"""
