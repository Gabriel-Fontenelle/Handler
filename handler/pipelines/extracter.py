from handler.pipelines import ProcessorMixin


class Extracter(ProcessorMixin):

    @classmethod
    def extract(cls, file_object):
        """
        Method to extract the information necessary from a file_object.
        This method must be override in child class.
        """
        raise NotImplementedError("Method extract must be overwritten on child class.")

    @classmethod
    def process(cls, *args, **kwargs):
        """
        Method used to run this class on Processor`s Pipeline for Extracting info from Data.
        This method and to_processor() is not need to extract info outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        """
        object_to_process = kwargs['object'] if 'object' in kwargs else args[0]

        cls.extract(file_object=object_to_process)

        return True

