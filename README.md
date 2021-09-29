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

Soon...
### Loading a file

### Generating a hash from file

### Saving file

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
