"""
Handler is a package for creating files in an object-oriented way,
allowing extendability to any file system.

Copyright (C) 2021 Gabriel Fontenelle Senno Silva

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Should there be a need for contact the electronic mail
`handler <at> gabrielfontenelle.com` can be used.
"""
import itertools

from ..exception import SerializerError
from ..image import WandImage
from ..pipelines import Pipeline
from ..pipelines.extractor.package import PSDLayersFromPackageExtractor


__all__ = [
    "ThumbnailDefaults",
    "FileThumbnail",
]


class ThumbnailDefaults:
    """
    Class to handle the default properties of render, to allow changes to be propagated to all images.
    For that end, this class should implement only class methods and attributes.

    This class should be used for setting the size and extension of thumbnail to be created.
    """

    # Resize data
    width = 250
    """
    Attribute that define the default width for the thumbnail.
    """
    height = 375
    """
    Attribute that define the default height for the thumbnail.
    """
    keep_ratio = True
    """
    Attribute that define if aspect ratio should be kept when resizing.
    """
    format = "jpeg"
    """
    Attribute that define the default extension for the thumbnail as a format for conversion used in Image classes.
    """
    format_extension = "jpg"
    """
    Attribute that define the default extension for the thumbnail. It should be related to the format attribute.
    """

    filename = None
    """
    Attribute that define the default filename for the thumbnail. It can have special characters to be 
    used with format.
    """
    mode = None
    """
    Attribute that define the default color schema for the thumbnail.
    """
    packed_to_ignore = set(PSDLayersFromPackageExtractor.extensions)
    """
    Attribute that define list of extensions where we should ignore the internal_files.
    """

    # Composer data
    composition = False
    """
    Attribute that define if the first image will be used or a composition of images in case there is multiples.
    """

    # Behavior for default image generator
    compose_default = True
    """
    Attribute that define if the default image should be composed or not. If not, it should return False.
    """
    compose_default_with_filename = False
    """
    Attribute that define if the default image to be composed should also add the filename to the composed image.
    """

    # Animation data
    delay = 1
    """
    Attribute that defines the delay between each frame in the animation in seconds.
    """


class FileThumbnail:
    """
    Class that store thumbnail data from file instance content.
    """

    # Default property
    defaults = ThumbnailDefaults
    """
    Attribute to store the default values to be used for handling thumbnails.
    This attribute must be a class, not instance, so any change will affect all usages. 
    """

    history = None
    """
    Attribute to store previous generated thumbnails to allow browsing old ones for current file.
    This attribute will be a dictionary with history for static and animated files.
    """
    related_file_object = None
    """
    Attribute to store the current file object associated with the FileThumbnail.
    """
    _static_file = None
    """
    Attribute to store the File object for the cover of the file, also known as thumbnail.
    """
    _animated_file = None
    """
    Attribute to store the File object for the animated preview of the file.
    """

    # Processor data
    image_engine = WandImage
    """
    Attribute that identifies the current engine for use with the thumbnails. This engine must be inherent from 
    ImageEngine or implement its methods to avoid errors.
    """
    composer_engine = None
    """
    """

    # Pipeline
    render_static_pipeline = Pipeline(
        "handler.pipelines.render.static.ImageRender",
        "handler.pipelines.render.static.PSDRender",
    )
    """
    Pipeline to render thumbnail representation from multiple source. For it to work, its classes should implement 
    stopper as True.
    """

    render_animated_pipeline = Pipeline(
        "handler.pipelines.render.static.ImageRender"
    )
    """
    Pipeline to render animated thumbnail representation from multiple source. For it to work, its classes should 
    implement stopper as True.
    """

    def __init__(self, **kwargs):
        """
        Method to create the current object using the keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

    @property
    def thumbnail(self):
        """
        Method to compose the cover for the file, also known as thumbnail.
        This method should return only one image.

        If composition is True in defaults, a mix of pages will be resized and combined in one image.
        If there is no image to represent the file, and compose_default is True in defaults, a default image will
        be composed else _static_file will be set to False.
        """
        if self.related_file_object._actions.thumbnail:
            self.reset(name="_static_file")

        # Generate static file if not exists already
        if self._static_file is None:

            if (
                self.related_file_object._meta.packed
                and self.related_file_object.extension not in self.defaults.packed_to_ignore
            ):
                # Check if there is an element in iterator, else the self.related_file_object will be used.
                first, second = itertools.tee(self.related_file_object.files, 2)
                files = first if next(second, False) else [self.related_file_object]
            else:
                files = [self.related_file_object]

            to_be_composed = []

            for file_object in files:
                # Call processor for each file running the pipeline to render a thumbnail
                # of the file, files that don't have a processor will result in None
                self.render_static_pipeline.run(object_to_process=file_object, engine=self.image_engine)

                # Check if static image was generated.
                # We use is None to avoid a bug where bool(file_object._thumbnail._static_file) return False.
                if file_object._thumbnail._static_file is not None:

                    if not self.defaults.composition:
                        # Return the first image
                        self._static_file = file_object._thumbnail._static_file

                        # Set state of related file as thumbnailed.
                        self.related_file_object._actions.thumbnailed()

                        return self._static_file

                    to_be_composed.append(file_object._thumbnail._static_file)

            if to_be_composed:
                # Call the current composer set up for the FileThumbnail.
                # It will clone the images and rendered to be a merge for the collection.
                self._static_file = self.composer_engine.compose(
                    files_to_compose=to_be_composed,
                    engine=self.image_engine
                )
            else:
                # No image was rendered for thumbnail, so we should return the default one or set it to False.
                self._static_file = self.defaults.default_image(self.related_file_object)

            # Set state of related file as thumbnailed.
            self.related_file_object._actions.thumbnailed()

        return self._static_file

    @property
    def preview(self):
        """
        Method to compose the preview animated for the file.
        This method should return only one animated image.
        """
        if self.related_file_object._actions.preview:
            self.reset(name="_animated_file")

        # Generate animated file if not exists already
        if self._animated_file is None:

            files = self.related_file_object.files if self.related_file_object._meta.packed else [
                self.related_file_object
            ]

            to_be_merged = []

            for file_object in files:
                # Call processor for each file running the pipeline to render an animated image
                # of the file, files that don't have a processor will result in None
                self.render_static_pipeline.run(object_to_process=file_object, image_engine=self.image_engine)

                # Check if animated image was generated
                if file_object._thumbnail._animated_file:

                    to_be_merged.append(file_object._thumbnail._animated_file)

            if not to_be_merged:
                self._animated_file = False

            elif len(to_be_merged) == 1:
                self._animated_file = to_be_merged[0]

            else:
                # Merge animated files in one
                pass

            # Set state of related file as previewed.
            self.related_file_object._actions.previewed()

        return self._animated_file

    def clean_history(self):
        """
        Method to clean the history of file thumbnail.
        The data will still be in memory while the Garbage Collector don't remove it.
        """
        self.history = {"_static_file": [], "_animated_file": []}

    def display_image(self):
        """
        Method to debug the current static image showing it with the available image engine.
        This method make use of property thumbnail to generate the thumbnail image if not
        processed already.
        """
        image = self.image_engine(buffer=self.thumbnail.buffer)
        image.show()

    def reset(self, name="_static_file"):
        """
        Method to clean the generated thumbnail keeping a history of changes.
        This method can be used for both static file and animated file, informing the attribute related
        to the file through the parameter `name`.
        """
        if self.history is None:
            self.clean_history()

        file_generated = getattr(self, name)

        if file_generated:
            # Add current generated file to memory
            self.history[name].append(file_generated)

            # Reset the internal files
            setattr(self, name, None)

