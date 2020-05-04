# -*- coding: utf-8 -*-

# Python 2 and 3 compatibility
from __future__ import (
	print_function,
	unicode_literals
)
from future.utils import iteritems
from builtins import (
	object,
	range
)

# Python internals
from uuid import uuid4

# core modules
from ..core.regex import (
	PatternFile
)

# modules
from .filesystem import FileSystemHandler


class RenamerHandler(object):

	@staticmethod
	def get_new_filename(path, filename, extension):
		if not extension:
			raise ValueError("ext must be a valid string and cannot be empty.")

		#Remove enumeration from filename
		filename = PatternFile.pattern_enumeration.sub('', filename)

		i = 0
		while FileSystemHandler.exists(path + filename + "." + extension):
			i += 1
			filename = PatternFile.pattern_enumeration.sub(' (' + str(i) + ')', filename)

		return filename

class RenamerUniqueHandler(object):

	@staticmethod
	def get_new_filename(path, filename, extension):
		if not extension:
			raise ValueError("ext must be a valid string and cannot be empty.")

		#Generate Unique filename
		filename = uuid4()

		i = 0
		while FileSystemHandler.exists(path + filename + "." + extension) and i < 100:
			i += 1
			#Generate Unique filename
			filename = uuid4()

		if i == 100:
			raise #Too many files being handler simultaneos

		return filename
