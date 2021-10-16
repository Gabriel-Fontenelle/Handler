# Handler

Handler is a Python package initially created to handle files, and files from remote resources (downloads), for use in 
a personal project that automatically crawl and download multimedia content. It evolved from a simple structure 
paradigm to an orient-object one, as a mean to show some colleagues the advantages in maintainability this paradigm 
brings. 

As time went by, I thought that this 
component of my project could be a standalone package that I could share.

### So what is this project for and why to use it?

The main motivation for the existence of this package, initially, was my need to have a download system able to save 
and load files from multiple filesystems and run distinct pos-processors in it - parsing and generating hashes and 
HTTP's metadata are a few examples. 

This project obviously isn't that system. It is a bit of it, the part that I thought would make more sense as an 
independent package, able to load files and do other stuff related to file management and being easily extendable. You 
can extend the `FileSystem` class to make your local or remote filesystem compatible, you can extend the pipeline 
for data extraction, for generating hashes and many other useful things related to handling files.

To handler files this project provides the classes `File`, `StreamFile` and `ContentFile`. What distinguish one from 
another is the previously set pipeline for data extraction. Those class inherent from `BaseFile` that requires a 
pipeline but not implement one. 

Basically this project abstracted the loading and creation of files to avoid some encountered problems:

- When saving overwrite a file, and you are not aware of it;
- There exists a CHECKSUM related to the file that you are not aware, and should be associated with it;
- Updating CHECKSUM after file`s content is changed;
- Loading and saving in a remote filesystem is complicated and each filesystem have distinct api calls.

Thus, this project was created with focus in extendability and hopefull it will be usefull for those that want to 
avoid the problems mentioned. 

### What resources this project offer when handling files?

The `BaseFile`, where all file`s class are inherent from, has the following attributes:

- `id` (`int` or `None`) - File`s ID in the File System.
- `filename` (`str` or `None`) -  Name of file without extension.
- `extension` (`str` or `None`) - Extension of file.
- `complete_filename` (`str`) - Merge of `filename` with `extension`.
- `create_date` (`datetime.datetime` or `None`) - Datetime when file was created.
- `update_date` (`datetime.datetime` or `None`) - Datetime when file was updated.
- `path` (`str` or `None`) - Full path to file including filename. This is the raw path only partially sanitized.
- `sanitize_path` (`str` or `None`) - Full sanitized path to file including filename.
- `save_to` (`str` or `None`) - Path of directory to save file. This path will be use for mixing relative paths.
- `relative_path` (`str` or `None`) - Relative path to save file. This path will be use for generating whole path 
  together with `save_to` and `complete_filename` (e.g `save_to` + `relative_path` + `complete_filename`). 
- `length` (`int`) - Size of file content.
- `mime_type` (`str` or `None`) - File`s mime type.
- `type` (`str` or `None`) - File's type (e.g. image, audio, video, application).

- `hashes` (`dict`) - Checksum information for file. It can be multiples like MD5, SHA128, SHA256, SHA512.
- `file_system_handler` (`FileSystem`) - FileSystem currently in use for File.
    It can be LinuxFileSystem, WindowsFileSystem or a custom one.
- `mime_type_handler` = (`BaseMimeTyper`) - Mimetype handler that defines the source of know Mimetypes.
  This is used to identify mimetype from extension and vice-verse.
- `uri_handler` (`URI`) - URI handler that defines methods to parser the URL.
- `extract_data_pipeline` (`Pipeline`) - Pipeline to extract data from multiple sources. This should be override at 
   child class.
- `compare_pipeline` (`Pipeline`) - Pipeline to compare two files.
- `hasher_pipeline` (`Pipeline`) -  Pipeline to generate hashes from content. 
- `rename_pipeline` (`Pipeline`) - Pipeline to rename file when saving.

- `meta` (`FileMetadata`) - Controller for additional metadata info that file can have. Those metadata will not always 
  exist for all files.
- `_state` (`FileState`) - Controller for state of file. The file will be set-up with default state before being 
  loaded or create from stream.
- `_actions` (`FileActions`) - Controller for pending actions that file must run. The file will be set-up with default 
  (empty) 
  actions.
- `_naming` (`FileNaming`) - Controller for renaming restrictions that file must adopt.
- `content` (`FileContent`) - Controller for how the content of file will be handled.
- `is_binary` (`bool`) - Whether the file content is binary or not. It is a shortcut to `content.is_binary`. 

and the following methods:

- `add_valid_filename` - Method to add filename and extension to file only if it has a valid extension.
        This method return boolean to indicate whether a filename and extension was added or not.
- `compare_to` - Method to run the pipeline, for comparing files.
        This method set-up for current file object with others.
- `generate_hashes` - Method to run the pipeline, to generate hashes, set-up for the file.
- `refresh_from_disk` - This method will reset all attributes, calling the pipeline to extract data again from disk.
- `save` - Method to save file to file system. In this method we do some validation and verify if file can be saved
        following some options informed through parameter `options`.
- `validate` - Method to validate if minimum attributes of file were set to allow saving.
- `write_content` - Method to write content to a given path. This method will truncate the file before saving content to it.

and provide shortcut to the following exceptions:

- `ImproperlyConfiguredFile` - Exception to throw when a required configuration is missing or misplaced.
- `ValidationError` - Exception to throw when a required attribute to be save is missing or improperly configured.
- `OperationNotAllowed` - Exception to throw when a operation is no allowed to be performed due to how the options are set-up in `save` 
  method.
- `NoInternalContentError` - Exception to throw when file was no internal content or being of wrong type to have internal content.
- `ReservedFilenameError` - Exception to throw when a file is trying to be renamed, but there is already another file with the filename 
    reserved. 


## How to use

Below I list some examples of how you could use this project.

### Loading a file

```python
from handler import File

# Load a file from local filesystem
my_file = File(path='<string: path to my file>')

# Load a file from remote or custom filesystem requires that the 
# class `FileSystem` be extend and passed through `file_system_handler` parameter.
my_file = File(
    path='<string: path to my file>', 
    file_system_handler='<class inherent from FileSystem: my_custom_filesystem>'
)

```

### Creating a new file

```python
from handler import ContentFile

# Create a new file manually without extracting data from any source.
my_file = ContentFile(run_extract_pipeline=False)
my_file.content = '<string or bytes: My content here>'
my_file.complete_filename = (
    '<string: filename>',
    '<string: extension without dot (.)>'
)
my_file.save_to = '<string: directory path where it will be saved>'
my_file.save()
```

```python
from handler import StreamFile

# Create a new file from a stream. 
my_file = StreamFile(metadata='<dict: my stream metadata>') # metadata is required by the 
# pipeline of data extraction, it can be empty if there is none. You can also avoid providing 
# metadata parameter if your custom extractor don`t require it. 
my_file.content = '<instance class inherent from BaseIO>'
my_file.save_to = '<string: directory path where it will be saved>'
my_file.save()

# Create a new file from a stream using a custom pipeline for data extraction:
my_file = StreamFile(extract_data_pipeline='<instance of Pipeline class: my custom pipeline') 
my_file.content = '<instance class inherent from BaseIO>'
my_file.save_to = '<string: directory path where it will be saved>'
my_file.save()
```

Any class inherent from `BaseFile` that not overwrite the property `content` (`ContentFile`, `StreamFile` and `File`), 
accept as content either `string`, `bytes` or instance inherent of `BaseIO`. 

### Generating a hash from file

Soon... The code already allow it, just need to complete this README.

### Saving file

Any change to file content can be saved with the code below. Changes in metadata of File are not applied to 
filesystem when saving.

```python
# Saving a new file
my_file.save()

# Saving a file previously loaded from file_system will throw a 
# exception `File.OperationNotAllowed` unless `allow_update` is set to `True` 
# or `create_backup` is set to `True`.
my_file.save(allow_update=True) # overwritten original file content
my_file.save(create_backup=True) # rename the old file as '<complete_filename>.bak' and create a new one
```

The following parameters are accepted in `save` method keyword arguments:

- `overwrite` (`bool`) - If file with same filename exists it will be overwritten.
- `save_hashes` (`bool`) - If hash generate for file should also be saved.
- `allow_search_hashes` (`bool`) - Allow hashes to be obtained from hash`s files already saved.
- `allow_update` (`bool`) - If file exists its content will be overwritten.
- `allow_rename` (`bool`) - If renaming a file and a file with the same name exists a new one will be created instead 
of overwriting it.
- `create_backup` (`bool`) - If file exists and its content is being updated the old content will be backup before saving.

### Customizing a pipeline

Soon... The code already allow it, just need to complete this README.

## Contributing

Soon...

## Related Projects

Soon...

## License

Copyright (C) 2021 Gabriel Fontenelle Senno Silva

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
