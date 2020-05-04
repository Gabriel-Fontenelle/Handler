# -*- coding: utf-8 -*-

# Python 2 and 3 compatibility
from __future__ import (
	print_function,
	unicode_literals
)
from builtins import (
	object
)

class DirectoryHandler(objects):
	pass
	#__get_new_name_file_exists

	#__remove_not_exists_file

	#def remove_unusing_cache_folders

	#__remove_not_exists_files
"""
	Method used to get relative path given two paths. The relative path is based on the path in based_on.
	based_on = c/a/b/c/d/g/index.html
	path = c/a/b/e/i/file.c
	return = ../../../e/i/file.c
"""

def get_directory_relative_path(based_on, path):

	based_on = based_on.replace('\\', '/')
	path = path.replace('\\', '/')


	#Fix directory without / on end
	fix = based_on.rpartition('/')
	if '.' not in fix[2]:
		based_on += '/'

	base_length = len(based_on)
	path_length = len(path)
	count = 0
	last_bar = 0

	if base_length > path_length:
		l = path_length
	else:
		l = base_length

	for i in range(0, l):
		if path[i] != based_on[i]:
			break
		else:
			count += 1
			if path[i] == '/':
				last_bar = count


	if last_bar:
		return '../' * based_on[last_bar:].count('/') + path[last_bar:]

	return path
