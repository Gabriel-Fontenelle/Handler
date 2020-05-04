# -*- coding: utf-8 -*-

# Python 2 and 3 compatibility
from __future__ import (
	print_function,
	unicode_literals
)
from builtins import (
	object,

)

# core modules
from ..core.exception import (
	DontOverwriteException,
	HashDifferException,
	CannotBeSaved,
)

# modules
from .filesystem import FileSystemHandler
from .renamer import RenamerHandler

class FileHandler(object):
	"""
		TODO:
			[X] Add unique filename handler. Get unique filename and use on reserve_file. DID IT, it is RenamerUniqueHandler
	"""

	#Set renamer handler
	renamer = RenamerHandler

	#overwrite_if_exists = False
	#rename_if_exists = True
	#ignore_if_exists = False #Deprecated
	#generate_new_filename #Used generate a new name with renamer, usefull to use with a RenamerUniqueHandler

	def __init__(self, overwrite=False, rename=True, force_use_new_name=False):
		self.overwrite_if_exists = overwrite
		self.rename_if_exists = rename

		#Set logic for unique filename
		self.set_generate_new_filename(force_use_new_name)

	def set_generate_new_filename(self, value):
		self.generate_new_filename = value

	@classmethod
	def __get_size_differential(cls, file_1, file_2):
		return file_2.get_length() - file_1.get_length()

	@classmethod
	def is_file_the_same(cls, file_1, file_2):
		""" Method used to check if two files area the same.
		"""

		#Check if size diferential is the same
		size_diff = cls.__get_size_differential(file_1, file_2)

		if size_diff == 0:
			return FileSystemHandler.is_file_the_same(file_1.get_complete_path_updated(), file_2.get_complete_path_updated())

		return False

	def __fix_append_destination(self, file, destination_path):
		if destination_path[-1] != file.separator:
			return destination_path + file.separator

		return destination_path

	def __prepare_destination(self, destination_path):
		"""
			If DontOverwriteException was raised even with self.rename_if_exists as True,
			than the file was create by another program before it could be copied by this method.
		"""
		FileSystemHandler.create_directory(destination_path)#This will not create directory if path exists

		if not FileSystemHandler.is_dir(destination_path):
			raise CannotBeSaved("Destination path |{}| is not a directory.".format(destination_path))

		if destination_path[-1] != FileSystemHandler.sep:
			destination_path += FileSystemHandler.sep

		return destination_path

	def __prepare_file(self, file, destination_path):
		destination_path = self.__fix_append_destination(file, destination_path)

		if self.generate_new_filename:
			new_filename = self.renamer.get_new_filename(
				destination_path,
				file.get_filename_updated(),
				file.get_extension()
			)
			file.set_new_filename(new_filename)

		elif FileSystemHandler.exists(destination_path + file.get_complete_filename_updated()):
			if not self.overwrite_if_exists and not self.rename_if_exists:
				raise CannotBeSaved("copy_file couldn`t save file because there is already a file with given name and overwrite and renamed are both False.")

			elif self.rename_if_exists:
				new_filename = self.renamer.get_new_filename(
					destination_path,
					file.get_filename_updated(),
					file.get_extension()
				)
				file.set_new_filename(new_filename)

	def copy_file(self, file, destination_path):
		"""
			If DontOverwriteException was raised even with self.rename_if_exists as True,
			than the file was create by another program before it could be copied by this method.
		"""
		destination_path = self.__prepare_destination(destination_path)
		self.__prepare_file(file, destination_path)

		FileSystemHandler.copy_file(file.get_complete_path_updated(), destination_path + file.get_complete_filename_updated(), self.overwrite_if_exists)

	def move_file(self, file, destination_path):
		destination_path = self.__prepare_destination(destination_path)
		self.__prepare_file(file, destination_path)

		FileSystemHandler.move_file(file.get_complete_path_updated(), destination_path + file.get_complete_filename_updated(), self.overwrite_if_exists)

	def reserve_file(self, file):
		#Check if already exists file, if so rename
		self.__prepare_file(file, file.get_file_location())

		#Create empty file with new name if already exists a file with given name
		FileSystemHandler.create_empty_file(file.get_complete_path_updated())

	def open_file(self, file):
		""" Open file to be write. Becarefull, if file already exists it will be overwrited.
		"""
		#Check if file is empty or can overwrite
		if FileSystemHandler.exists(file.get_complete_path_updated()):
			if not FileSystemHandler.is_empty(file.get_complete_path_updated()) and not self.overwrite_if_exists:
				raise CannotBeSaved("open_file couldn`t open pointer to file because there is already a file with given name and overwrite is False.")

		fp = FileSystemHandler.open(file.get_complete_path_updated(), file.get_write_mode())
		file.set_file_pointer(fp)

	def close_file(self, file):
		if file.get_file_pointer():
			FileSystemHandler.close(file.get_file_pointer())
			file.set_file_pointer(None)

	def read_block_in_file(self, file, block_size):
		if file.get_file_pointer() is None:
			self.open_file(file)

		return file.get_file_pointer().read(block_size)

	def save_block_in_file(self, file, block):
		if file.get_file_pointer() is None:
			self.open_file(file)

		FileSystemHandler.save_block_in_file(file.get_file_pointer(), block)

	def instance_hashes(self, file, hash_list = ['md5']):
		#Instance hash from hashlib
		hashes = FileSystemHandler.init_hashes(hash_list)

		#Add hashes to file.
		file.set_hash_instance(hashes)

	def update_hashes(self, file, block):
		FileSystemHandler.update_hashes(block, file.get_hash_instance())

	def get_digested_hashes(self, file):
		return FileSystemHandler.digest_hashes(file.get_hash_instance())

	def check_hashes(self, file):
		""" Method used to check if hash is the same

		"""
		digested = self.get_digested_hashes(file)

		if not file.get_hashes():
			file.set_hashes(digested)

		else:
			for hash_type in digested:
				hash_save = file.get_hash(hash_type)
				if not hash_save:
					file.set_hash(hash_type, digested[hash_type])
				elif hash_save != digested[hash_type]:
					raise HashDifferException(hash_type, "Hash saved differ on check_hashes() method")

	def load_hashes(self, file, hash_list = []):
		self.instance_hashes(file, hash_list)

		while True:
			chunk = self.read_block_in_file(file, 512)#512Kb
			if not chunk:
				break

			self.update_hashes(file, chunk)

		#Close file
		self.close_file(file)

		#Set digested hashes
		self.digest_hashes(file)

	def digest_hashes(self, file):
		""" Method used to get hash instance from file, generate hex and save hex on object.
			This method will replace any previous hash digested save on file object.
		"""
		file.set_hashes(self.get_digested_hashes(file))
