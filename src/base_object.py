# pylint: disable=too-few-public-methods
# -*- coding: utf-8 -*-
""" Base verbose object """


from typing import Optional


class DebugError(Exception):
    def __init__(self, message) -> None:
        super().__init__("DEBUG "+message)


class BaseObject:
    """ Base class for every object """

    def __init__(self, verbose:Optional[bool]=True):
        self._verbose = verbose

    def _vprint(self, string:str, end:str="\n") -> None:
        """ Print if verbose """
        if self._verbose:
            print("DEBUG "+string, end=end)
    
    def __getstate__(self):
        """ Overwritten to exclude private attributes in jsonpickle
        https://stackoverflow.com/questions/18147435/how-to-exclude-specific-fields-on-serialization-with-jsonpickle """
        state = self.__dict__.copy()
        attributes = list(state.keys())
        for att in attributes:
            if att.startswith('_'):
                state.pop(att)
        return state

    def __setstate__(self, state):
        """ Overwritten to exclude private attributes in jsonpickle
        https://stackoverflow.com/questions/18147435/how-to-exclude-specific-fields-on-serialization-with-jsonpickle """
        self.__dict__.update(state)

    def to_record(self, table):
        """ Return a record of the current object, for the given table
        NOTE table is a Table object, and this returns a Record object, crossreference got in the way
        of type hinting """
        raise NotImplementedError

    @classmethod
    def from_record(record, verbose:Optional[bool]=True):
        """ Return an object of the current class, from the given record
        NOTE record is a Record object, and this returns a BaseObject object, crossreference got in the
        way of type hinting """
        raise NotImplementedError


class Singleton(type): 
    # Inherit from "type" in order to gain access to method __call__
    def __init__(self, *args, **kwargs):
        self.__instance = None # Create a variable to store the object reference
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            # if the object has not already been created
            self.__instance = super().__call__(*args, **kwargs) # Call the __init__ method of the subclass and save the reference
            return self.__instance
        else:
            # if object reference already exists; return it
            return self.__instance
