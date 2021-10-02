# Handler

Handler is a Python package initially created to handle files, and files from remote resources (downloads), for use in 
a personal project that automatically crawl and download multimedia content. It evolved from a simple structure 
paradigm to an orient-object one, as a mean to show some colleagues the advantages in maintainability this paradigm 
brings. 

As time went by, I thought that this 
component of my project could be a standalone package that I could share.

### So what is this project for?

Loading files, reading its metadata information 
from compatible filesystems (you can extend the 
`FileSystem` class to make your local or remote filesystem compatible), generating or checking hashes like md5 and 
sha256 (and many others), and saving files without worrying about overwriting existing ones, unless you want it 
to of course.

### Why was this project created?

The main motivation for the existence of this package, initially, was my need to have a download system able to save 
and load files from multiple filesystems and run distinct pos-processors in it - parsing and generating hashes are 
a few examples. 

This project obviously isn't that system. It is a bit of it, the part that I thought would make more sense as an 
independent package, able to load files and do other stuff related to file management.

## How to use

To handler files this project provides the classes `File`, `StreamFile` and `ContentFile`. What distinguish one from 
another is the previously set pipeline for data extraction. Those class inherent from `BaseFile` that requires a 
pipeline but not implement one. 

Those pipelines are used not only for data extraction (through `extract_data_pipeline`), but also to generate hash 
(`hasher_pipeline`) or rename a file (`rename_pipeline`) or compare a file with another one (`compare_pipeline`), and 
are implementations that inherent from `ProcessorMixin` and make use of `Pipeline`.

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
