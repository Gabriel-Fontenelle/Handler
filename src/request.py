# -*- coding: utf-8 -*-

# Python 2 and 3 compatibility
from __future__ import (
	print_function,
	unicode_literals
)
from future.utils import iteritems
from builtins import (
	object,
)

# third-party
from requests import (
	head as requests_head,
	get as requests_get
)

# core modules
from ..core.regex import (
	PatternFile
)

# modules
from .uri import URLSanitizer


class RequestHandler(object):

	remove_www_from_domain = True
	system_folder_limit = 200
	ignore_double_http = True

	@classmethod
	def generate_folder_name(cls, url):
		#Fix url encode.
		url_parse = urlparse(unquote(url))
		path = url_parse.path.replace(':','/').lstrip("/")

		#Replace unnecessary things.
		host = sub(PatternUri.pattern_uri_port, '', url_parse.netloc).lower()

		#Remove www if option remove_www_from_domain set on class
		if cls.remove_www_from_domain and host[:4] == 'www.':
			host = host[4:]

		path = sub(PatternUri.pattern_uri_index, '', path)
		path = sub(PatternUri.pattern_uri_type, '', path)
		path = path.rstrip("/")

		dirs = []

		for type, value in iteritems(parse_qs(url_parse.query.replace(':','/'))):
			for dir in value:
				dirs.append(dir)

		if dirs:
			path = path + "/" + "/".join(dirs)

		#Remove invalid folder characters
		path = sub(PatternFolder.pattern_invalid_symbol, '', path)

		#Remove characters not extract from query
		path = sub(PatternMiscellaneou.pattern_invalid_query, '/', path)

		path = sub(PatternUri.pattern_uri_double_bar, '/', path)

		if sep != "/":
			path = sep.join(path.split("/"))

		path = os_path.join(host, path)

		if path[-1] == sep:
			path = path[0:-1]

		#remove extension from folder name
		if path.count(sep) > 1:
			#Remove only in subfolder.
			path = sub(PatternFile.pattern_pseudo_extension, '', path)

		return path[:cls.system_folder_limit]

	@staticmethod
	def redirect_url_if_needed(url):
		meta = requests_head(url)
		meta.close()

		#Max redirect times.
		counter = 20

		#Set sanitizer for url used on redirect
		url_sanitizer = URLSanitizer(url)

		resource_metadata = meta.headers

		#Check if need to solve redirect.
		while meta.is_redirect:
			url_sanitizer.set_url(resource_metadata['Location'])
			url = url_sanitizer.get_sanitized_url()

			meta = requests_head(url)
			meta.close()
			resource_metadata = meta.headers

			if not counter:
				break
			counter -=1

		return (url, meta.status_code, resource_metadata)

	@staticmethod
	def get_request_from_uri(url):
		return requests_get(url, stream=True)
