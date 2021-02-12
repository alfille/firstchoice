#!/usr/bin/python3

# First choice pack and unpack into sqlite
# Paul H Alfille 2021

try:
    import sqlite3
except:
    print("Please install the sqlite3 module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
import common

def FC2SQLquery( fld, fol_string ):
    # converts an first choice query to sqlite3 syntax
    
    # returns a tuple of
    # 1. query text wit hplaceholders
    # 2. list of params
    
    # None if no query
    # 
    if fol_string is None:
        return None
    
    # trim off leading and training whitespace
    fol = fol_string.strip()
    if fol == '':
        return None
    
    # Test for negation
    if fol[0] == '/':
        negate = " NOT "
        fol = fol[1:]
    else:
        negate = ""
        
    # Test for Wildcard
    if fol.find('..')>=0 or fol.find('?')>=0:
        return (
            fld + negate + ' LIKE ?', 
            [fol.replace('..','%').replace('?','_')] 
            )
        
    # Test for Range
    if fol.find('->')>0:
        return (
            fld + negate + ' BETWEEN ? AND ?',
            fol.split('->',1)
            )
        
    # Test for conditions
    if fol[0] == '=':
        if negate == '':
            return (
                fld + '= ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '!= ?',
                [fol[1:]]
                )
    if fol[0].find('<=') == 0:
        if negate == '':
            return (
                fld + '<= ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '> ?',
                [fol[1:]]
                )
    if fol[0].find('>=') == 0:
        if negate == '':
            return (
                fld + '>= ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '< ?',
                [fol[1:]]
                )
    if fol[0] == '>':
        if negate == '':
            return (
                fld + '> ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '<= ?',
                [fol[1:]]
                )
    if fol[0] == '<':
        if negate == '':
            return (
                fld + '< ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '>= ?',
                [fol[1:]]
                )
        
    return (
        fld + ' LIKE ?',
        [fol]
        )

class SQL_table:
    def __init__( self, sqlfile, field_list ):
        self.field_list = None
        self.connection = None
        self.total = 0
        self.added = 0
        self.updated = 0
        self.deleted = 0

        if sqlfile is not None:
            self.connection = sqlite3.connect(sqlfile)
        else:
            self.connection = sqlite3.connect(":memory:")
            
        # Delete old table
        if sqlfile is not None:
            if common.args.sql > 0 :
                print('DROP TABLE IF EXISTS first')
            cursor = self.connection.cursor()
            cursor.execute('DROP TABLE IF EXISTS first')
            self.connection.commit()
        
        # Create new table
        self.field_list = field_list
        if common.args.sql > 0 :
            print('CREATE TABLE first ( _ID INTEGER PRIMARY KEY, {}, _ADDED INTEGER DEFAULT 0, _CHANGED INTEGER DEFAULT 0)'.format(','.join([f+' TEXT' for f in field_list])) )
        cursor = self.connection.cursor()
        cursor.execute('CREATE TABLE first ( _ID INTEGER PRIMARY KEY, {}, _ADDED INTEGER DEFAULT 0, _CHANGED INTEGER DEFAULT 0)'.format(','.join([f+' TEXT' for f in field_list])) ) 
        self.connection.commit()

    def AllDataGet( self ):
        if common.args.sql > 0:
            print('SELECT {} FROM first'.format(','.join(self.field_list) ) )
        cursor = self.connection.cursor()
        cursor.execute('SELECT {} FROM first'.format(','.join(self.field_list)) )
        return cursor.fetchall()

    def AllDataPut( self, full_data_list ):
        # Add all data
        if common.args.sql > 0:
            print('INSERT INTO first ( {} ) VALUES ( {} )'.format(','.join(self.field_list),','.join(list('?'*len(self.field_list)))),"<Full Data List>")
        cursor = self.connection.cursor()
        cursor.executemany('INSERT INTO first ( {} ) VALUES ( {} )'.format(','.join(self.field_list),','.join(list('?'*len(self.field_list)))), full_data_list )
        self.connection.commit()
        cursor.execute('SELECT COUNT(_ID) FROM first' )
        self.total = cursor.fetchone()[0]
        
    def FindIDplus(self, ID ):
        r = self.FindID(ID)
        if r is None:
            return None
        return (ID,) + r
            
    def SearchDict( self, search_dict ):
        # Searches using a dict of field criteria (blank ignored)
        where, params = self.where( search_dict )
        #print(where,params)
        if common.args.sql > 0:
            print('SELECT _ID FROM first {}'.format(where) , params )
        cursor = self.connection.cursor()
        return cursor.execute('SELECT _ID FROM first {}'.format(where) , params ).fetchall()

    def SortedSearchDict( self, flist, search_dict ):
        # Search for a set of fields with the given criteria
        # return tuples of the field list ordered by field
        # Searches using a dict of field criteria (blank ignored)
        #
        # Note that return includes _ID as first field, but it isn't part of sort (of course)
        #
        # Also an empty field list defaults to all
        #
        where, params = self.where( search_dict )
        #print(where,params)
        if len(flist) == 0:
            fields = ','.join(self.field_list)
        else:
            fields = ','.join(flist)
        if common.args.sql > 0:
            print('SELECT _ID, {} FROM first {} ORDER BY {} '.format(where,fields,fields) , params )
        cursor = self.connection.cursor()
        return cursor.execute('SELECT _ID,{} FROM first {} ORDER BY {} '.format(fields,where,fields), params ).fetchall()

    def Search( self, search_tuple ):
        # Searches using a tuple of field criteria (one for each field but blank ignored)
        # by constructing a dict
        return self.SearchDict( {f:s for f,s in zip( self.field_list, search_tuple ) if s is not None and len(s.strip())>0 } )

    def where( self, search_dict ):
        # returns the WHERE clause (if needed, else '')
        # and the parameters for placeholders
        # as a tuple of string and tuple)
        where_clause = []
        where_param = []
        for s in search_dict:
            #print(s,search_dict[s])
            if s not in self.field_list:
                continue
            q = FC2SQLquery( s, search_dict[s] )
            if q is None:
                continue
            where_clause.append(q[0])
            where_param += q[1]
            #print( "where",where_clause, where_param )
        if where_clause == []:
            return ( '', [])
        return (
            ' WHERE ' + ' AND '.join(where_clause),
            tuple(where_param)
            )

    def Insert( self, data_tuple ):
        # Create a new SQL record
        # return the new _ID
        if common.args.sql > 0:
            print('INSERT INTO first ( {}, _ADDED ) VALUES ( {} )'.format(','.join(self.field_list),','.join(list('?'*(len(self.field_list)+1)))),data_tuple+(1,))
        cursor = self.connection.cursor()
        cursor.execute('INSERT INTO first ( {}, _ADDED ) VALUES ( {} )'.format(','.join(self.field_list),','.join(list('?'*(len(self.field_list)+1)))),data_tuple+(1,))
        self.connection.commit()
        self.total += 1
        self.added += 1
        return cursor.lastrowid
        
    def Update( self, ID, data_tuple ):
        # Update an SQL record
        if common.args.sql > 0:
            print('UPDATE first SET {}, _CHANGED=1 WHERE _ID=?'.format(','.join(['{}=?'.format(f) for f in self.field_list])),data_tuple+(ID,) )
        cursor = self.connection.cursor()
        cursor.execute('UPDATE first SET {}, _CHANGED=1 WHERE _ID=?'.format(','.join(['{}=?'.format(f) for f in self.field_list])),data_tuple+(ID,) )
        self.connection.commit()
        cursor.execute('SELECT COUNT(_ID) FROM first WHERE _CHANGED=1')
        self.updated=cursor.fetchone()[0]
        
    def Delete( self, ID ):
        # Delete an SQL record
        if common.args.sql > 0:
            print('DELETE FROM first WHERE _ID=?',(ID,) )
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM first WHERE _ID=?',(ID,) )
        self.connection.commit()
        cursor.execute('SELECT COUNT(_ID) FROM first WHERE _ADDED=1')
        self.added=cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(_ID) FROM first WHERE _CHANGED=1')
        self.updated=cursor.fetchone()[0]
        self.total -= 1
        self.deleted += 1
        
    def FindID( self, ID=None ):
        # return tuple of field values, except _ID
        # ID = None for blank (new) record
        if ID is None:
            return tuple( ' ' * len(self.field_list))
        if common.args.sql > 0:
            print('SELECT {} FROM first WHERE _ID=?'.format(','.join(self.field_list)),(ID,))
        cursor = self.connection.cursor()
        cursor.execute('SELECT {} FROM first WHERE _ID=?'.format(','.join(self.field_list)),(ID,))
        return cursor.fetchone()
    
    def IDtoDict( self, ID ):
        # includes _ID as a special case
        return { f:v for f,v in zip( self.field_list+['_ID'], self.FindID( ID )+(ID,) ) }

    def DicttoTup( self, fdict ):
        l = []
        for f in self.field_list:
            if f in fdict:
                l.append( fdict[f] )
            else:
                l.append('')
        return tuple(l)

    def RemoveFields( self, fdict ):
        for f in self.field_list:
            if f in fdict:
                del fdict[f]
    
    def PadFields( self, fdict ):
        for f in self.field_list:
            if f not in fdict:
                fdict[f] = ''
                
    def IsEmpty( self, fdict ):
        for f in self.field_list:
            if f in fdict and max([len(l.strip()) for l in fdict[f].split('\n')]) > 0:
                return False
        return True
