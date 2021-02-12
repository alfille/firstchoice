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

import common

class SQL_persistent:
    def __init__( self, user, filename ):
        # open or create database
        self.user = user
        self.filename = filename
        self.connection = type(self)._Connect()

    @classmethod
    def _Connect( cls ):
        # class method because filelist and userlist are class methods
        connection = sqlite3.connect('persistent.db')
        if common.args.sql:
            print('CREATE TABLE IF NOT EXISTS persistent (user TEXT NOT NULL, filename TEXT NOT NULL, ptype TEXT NOT NULL, NAME TEXT  NOT NULL, jsondata TEXT)' )
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS persistent (user TEXT NOT NULL, filename TEXT NOT NULL, ptype TEXT NOT NULL, NAME TEXT  NOT NULL, jsondata TEXT)' )
        if common.args.sql:
            print('CREATE UNIQUE INDEX IF NOT EXISTS ipersistent ON persistent (user, filename , ptype , NAME )' )
        cursor = connection.cursor()
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ipersistent ON persistent (user, filename , ptype , NAME )' )
        connection.commit()
        return connection

    @classmethod
    def Userlist( cls ):
        connection = cls._Connect()
        if common.args.sql:
            print('SELECT DISTINCT user FROM persistent ORDER BY user')
        cursor = connection.cursor()
        users = cursor.execute('SELECT DISTINCT user FROM persistent ORDER BY user' ).fetchall()
        return [u[0] for u in users]

    @classmethod
    def Filelist( cls ):
        connection = cls._Connect()
        if common.args.sql:
            print('SELECT DISTINCT filename FROM persistent ORDER BY filename')
        cursor = connection.cursor()
        files = cursor.execute('SELECT DISTINCT filename FROM persistent ORDER BY filename' ).fetchall()
        return [f[0] for f in files]

    def _NameList( self, ptype ):
        if common.args.sql:
            print('SELECT name FROM persistent WHERE user=? AND filename=? AND ptype=?',(self.user,self.filename,ptype) )
        cursor = self.connection.cursor()
        nm = cursor.execute('SELECT name FROM persistent WHERE user=? AND filename=? AND ptype=?',(self.user,self.filename,ptype) ).fetchall()
        return [n[0] for n in nm]

    def _SetField( self, name, ptype, data ):
        if data is None:
            #Do a DELETE !
            if common.args.sql:
                print('DELETE FROM persistent WHERE user=? AND filename=? AND ptype=? AND name=?',(self.user,self.filename,ptype,name) )
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM persistent WHERE user=? AND filename=? AND ptype=? AND name=?',(self.user,self.filename,ptype,name) )
            self.connection.commit()
        else:
            j = json.dumps(data)
            if common.args.sql:
                print('INSERT OR REPLACE INTO persistent (user,filename,ptype,name,jsondata) VALUES (?,?,?,?,?)',(self.user,self.filename,ptype,name,j) )
            cursor = self.connection.cursor()
            cursor.execute('INSERT OR REPLACE INTO persistent (user,filename,ptype,name,jsondata) VALUES (?,?,?,?,?)',(self.user,self.filename,ptype,name,j) )
            self.connection.commit()

    def _GetField( self, name, ptype ):
        if common.args.sql:
            print('SELECT jsondata FROM persistent WHERE user=? AND filename=? AND ptype=? AND name=?',(self.user,self.filename,ptype,name) )
        cursor = self.connection.cursor()
        j = cursor.execute('SELECT jsondata FROM persistent WHERE user=? AND filename=? AND ptype=? AND name=?',(self.user,self.filename,ptype,name) ).fetchone()
        if j is not None:
            return json.loads(j[0])
        return None

    def SearchNames( self ):
        return self._NameList("search")

    def SetSearch( self, name, searchdict ):
        self._SetField( name, "search", searchdict )
        
    def GetSearch( self, name ):
        return self._GetField( name, "search" )
        
    def TableNames( self ):
        return self._NameList("table")

    def SetTable( self, name, table ):
        self._SetField( name, "table", table )
        
    def GetTable( self, name ):
        return self._GetField( name, "table" )
        

