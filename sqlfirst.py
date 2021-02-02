#!/usr/bin/python3

# First choice pack and unpack into sqlite
# Paul H Alfille 2021

# Wrap firstchoice-specific code into an sqlite3 one.

try:
    import sys
except:
    print("Please install the sys module")
    print("\tit should be part of the standard python3 distribution")
    raise
       
import first
import sqltable

ArgSQL = 0

class SQL_FOL_handler(first.FOL_handler):
    def __init__(self, FOLfile,  FOLout='OUTPUT.FOL' , sqlfile=None, **kwargs):
        # Read in the FOL file (dbase) into an sql database sqlfile -- None for memory
        # Alternatively use the connection to use an already opened database file
        
        global ArgSQL

        super().__init__( FOLfile,  FOLout, **kwargs)

        sqltable.SQL_table.Prepare( sqlfile )
        
        # Create new table
        self.Fields()
        sqltable.SQL_table.Create( self.fields )

        # Put all FOL data into SQL table
        sqltable.SQL_table.AllDataPut(self.data)

        
    def Fields( self ):
        self.fields = [SqlField(f['field']) for f in self.form['fields']]
        #print(self.fields)

    def Write( self ):
        self.data = sqltable.SQL_table.AllDataGet()
        super().Write()

if __name__ == '__main__':
    def signal_handler( signal, frame ):
        # Signal handler
        # signal.signal( signal.SIGINT, signal.SIG_IGN )
        sys.exit(0)

if __name__ == '__main__': # command line
    """
    First Choice FOL_handler File
    *.fol
    """
    args = first.CommandLine() # Get args from command line
    ArgVerbose = args.verbose or 0
    ArgFields = args.fields or 0
    ArgBlocks = args.blocks or 0
    ArgData = args.data or 0
    ArgSQL = args.sql or 0
    
    # Set up keyboard interrupt handler
    signal.signal(signal.SIGINT, first.signal_handler )
    
    # Start program
    
    # Read in databaase (FOL file already open from command line)
    dbase_class = SQL_FOL_handler( args.In, args.Out )
    
    # Changes could happen here,
    # If nothing else, this is a test of parsing
    
    # Write out file to new database
    dbase_class.Write()

    sys.exit(None)
    
else: #module
    first.ArgSQL = 1
    def OpenDatabase( databasename, SQLverbose=0 ):
        global ArgSQL = SQLverbose
        return SQL_FOL_handler( databasename )
        
    def Fields(dbase_class):
        return dbase_class.fields;
        
    def SaveDatabase( dbase_class, newdatabase ):
        if dbase_class is not None:
            dbase_class.Write()
