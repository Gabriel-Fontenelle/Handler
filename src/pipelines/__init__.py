"""
Module to define the pipelines and its processors classes.
A Pipeline is a sequence that loop processors to be run.
"""
from inspect import ismethod

__all__ = [
    'Processor',
    'ProcessorMixin',
    'Pipeline'
]


class Processor:
    """
    Class to initiate a processor to be used on Pipeline.
    Processors are intermediate class between the pipelines manager (Pipeline)
    and the class with the methods to be run on pipelines.
    """

    verbose_name = None
    """
    Verbose name for processor.
    """
    classname = None
    """
    The class for the processor, this is the class that will be instantiated
    to run the processor.
    """
    method_name = None
    """
    Name of method that must be called when run this processor.
    This method must be have a @classmethod attribute.
    """
    stopper = False
    """
    If this processor stops the pipelines or not.
    """

    def __init__(self, classname, verbose_name, method_name, stopper):
        self.classname = classname
        self.verbose_name = verbose_name
        self.stopper = stopper
        self.method_name=method_name

    def run(self, object_to_process, *args, **kwargs):
        """
        Method to run methodname from classname and return boolean.
        For this method to work methodname should return boolean whether it as successful or not.
        """
        # Get method
        method = getattr(self.classname, self.methodname)

        # Check if method of methodname has classmethod decorator.
        if not ismethod(method):
            raise ProcessLookupError(f"{self.classname.__name__}.{method} should be a classmethod.")

        # Run methodname passing args and kwargs to it and return boolean result from processor
        return getattr(self.classname, self.methodname)(object_to_process, *args, **kwargs)


class ProcessorMixin:
    """
    Class to add required methods of pipelines to the class of processor.classname.
    """
    method_name_to_process = "process"

    @classmethod
    def to_processor(cls, stopper=True):
        """
        Method used to return a processor from class.
        This method can be overwritten in child class. Valid return are Processor object or
        dict containing classname, verbose_name, stopper.
        """
        return Processor(
            classname=cls.__class__,
            verbose_name=str(cls.__class__),
            stopper=stopper,
            method_name=cls.method_name_to_process
        )

    @classmethod
    def process(self, *args, **kwargs):
        """
        Method used to run this class on Processor`s Pipeline.
        This method and to_processor() is not need to compare files
        outside a pipelines.
        Inside the pipeline this method will call to_processor() and run custom logic to
        process the current pipeline that could be a extracter, renamer, hasher, etc.
        """
        raise NotImplementedError("The process method must be overwrite on child class.")


class Pipeline:
    """
    Class to initiate a pipelines with given processors to be run.
    """

    processors_ran = 0
    """ 
    Variable to register the amount of processors ran for this pipelines.
    """

    def __init__(self, *processors):
        """
        This method can receive a single Processor object,
        or a list of Processor objects or a tuple with classname, verbose_name
        and stopper configuration.
        """
        for processor in processors:
            # Check if processor is a dict containing classname, verbose_name and stopper
            if isinstance(dict, processor):
                if not ('classname' in processor or 'stopper' in processor):
                    raise ValueError("Processor dict for pipelines need at least classname and stopper setted.")

                self.add_new_processor(
                    classname=processor.pop('classname'),
                    stopper=processor.pop('stopper'),
                    verbose_name=processor.pop('verbose_name', None),
                )

            # Check if processor is an object from processor
            elif isinstance(processor, Processor):
                self.add_processor(processor)

            else:
                raise ValueError(f"{processor} is not a valid processor. Expecting a dict or Processor object.")

    def add_new_processor(self, classname, verbose_name, stopper):
        """
        Method to instantiate a new processor from parameters and
        add it to list of processors.
        """
        self.pipeline_processors.append(
            Processor(
                classname=classname,
                verbose_name=verbose_name,
                stopper=stopper
            )
        )

    def add_processor(self, processor):
        """
        Method add a processor object to list of processors.
        """
        self.pipeline_processors.append(
            processor
        )

    def run(self, object_to_process, *args, **kwargs):
        """
        Method to run the entire pipelines.
        The processor will define if method will stop or not
        the pipelines.
        """
        # For each processor
        ran = 0
        for processor in self.pipeline_processors:
            result = processor.run(object_to_process, *args, **kwargs)
            ran += 1
            if result and processor.stopper:
                break

        # register statical data about pipelines.
        self.processors_ran = ran
