# -*- coding: utf-8 -*-

# Python 2 and 3 compatibility
from __future__ import (
	print_function,
	unicode_literals
)
from builtins import (
	object
)
from io import open

# Python internals
from filecmp import cmp
from copy import copy
from shutil import move
from os import (
	makedirs,
	fsync,
	sep as os_sep
)
from os.path import (
	exists,
	isdir,
	getsize,
	dirname
)

# third-party
from send2trash import send2trash
from hashlib import (
	new as hashlib_new,
	algorithms_guaranteed
)

# core modules
from ..core.exception import (
	DontOverwriteException,
)


class FileSystemHandler(object):

	sep = os_sep

	@classmethod
	def is_dir(cls, path):
		"""
			The default implementation uses os.path operations. Override this method if that’s not appropriate for your storage.
		"""
		return isdir(path)

	@classmethod
	def is_file(cls, path):
		"""
			The default implementation uses os.path operations. Override this method if that’s not appropriate for your storage.
		"""
		return cls.is_dir(path) is False

	@classmethod
	def exists(cls, path):
		"""
			The default implementation uses os.path operations. Override this method if that’s not appropriate for your storage.
		"""
		return exists(path)

	@classmethod
	def is_empty(cls, path):
		"""
			The default implementation uses os.path operations. Override this method if that’s not appropriate for your storage.
		"""
		return getsize(path) == 0

	@classmethod
	def is_file_the_same(cls, path_1, path_2):
		""" Method used to check if two files are the same

		"""
		return cmp(path_1, path_2, False)

	@classmethod
	def init_hashes(cls, hash_list = []):
		hashes = {}

		for hash_type in hash_list:
			if hash_type in algorithms_guaranteed:
				hashes[hash_type] = hashlib_new(hash_type)

		return hashes

	@classmethod
	def digest_hashes(cls, hashes):
		digested = {}

		for hash_type in hashes:
			digested[hash_type] = hashes[hash_type].hexdigest()

		return digested

	@classmethod
	def update_hashes(cls, block, hashes):
		for hash_type in hashes:
			hashes[hash_type].update(block)

	@classmethod
	def send_to_trash(cls, path):
		""" Class method to send file or directory specified with path
			to trash instead of removing it.
		"""
		if cls.exists(path):
			#Send to trash
			send2trash(path)

	@classmethod
	def create_directory(cls, directory_path):
		""" Class method to create directory in the file system.
			This method will try to create directory only if it not exits already.
		"""
		#Create Directory
		if not directory_path:
			raise ValueError("Is necessary the receive a folder name on create_directory method.")

		if not cls.exists(directory_path):
			makedirs(directory_path)

	@classmethod
	def get_size(cls, path):
		return getsize(path)

	@classmethod
	def create_empty_file(cls, file_path):
		basedir = dirname(file_path)

		cls.create_directory(basedir)

		open(file_path, 'a').close()

	@classmethod
	def copy_file(cls, file_path_origin, file_path_destination, overwrite_if_exists = False):
		""" Method used to copy a file from origin to destination.
			This method only try to copy if file exists.
			This method not check if there is a error and maybe can
			produce a OSError exception if not enough space in destination.

			This method will overwrite destination file if overwrite_if_exists is True.
			#This method will use a renamed destination file if
		"""
		if cls.exists(file_path_origin):
			file_exists = cls.exists(file_path_destination)
			if (file_exists and overwrite_if_exists) or not file_exists:
				copy(file_path_origin, file_path_destination)
			else:
				raise DontOverwriteException("Cannot overwrite file because overwrite_if_exists is False")

	@classmethod
	def move_file(cls, file_path_origin, file_path_destination, overwrite_if_exists = False):
		""" Method used to move a file from origin to destination.
			This method do use copy_file to first copy the file and after send file to trash.
			The file only will be sent to trash if no exception was raised on copy_file

		"""
		cls.copy_file(file_path_origin, file_path_destination, overwrite_if_exists)
		cls.send_to_trash(file_path_origin)

	@classmethod
	def save_block_in_file(cls, file_pointer, block):
		file_pointer.write(block)
		#Certify that internal buffer is sent to OS buffer file.
		file_pointer.flush()
		#Certify that OS buffer file save block on file.
		fsync(file_pointer.fileno())

	@classmethod
	def open(cls, path, mode):
		return open(path, mode)

	@classmethod
	def close(cls, file_pointer):
		file_pointer.close()
