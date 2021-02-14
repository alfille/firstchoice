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
import common

def SqlField( field ):
    return field.replace(' ','_')

def PrintField( field ):
    return field.replace('_',' ')
    

class SQL_FOL_handler(first.FOL_handler):
    def __init__(self, FOLfile,  FOLout='OUTPUT.FOL' , sqlfile=None, **kwargs):
        # Read in the FOL file (dbase) into an sql database sqlfile -- None for memory
        # Alternatively use the connection to use an already opened database file
        
        super().__init__( FOLfile,  FOLout, **kwargs)

        # Create new table
        self.Fields()
        self.SQLtable = sqltable.SQL_table( sqlfile, self.fields )

        # Put all FOL data into SQL table
        self.SQLtable.AllDataPut(self.data)

        
    def Fields( self ):
        self.fields = [SqlField(f['field']) for f in self.form['fields']]
        #print(self.fields)

    def Write( self ):
        self.data = self.SQLtable.AllDataGet()
        super().Write()

def CommandLineArgs( cl ):
    first.CommandLineArgs( cl )
    cl.add_argument("-s","--sql",help="Show SQL statements",action="count")

if __name__ == '__main__':
    def signal_handler( signal, frame ):
        # Signal handler
        # signal.signal( signal.SIGINT, signal.SIG_IGN )
        sys.exit(0)

    def CommandLineInterp( ):
        first.CommandLineInterp( )

    def CommandLine():
        """Setup argparser object to process the command line"""
        cl = argparse.ArgumentParser(description="SQL access to a PFS:First Choice v3 database file (.FOL). 2021 by Paul H Alfille")
        CommandLineArgs( cl )
        cl.add_argument("In",help="Existing database file (type .FOL)",type=argparse.FileType('rb'))

        return cl.parse_args()

if __name__ == '__main__': # command line
    """
    First Choice FOL_handler File
    *.fol
    """
    common.args = CommandLine() # Get args from command line
    CommandLineInterp( )
    
    # Set up keyboard interrupt handler
    signal.signal(signal.SIGINT, first.signal_handler )
    
    # Start program
    
    # Read in databaase (FOL file already open from command line)
    try:
        dbase_class = SQL_FOL_handler( args.In, args.Out )
    except common.User_Error as error:
        print("Error parsing database file: {}".format(error))
        dbase_class = None
    
    # Changes could happen here,
    # If nothing else, this is a test of parsing
    
    # Write out file to new database
    if dbase_class is not None:
        dbase_class.Write()

    sys.exit(None)
    
else: #module
    def OpenDatabase( databasename ):
        return SQL_FOL_handler( databasename )
        
    def Fields(dbase_class):
        return dbase_class.fields;
        
    def SaveDatabase( dbase_class, newdatabase ):
        if dbase_class is not None:
            dbase_class.Write()
