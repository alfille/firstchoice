#!/usr/bin/python3

# First choice pack and unpack into sqlite
# Paul H Alfille 2021

# manages the search state -- i.e. what search is under way, and where in the search we are.

import sqltable

class SearchState:
    def __init__(self, dbaseobj, dictionary):
        self.dbaseobj = dbaseobj # for list of fields
        self._last_dict = self.FieldDict( dictionary )
        self._list = [ID[0] for ID in sqltable.SQL_record.SearchDict( self.last_dict )]
        self._index = -1
        if self._list is None:
            self._length = 0
        else:
            self._length = len(self._list)
            #print("Search list",self._list)
        
    def FieldDict( self, dictionary ):
        # return dict with only valid fields
        d = {}
        flist = [f.field for f in self.dbaseobj.flist]
        for k in dictionary:
            if k in flist:
                d[k] = dictionary[k]
        return d
        
    @property
    def last_dict(self):
        return self._last_dict

    @property
    def first( self ):
        if self._length == 0:
            return None
        else:
            self._index = 0
            return self.list[0]
        
    @property
    def next( self ):
        #print("Next",self._index,self._list)
        if self._length == 0:
            return None

        self._index += 1

        return self.index_check()
    
    @property
    def back( self ):
        if self._length == 0:
            return None

        self._index -= 1

        return self.index_check()

    def index_check( self ):
        if self._index < 0:
            self._index = 0
        elif self._index >= self.length:
            self._index = self._length-1
        return self._list[self._index]

    @property
    def list(self):
        return self._list

    @property
    def length( self):
        return self._length

    @property
    def index( self ):
        # Not Zero-based
        return self._index + 1

