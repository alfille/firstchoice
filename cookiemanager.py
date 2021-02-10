# http_server_GET.py

try:
    import datetime
except:
    print("Please install the datetime module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
try:
    from http import cookies
except:
    print("Please install the http.cookies module")
    print("\tit should be part of the standard python3 distribution")
    raise

try:
    import random
except:
    print("Please install the random module")
    print("\tit should be part of the standard python3 distribution")
    raise    
    
import sqlfirst
import persistent
import dbaselist

class CookieObject:
    def __init__( self ):
        self._dbaseobj   = None
        self._persistent = None
        self._dbasename  = ''
        self._user       = ''
        self._time       = datetime.time()
        self._search     = {}
        self._last       = {}
        self._table      = {}
        self._current    = { 'search':'default', 'table':'default', }
        self._modified   = { 'search':False, 'table':False, }

    @property
    def UserDbase( self ):
        # returns a tuple
        return (self._user,self._dbasename)

    @UserDbase.setter
    def UserDbase( self, user_file ):
        # takes a tuple
        self._user, self._dbasename = user_file

        # database object
        self._dbaseobj = dbaselist.dbaselist( user_file[1] )
        #print("DBASEOBJ",self._dbaseobj, user_file )

        # persistent database
        self._persistent = persistent.SQL_persistent( *user_file )
        
        ts = self._persistent.GetTable('default')
        if ts is None:
            ts = [(sqlfirst.SqlField(f.field),"1fr") for f in self._dbaseobj.flist]
            self._persistent.SetTable('default', ts )
        self._table = ts
        self._search = self._persistent.GetSearch('default')

    @property
    def dbaseobj( self ):
        return self._dbaseobj

    @dbaseobj.setter
    def dbaseobj( self, dbaseobj ):
        self._dbaseobj = dbaseobj

    @property
    def persistent( self ):
        return self._persistent

    @persistent.setter
    def persistent( self, persistent ):
        self._persistent = persistent

    @property
    def last( self ):
        return self._last

    @last.setter
    def last( self, last ):
        self._last = last

    @property
    def table( self ):
        return self._table

    @table.setter
    def table( self, table ):
        self._table = table

    @property
    def tablename( self ):
        return self._current['table']

    @tablename.setter
    def tablename( self, name ):
        self._modified['table'] = False
        self._persistent.SetTable( name, self._table )
        self._current['table'] = name

    @property
    def tablemod( self ):
        return self._modified['table']

    @tablemod.setter
    def tablemod( self, mod ):
        self._modified['table'] = mod

    @property
    def search( self ):
        return self._search

    @search.setter
    def search( self, search ):
        self._search = search

    @property
    def searchname( self ):
        return self._current['search']

    @searchname.setter
    def searchname( self, name ):
        self._current['search'] = name
        self._modified['search'] = False
        self._persistent.SetSearch( name, self._search )

    @property
    def searchmod( self ):
        return self._modified['search']

    @searchmod.setter
    def searchmod( self, mod ):
        self._modified['search'] = mod

    

class CookieManager:
    # List of all cookie sessions
    # essentially users since last startup
    # Only static methods since the cookie session holds a key to all members
    active_cookies = {}

    @classmethod
    def Valid( cls, cookie ):
        if cookie is None:
            #print("BAD COOKIE")
            return False

        session = cookie['session'].value
        if session not in cls.active_cookies:
            #print("BAD SESSION")
            return False

        if cls.active_cookies[session].dbaseobj is None:
            #print("BAD DBASEOBJ")
            return False

        #print("GOOD COOKIE")
        return True

    @classmethod
    def _reexpire( cls ):
        expiration = datetime.datetime.now() + datetime.timedelta(days=7)
        return expiration.strftime("%a, %d-%b-%Y %H:%M:%S EST")

    @classmethod
    def NewSession( cls ):
        #print("NEW COOKIE")
        # Make the cookie
        cookie = cookies.SimpleCookie()
        cookie["session"] = random.randint(1,1000000000)
        #cookie["session"] = str(random.randint(1,1000000000))+datetime.datetime.now.ctime()
        cookie["session"]["expires"] = cls._reexpire()

        # Initialize and Add to list
        cls._GetCookieObj(cookie) 

        # return cookie
        return cookie

    @classmethod
    def _GetCookieObj( cls, cookie ):
        # creates an cookie entry if none exists
        # resets clock
        #
        # return active_cookie[session]
        
        session = cookie["session"].value
        if session not in cls.active_cookies:
            cls.active_cookies[session] =  CookieObject()
        return cls.active_cookies[session]
    
    @classmethod
    def GetDbaseObj( cls, cookie ):
        return cls._GetCookieObj( cookie ).dbaseobj
    
    @classmethod
    def SetUserDbase( cls, cookie, user, dbasename ):
        cls._GetCookieObj( cookie ).UserDbase = ( user, dbasename )
    
    @classmethod
    def Persistent( cls, cookie ):
        return cls._GetCookieObj( cookie ).persistent
        

    @classmethod
    def GetUserDbase( cls, cookie ):
        return cls._GetCookieObj( cookie ).UserDbase
    
    @classmethod
    def SetSearch( cls, cookie, active_search ):
        cls._GetCookieObj( cookie ).search = active_search 

    @classmethod
    def GetSearch( cls, cookie ):
        return cls._GetCookieObj( cookie ).search

    @classmethod
    def SetLast( cls, cookie, lastdict ):
        cls._GetCookieObj( cookie ).last = lastdict

    @classmethod
    def GetLast( cls, cookie ):
        return cls._GetCookieObj( cookie ).last

    @classmethod
    def ResetTable( cls, cookie ):
        c_obj = cls._GetCookieObj( cookie )
        c_obj.table = [(sqlfirst.SqlField(f.field),"1fr") for f in c_obj.dbaseobj.flist]
        
    @classmethod
    def GetTable( cls, cookie ):
        return cls._GetCookieObj( cookie ).table
        
    @classmethod
    def SetTable( cls, cookie, table ):
        cls._GetCookieObj( cookie ).table = table
        
    @classmethod
    def GetTableName( cls, cookie ):
        return cls._GetCookieObj( cookie ).tablename
        
    @classmethod
    def SetTableName( cls, cookie, name ):
        cls._GetCookieObj( cookie ).tablename = name
        
    @classmethod
    def SetTableMod( cls, cookie ):
        cls._GetCookieObj( cookie ).tablemod = True
        
    @classmethod
    def GetTableMod( cls, cookie ):
        return cls._GetCookieObj( cookie ).tablemod
        
    @classmethod
    def GetSearchName( cls, cookie ):
        return cls._GetCookieObj( cookie ).searchname
        
    @classmethod
    def SetSearchName( cls, cookie, name ):
        cls._GetCookieObj( cookie ).searchname = name
        
    @classmethod
    def SetSearchMod( cls, cookie ):
        cls._GetCookieObj( cookie ).searchmod = True
        
    @classmethod
    def GetSearchMod( cls, cookie ):
        return cls._GetCookieObj( cookie ).searchmod
