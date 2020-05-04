# -*- coding: utf-8 -*-

# Python 2 and 3 compatibility

from __future__ import (
	print_function,
	unicode_literals
)
from future.utils import iteritems
from builtins import object


class URLSanitizer(object):

	#schema
	#base_url
	#url
	#sanitize_url

	def __init__(self, url):
		self.base_url = url
		self.set_schema(url)
		self.url = None

	def __is_https(self):
		return 'https' in self.base_url[:7]

	def set_schema(self, url):
		if self.__is_https():
			self.schema = 'https:'
		else:
			self.schema = 'http:'

	def set_url(self, url):
		self.url = url
		self.sanitize_url = None

	def get_sanitized_url(self):
		if self.sanitize_url is None:
			if not "http" in self.url[:6]:
				if self.url[0:2] == '//':
					absolute_url = self.schema + self.url
				else:
					absolute_url = urljoin(self.base_url, self.url) #This only fix relative path with ../ if base_url ends with /
			else:
				absolute_url = self.url

			self.sanitize_url = unquote(absolute_url)

		return self.sanitize_url
