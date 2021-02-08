#!/usr/bin/python3

# First choice pack and unpack into sqlite
# Paul H Alfille 2021

# Manages persistent data (across invocations) in an SQL database
# called "persistent.db"

try:
    import sqlite3
except:
    print("Please install the sqlite3 module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
try:
    import json
except:
    print("Please install the json module")
    print("\tit should be part of the standard python3 distribution")
    raise

ArgSQL = 0

class SQL_persistent:
    def __init__( self, user, filename ):
        global ArgSQL
        # open or create database
        self.user = user
        self.filename = filename
        self.connection = type(self).Connect()

    @classmethod
    def Connect( cls ):
        connection = sqlite3.connect('persistent.db')
        if ArgSQL > 0:
            print('CREATE TABLE IF NOT EXISTS persistent (user TEXT NOT NULL, filename TEXT NOT NULL, ptype TEXT NOT NULL, NAME TEXT  NOT NULL, jsondata TEXT)' )
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS persistent (user TEXT NOT NULL, filename TEXT NOT NULL, ptype TEXT NOT NULL, NAME TEXT  NOT NULL, jsondata TEXT)' )
        if ArgSQL > 0:
            print('CREATE UNIQUE INDEX IF NOT EXISTS ipersistent ON persistent (user, filename , ptype , NAME )' )
        cursor = connection.cursor()
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ipersistent ON persistent (user, filename , ptype , NAME )' )
        connection.commit()
        return connection

    @classmethod
    def Userlist( cls ):
        connection = cls.Connect()
        if ArgSQL > 0:
            print('SELECT DISTINCT user FROM persistent ORDER BY user')
        cursor = connection.cursor()
        users = cursor.execute('SELECT DISTINCT user FROM persistent ORDER BY user' ).fetchall()
        return [u[0] for u in users]

    @classmethod
    def Filelist( cls ):
        connection = cls.Connect()
        if ArgSQL > 0:
            print('SELECT DISTINCT filename FROM persistent ORDER BY filename')
        cursor = connection.cursor()
        files = cursor.execute('SELECT DISTINCT filename FROM persistent ORDER BY filename' ).fetchall()
        return [f[0] for f in files]

    def NameList( self, ptype ):
        if ArgSQL > 0:
            print('SELECT name FROM persistent WHERE user=? AND filename=? AND ptype=?',(self.user,self.filename,ptype) )
        cursor = self.connection.cursor()
        nm = cursor.execute('SELECT name FROM persistent WHERE user=? AND filename=? AND ptype=?',(self.user,self.filename,ptype) ).fetchall()
        return [n[0] for n in nm]

    def SetField( self, name, ptype, data ):
        if data is None:
            #Do a DELETE !
            if ArgSQL > 0:
                print('DELETE FROM persistent WHERE user=? AND filename=? AND ptype=? AND name=?',(self.user,self.filename,ptype,name) )
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM persistent WHERE user=? AND filename=? AND ptype=? AND name=?',(self.user,self.filename,ptype,name) )
            self.connection.commit()
        else:
            j = json.dumps(data)
            if ArgSQL > 0:
                print('INSERT OR REPLACE INTO persistent (user,filename,ptype,name,jsondata) VALUES (?,?,?,?,?)',(self.user,self.filename,ptype,name,j) )
            cursor = self.connection.cursor()
            cursor.execute('INSERT OR REPLACE INTO persistent (user,filename,ptype,name,jsondata) VALUES (?,?,?,?,?)',(self.user,self.filename,ptype,name,j) )
            self.connection.commit()

    def GetField( self, name, ptype ):
        if ArgSQL > 0:
            print('SELECT jsondata FROM persistent WHERE user=? AND filename=? AND ptype=? AND name=?',(self.user,self.filename,ptype,name) )
        cursor = self.connection.cursor()
        j = cursor.execute('SELECT jsondata FROM persistent WHERE user=? AND filename=? AND ptype=? AND name=?',(self.user,self.filename,ptype,name) ).fetchone()
        if j is not None:
            return json.loads(j[0])
        return None

    def SearchNames( self ):
        return self.NameList("search")

    def SetSearch( self, name, searchdict ):
        self.SetField( name, "search", searchdict )
        
    def GetSearch( self, name ):
        return self.GetField( name, "search" )
        
    def TableNames( self ):
        return self.NameList("table")

    def SetTable( self, name, table ):
        self.SetField( name, "table", table )
        
    def GetTable( self, name ):
        return self.GetField( name, "table" )
        

