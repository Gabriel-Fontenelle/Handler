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
`filez <at> gabrielfontenelle.com` can be used.
"""
from __future__ import annotations

import itertools
from typing import Any, Type, TYPE_CHECKING

from ..exception import SerializerError
from ..image import WandImage
from ..pipelines import Pipeline
from ..pipelines.extractor.package import PSDLayersFromPackageExtractor
from ..video import MoviePyVideo

if TYPE_CHECKING:
    from . import BaseFile
    from ..image import ImageEngine
    from ..video import VideoEngine

__all__ = [
    "FileThumbnail",
    "PreviewDefaults",
    "ThumbnailDefaults",
]


class ThumbnailDefaults:
    """
    Class to handle the default properties of render, to allow changes to be propagated to all images.
    For that end, this class should implement only class methods and attributes.

    This class should be used for setting the size and extension of thumbnail to be created.
    """

    # Resize data
    width: int = 250
    """
    Attribute that define the default width for the thumbnail.
    """
    height: int = 375
    """
    Attribute that define the default height for the thumbnail.
    """
    keep_ratio: int = True
    """
    Attribute that define if aspect ratio should be kept when resizing.
    """
    format: str = "jpeg"
    """
    Attribute that define the default extension for the thumbnail as a format for conversion used in Image classes.
    """
    format_extension: str = "jpg"
    """
    Attribute that define the default extension for the thumbnail. It should be related to the format attribute.
    """
    format_dpi: int = 72
    """
    Attribute that define the resolution for the thumbnail when rendering a vectorized content.
    """

    color_to_trim: tuple[int, int, int] = (255, 255, 255)
    """
    Attribute that define which color should be used to trim an image if required.
    """

    filename: str | None = None
    """
    Attribute that define the default filename for the thumbnail. It can have special characters to be 
    used with format.
    """
    mode: str | None = None
    """
    Attribute that define the default color schema for the thumbnail.
    """
    packed_to_ignore: set[str] = PSDLayersFromPackageExtractor.extensions
    """
    Attribute that define list of extensions where we should ignore the internal_files.
    """

    # Engines
    composer_engine = None
    """
    Attribute that identifies the current engine for composing thumbnails in case there is multiples candidates. If 
    this value is None no composition will be made and the first image found should be used instead.
    Available composer can be found at `filez.image.composer.merger`.
    TODO: Create composer
    """
    default_engine = None
    """
    Attribute that identifies the current engine for composing the default image.
    If this value is None no default image will be created and _static_image will be set to False case there is 
    no thumbnail to be created.
    Available default composers can be found at `filez.image.composer.default`.
    TODO: Create composer
    """


class PreviewDefaults(ThumbnailDefaults):
    """
    Class to handle the default properties of render, to allow changes to be propagated to all images.
    For that end, this class should implement only class methods and attributes.

    This class should be used for setting the size and extension of preview to be created.
    """

    format: str = "webp"
    """
    Attribute that define the default extension for the thumbnail as a format for conversion used in Image classes.
    """
    format_extension: str = "webp"
    """
    Attribute that define the default extension for the thumbnail. It should be related to the format attribute.
    """

    # Animation data
    delay: int = 1
    """
    Attribute that defines the delay between each frame in the animation in seconds.
    """
    duration: int = 10
    """
    Attribute that defines a fix percentual duration for the animation.
    """


class FileThumbnail:
    """
    Class that store thumbnail data from file instance content.
    """

    # Default properties
    static_defaults: Type[ThumbnailDefaults] = ThumbnailDefaults
    """
    Attribute to store the default values to be used for handling thumbnails.
    This attribute must be a class, not instance, so any change will affect all usages. 
    """
    animated_defaults: Type[PreviewDefaults] = PreviewDefaults
    """
    Attribute to store the default values to be used for handling animated previews.
    This attribute must be a class, not instance, so any change will affect all usages. 
    """

    # Thumbnail and preview data
    history: dict[str, list[BaseFile]]
    history = None
    """
    Attribute to store previous generated thumbnails to allow browsing old ones for current file.
    This attribute will be a dictionary with history for static and animated files.
    """
    related_file_object: BaseFile
    related_file_object = None
    """
    Attribute to store the current file object associated with the FileThumbnail.
    """
    _static_file: BaseFile
    _static_file = None
    """
    Attribute to store the File object for the cover of the file, also known as thumbnail.
    """
    _animated_file: BaseFile
    _animated_file = None
    """
    Attribute to store the File object for the animated preview of the file.
    """

    # Engines
    image_engine: Type[ImageEngine] = WandImage
    """
    Attribute that identifies the current engine for use with the thumbnails. This engine must be inherent from 
    ImageEngine or implement its methods to avoid errors.
    """
    video_engine: Type[VideoEngine] = MoviePyVideo
    """
    Attribute that identifies the current engine for use with videos for the thumbnails. This engine must be inherent 
    from VideoEngine or implement its methods to avoid errors.
    """

    # Pipelines
    render_static_pipeline: Pipeline = Pipeline(
        "filez.pipelines.render.static.DocumentFirstPageRender",
        "filez.pipelines.render.static.ImageRender",
        "filez.pipelines.render.static.PSDRender",
        "filez.pipelines.render.static.VideoRender",
    )
    """
    Pipeline to render thumbnail representation from multiple source. For it to work, its classes should implement 
    stopper as True.
    """
    render_animated_pipeline: Pipeline = Pipeline(
        "filez.pipelines.render.animated.StaticAnimatedRender",
        "filez.pipelines.render.animated.ImageAnimatedRender",
    )
    """
    Pipeline to render animated thumbnail representation from multiple source. For it to work, its classes should 
    implement stopper as True.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Method to create the current object using the keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

    @property
    def __serialize__(self) -> dict[str, Any]:
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """

        attributes = {
            "static_defaults",
            "animated_defaults",
            "history",
            "related_file_object",
            "_static_file",
            "_animated_file",
            "image_engine",
            "video_engine",
            "render_static_pipeline",
            "render_animated_pipeline",
        }

        return {key: getattr(self, key) for key in attributes}

    @property
    def thumbnail(self) -> BaseFile:
        """
        Method to compose the cover for the file, also known as thumbnail.
        This method should return only one image.

        If there is a composer engine in static_defaults, a mix of pages will be resized and combined in one image.
        If there is no image to represent the file, and there is a default engine in static_defaults, a default image
        will be composed else _static_file will be set to False.
        """
        if self.related_file_object._actions.thumbnail:
            self.reset(name="_static_file")

        # Generate static file if not exists already
        if self._static_file is None:
            self._generate_file(name="static", defaults=self.static_defaults)

        return self._static_file

    @property
    def preview(self) -> BaseFile:
        """
        Method to compose the preview animated for the file.
        This method should return only one animated image.

        If there is a composer engine in animated_defaults, a mix of animated images will be merged in one image.
        If there is no image to represent the file, and there is a default engine in animated_defaults, a default image
        will be composed else _animated_file will be set to False.
        """
        if self.related_file_object._actions.preview:
            self.reset(name="_animated_file")

        # Generate animated file if not exists already
        if self._animated_file is None:
            self._generate_file(name="animated", defaults=self.animated_defaults)

        return self._animated_file

    def _conclude_static_action(self) -> None:
        """
        Method to apply the action related with generating a static thumbnail file.
        As convention this method should be considered private and not called outside internal use.
        """
        self.related_file_object._actions.thumbnailed()

    def _conclude_animated_action(self) -> None:
        """
        Method to apply the action related with generating an animate preview file.
        As convention this method should be considered private and not called outside internal use.
        """
        self.related_file_object._actions.previewed()

    def _generate_file(self, defaults: Type[ThumbnailDefaults], name: str = "static") -> None:
        """
        Method to process a list of files in order to generate thumbnail's or previews' files.
        This method use name to retrieve the related files in thumbnail. Possible names are static and animated.
        As convention this method should be considered private and not called outside internal use.

        If there is a composer engine in defaults, the composer will be called to process the list of files
        generated.
        If there is no image to represent the file, and there is a default engine in defaults, a default image
        will be composed else the file related to name will be set to False.
        """

        # Obtain the current list of files that could be used for generating previews.
        files: list[BaseFile] = self._get_files_to_process(defaults)

        to_be_processed: list[BaseFile] = []

        for file_object in files:
            # Call processor for each file running the pipeline to render an animated image
            # of the file, files that don't have a processor will result in None
            getattr(self, f"render_{name}_pipeline").run(
                object_to_process=file_object,
                image_engine=self.image_engine,
                video_engine=self.video_engine,
                **file_object._get_kwargs_for_pipeline(f"render_{name}_pipeline")
            )

            # Check if animated image was generated
            file_processed: BaseFile = getattr(file_object._thumbnail, f"_{name}_file")

            if file_processed is not None:

                if defaults.composer_engine is None:
                    # Return the first preview
                    setattr(self, f"_{name}_file", file_processed)

                    # Set state of related file as concluded.
                    getattr(self, f"_conclude_{name}_action")()

                    return

                to_be_processed.append(file_processed)

        if to_be_processed:
            # Call the current composer set up for the FileThumbnail.
            # It will clone the images and merge it in a single sequence.
            setattr(self, f"_{name}_file", defaults.composer_engine.compose(
                objects_to_compose=to_be_processed,
                engine=self.image_engine
            ))
        elif defaults.default_engine is not None:
            # No image was rendered for thumbnail, so we should return the default one.
            setattr(self, f"_{name}_file", defaults.default_engine.compose(object_to_process=self.related_file_object))
        else:
            setattr(self, f"_{name}_file", False)

        # Set state of related file as concluded.
        getattr(self, f"_conclude_{name}_action")()

    def _get_files_to_process(self, defaults: Type[ThumbnailDefaults]) -> list[BaseFile]:
        """
        Method to obtain the list of files to process considering if current related file object is a package with
        internal files or not.
        As convention this method should be considered private and not called outside internal use.
        """
        if self.related_file_object.meta.packed and self.related_file_object.extension not in defaults.packed_to_ignore:
            # Check if there is an element in iterator, else the self.related_file_object will be used.
            first, second = itertools.tee(self.related_file_object.files, 2)
            try:
                next(second)
                files = list(first)
            except StopIteration:
                files = [self.related_file_object]
        else:
            files = [self.related_file_object]

        return files

    def clean_history(self) -> None:
        """
        Method to clean the history of file thumbnail.
        The data will still be in memory while the Garbage Collector don't remove it.
        """
        self.history: dict[str, list[BaseFile]] = {"_static_file": [], "_animated_file": []}

    def display_image(self) -> None:
        """
        Method to debug the current static image showing it with the available image engine.
        This method make use of property thumbnail to generate the thumbnail image if not
        processed already.
        """
        buffer = self.thumbnail.content_as_buffer
        if buffer:
            image = self.image_engine(buffer=buffer)
            image.show()

    def display_animation(self) -> None:
        """
        Method to debug the current animated image showing it with the available image engine.
        This method make use of property preview to generate the thumbnail image if not
        processed already.
        """
        buffer = self.preview.content_as_buffer
        if buffer:
            image = self.image_engine(buffer=buffer)
            image.show()

    def reset(self, name: str = "_static_file") -> None:
        """
        Method to clean the generated thumbnail keeping a history of changes.
        This method can be used for both static file and animated file, informing the attribute related
        to the file through the parameter `name`.
        """
        if self.history is None:
            self.clean_history()

        file_generated: BaseFile | None = getattr(self, name)

        if file_generated:
            # Add current generated file to memory
            self.history[name].append(file_generated)

            # Reset the internal files
            setattr(self, name, None)
