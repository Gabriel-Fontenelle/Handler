# -*- coding: utf-8 -*-

# Python 2 and 3 compatibility
from __future__ import (
	print_function,
	unicode_literals
)
from builtins import (
	object
)

# third-party
from psutil import (
	disk_usage,
	virtual_memory,
	swap_memory
)

class SystemHandler(object):

	@classmethod
	def has_available_swap(self, reversed_data = 0):
		""" Method to verify if there is swap memory available for reserved_data.
			The default implementation uses psutil operations. Override this method if that's not appropriate for your system.

		"""
		data = virtual_memory()
		return virtual_memory.available >= reversed_data

	@classmethod
	def has_available_memory(self, reserved_data = 0):
		""" Method to verify if there is memory available for reserved_data.
			The default implementation uses psutil operations. Override this method if that's not appropriate for your system.

		"""
		data = swap_memory()
		return data.free >= reserved_data

	@classmethod
	def has_available_disk(cls, drive, reserved_data = 0):
		""" Method to verify if there is available space in disk for reserved_data.
			The default implementation uses psutil operations. Override this method if that's not appropriate for your system.

		"""
		data = disk_usage(drive)
		return data.free >= reserved_data
