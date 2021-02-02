#!/usr/bin/python3

# First choice pack and unpack into sqlite
# Paul H Alfille 2021

try:
    import sqlite3
except:
    print("Please install the sqlite3 module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
ArgSQL = 0

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
    field_list = None
    connection = None
    total = 0
    added = 0
    updated = 0
    deleted = 0

    @classmethod
    def Prepare( cls, sqlfile ):
        global ArgSQL
        if sqlfile is not None:
            cls.connection = sqlite3.connect(sqlfile)
        else:
            cls.connection = sqlite3.connect(":memory:")
            
        # Delete old table
        if sqlfile is not None:
            if ArgSQL > 0 :
                print('DROP TABLE IF EXISTS first')
            cursor = cls.connection.cursor()
            cursor.execute('DROP TABLE IF EXISTS first')
            cls.connection.commit()
        
    @classmethod
    def Create( cls, field_list ):
        global ArgSQL
        # Create new table
        cls.field_list = field_list
        if ArgSQL > 0 :
            print('CREATE TABLE first ( _ID INTEGER PRIMARY KEY, {}, _ADDED INTEGER DEFAULT 0, _CHANGED INTEGER DEFAULT 0)'.format(','.join([f+' TEXT' for f in field_list])) )
        cursor = cls.connection.cursor()
        cursor.execute('CREATE TABLE first ( _ID INTEGER PRIMARY KEY, {}, _ADDED INTEGER DEFAULT 0, _CHANGED INTEGER DEFAULT 0)'.format(','.join([f+' TEXT' for f in field_list])) ) 
        cls.connection.commit()

    @classmethod    
    def AllDataGet( cls ):
        global ArgSQL
        if ArgSQL > 0:
            print('SELECT {} FROM first'.format(','.join(cls.field_list) ) )
        cursor = cls.connection.cursor()
        cursor.execute('SELECT {} FROM first'.format(','.join(cls.field_list)) )
        return cursor.fetchall()

    @classmethod    
    def AllDataPut( cls, full_data_list ):
        global ArgSQL
        # Add all data
        if ArgSQL > 0:
            print('INSERT INTO first ( {} ) VALUES ( {} )'.format(','.join(cls.field_list),','.join(list('?'*len(cls.field_list)))),"<Full Data List>")
        cursor = cls.connection.cursor()
        cursor.executemany('INSERT INTO first ( {} ) VALUES ( {} )'.format(','.join(cls.field_list),','.join(list('?'*len(cls.field_list)))), full_data_list )
        cls.connection.commit()
        cursor.execute('SELECT COUNT(_ID) FROM first' )
        cls.total = cursor.fetchone()[0]
        
class SQL_record(SQL_table):
    @classmethod
    def FindIDplus(cls, ID ):
        r = cls.FindID(ID)
        if r is None:
            return None
        return (ID,) + r
            
    @classmethod
    def SearchDict( cls, search_dict ):
        global ArgSQL
        # Searches using a dict of field criteria (blank ignored)
        where, params = cls.where( search_dict )
        #print(where,params)
        if ArgSQL > 0:
            print('SELECT _ID FROM first {}'.format(where) , params )
        cursor = cls.connection.cursor()
        return cursor.execute('SELECT _ID FROM first {}'.format(where) , params ).fetchall()

    @classmethod
    def SortedSearchDict( cls, flist, search_dict ):
        global ArgSQL
        # Search for a set of fields with the given criteria
        # return tuples of the field list ordered by field
        # Searches using a dict of field criteria (blank ignored)
        #
        # Note that return includes _ID as first field, but it isn't part of sort (of course)
        #
        # Also an empty field list defaults to all
        #
        where, params = cls.where( search_dict )
        #print(where,params)
        if len(flist) == 0:
            fields = ','.join(cls.field_list)
        else:
            fields = ','.join(flist)
        if ArgSQL > 0:
            print('SELECT _ID, {} FROM first {} ORDER BY {} '.format(where,fields,fields) , params )
        cursor = cls.connection.cursor()
        return cursor.execute('SELECT _ID,{} FROM first {} ORDER BY {} '.format(fields,where,fields), params ).fetchall()

    @classmethod
    def Search( cls, search_tuple ):
        global ArgSQL
        # Searches using a tuple of field criteria (one for each field but blank ignored)
        # by constructing a dict
        return cls.SearchDict( {f:s for f,s in zip( cls.field_list, search_tuple ) if s is not None and len(s.strip())>0 } )

    @classmethod
    def where( cls, search_dict ):
        # returns the WHERE clause (if needed, else '')
        # and the parameters for placeholders
        # as a tuple of string and tuple)
        where_clause = []
        where_param = []
        for s in search_dict:
            #print(s,search_dict[s])
            if s not in cls.field_list:
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

    @classmethod
    def Insert( cls, data_tuple ):
        global ArgSQL
        # Create a new SQL record
        # return the new _ID
        if ArgSQL > 0:
            print('INSERT INTO first ( {}, _ADDED ) VALUES ( {} )'.format(','.join(cls.field_list),','.join(list('?'*(len(cls.field_list)+1)))),data_tuple+(1,))
        cursor = cls.connection.cursor()
        cursor.execute('INSERT INTO first ( {}, _ADDED ) VALUES ( {} )'.format(','.join(cls.field_list),','.join(list('?'*(len(cls.field_list)+1)))),data_tuple+(1,))
        cls.connection.commit()
        cls.total += 1
        cls.added += 1
        return cursor.lastrowid
        
    @classmethod
    def Update( cls, ID, data_tuple ):
        global ArgSQL
        # Update an SQL record
        if ArgSQL > 0:
            print('UPDATE first SET {}, _CHANGED=1 WHERE _ID=?'.format(','.join(['{}=?'.format(f) for f in cls.field_list])),data_tuple+(ID,) )
        cursor = cls.connection.cursor()
        cursor.execute('UPDATE first SET {}, _CHANGED=1 WHERE _ID=?'.format(','.join(['{}=?'.format(f) for f in cls.field_list])),data_tuple+(ID,) )
        cls.connection.commit()
        cursor.execute('SELECT COUNT(_ID) FROM first WHERE _CHANGED=1')
        cls.updated=cursor.fetchone()[0]
        
    @classmethod
    def Delete( cls, ID ):
        global ArgSQL
        # Delete an SQL record
        if ArgSQL > 0:
            print('DELETE FROM first WHERE _ID=?',(ID,) )
        cursor = cls.connection.cursor()
        cursor.execute('DELETE FROM first WHERE _ID=?',(ID,) )
        cls.connection.commit()
        cursor.execute('SELECT COUNT(_ID) FROM first WHERE _ADDED=1')
        cls.added=cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(_ID) FROM first WHERE _CHANGED=1')
        cls.updated=cursor.fetchone()[0]
        cls.total -= 1
        cls.deleted += 1
        
    @classmethod
    def FindID( cls, ID=None ):
        # return tuple of field values, except _ID
        # ID = None for blank (new) record
        global ArgSQL
        if ID is None:
            return tuple( ' ' * len(cls.field_list))
        if ArgSQL > 0:
            print('SELECT {} FROM first WHERE _ID=?'.format(','.join(cls.field_list)),(ID,))
        cursor = cls.connection.cursor()
        cursor.execute('SELECT {} FROM first WHERE _ID=?'.format(','.join(cls.field_list)),(ID,))
        return cursor.fetchone()
    
    @classmethod
    def IDtoDict( cls, ID ):
        # includes _ID as a special case
        return { f:v for f,v in zip( cls.field_list+['_ID'], cls.FindID( ID )+(ID,) ) }

    @classmethod
    def DicttoTup( cls, fdict ):
        l = []
        for f in cls.field_list:
            if f in fdict:
                l.append( fdict[f] )
            else:
                l.append('')
        return tuple(l)

    @classmethod
    def RemoveFields( cls, fdict ):
        for f in cls.field_list:
            if f in fdict:
                del fdict[f]
    
    @classmethod
    def PadFields( cls, fdict ):
        for f in cls.field_list:
            if f not in fdict:
                fdict[f] = ''
                
    @classmethod
    def IsEmpty( cls, fdict ):
        for f in cls.field_list:
            if f in fdict and max([len(l.strip()) for l in fdict[f].split('\n')]) > 0:
                return False
        return True

