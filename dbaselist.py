#!/usr/bin/python3

# First choice pack and unpack into sqlite
# Paul H Alfille 2021

# Manages persistent data (across invocations) in an SQL database
# called "persistent.db"

try:
    import glob
except:
    print("Please install the glob module")
    print("\tit should be part of the standard python3 distribution")
    raise

import sqlfirst

class DbaseField:
    # Convenience class to make finding field information easier
    # Looks at the dbase_class.form object and both the fields list and the textwrap list
    # 

    def __init__(self,field):
        self._field = sqlfirst.SqlField(field['field'])
        self._length = field['length']
        text_wrap = field['textwrap']
        self._final = text_wrap._final
        template = text_wrap.template
        self._lines = len(template)
        if template[-1] == 0:
            self._lines -= 1
        
    @property
    def field( self ):
        return self._field
        
    @property
    def final( self ):
        return self._final
        
    @property
    def length( self ):
        return self._length
        
    @property
    def lines( self ):
        return self._lines
            
class dbaselist(object):
    # only one per database name -- use __new__ to regulate this
    existing = {}

    def __new__( cls, filename ):
        # check list of existing dabase connections
        if filename in cls.existing:
            return cls.existing[filename]
        return super( dbaselist, cls).__new__(cls)
    
    def __init__(self, filename):
        # got here, so a new database
        # add to name list
        type(self).existing[filename] = self

        # open and parse database
        self.dbase_class = sqlfirst.OpenDatabase(filename)

        # list of fields
        self._flist = [ DbaseField(f) for f in self.dbase_class.form['fields'] ] 

    @property
    def SQLtable( self ):
        # avoid one level of indirection
        return self.dbase_class.SQLtable

    @property
    def flist( self ) :
        # field list of DbaseField objects
        return self._flist

    @classmethod
    def filelist( cls ):
        return glob.glob('../**/*.fol',recursive=True) + glob.glob('../**/*.FOL',recursive=True)

    def __del__(self):
        sqlfirst.SaveDatabase( self.dbase_class, "backup.FOL" )
    
