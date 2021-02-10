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

class CookieManager:
    # List of all cookie sessions
    # essentially users since last startup
    # Only static methods since the cookie session holds a key to all members
    active_cookies = {}

    @classmethod
    def Valid( cls, cookie ):
        if cookie is None:
            return False
        session = cookie['session'].value
        if session in cls.active_cookies:
            sdict = cls.active_cookies[session]
            sdict['time'] = datetime.time()
            if sdict['dbaseobj'] is None:
                return False
            return True
        return False

    @classmethod
    def _reexpire( cls ):
        expiration = datetime.datetime.now() + datetime.timedelta(days=7)
        return expiration.strftime("%a, %d-%b-%Y %H:%M:%S EST")

    @classmethod
    def NewSession( cls ):
        # Make the cookie
        cookie = cookies.SimpleCookie()
        cookie["session"] = str(random.randint(1,1000000000))+datetime.datetime.now.ctime()
        cookie["session"]["expires"] = cls._reexpire()

        # Initialize and Add to list
        cls._GetSessionDict(cookie) 

        # return cookie
        return cookie

    @classmethod
    def _GetSessionDict( cls, cookie ):
        # creates an cookie entry if none exists
        # resets clock
        #
        # return active_cookie[session]
        
        session = cookie['session'].value
        if session in cls.active_cookies:
            cls.active_cookies[session]['time'] = datetime.time()
        else:
            if len(cls.active_cookies) > 1000:
                # Too long, trim oldest 30%
                t = sorted([ v['time'] for v in cls.active_cookies.values() ])[300]
                cls.active_cookies = { s:cls.active_cookies[s] for s in cls.active_cookies and cls.active_cookies[s]['time'] > t }

            # time used to trim list
            # search is a SearchState object
            # last is prior formdict
            # table is list of fields and sizes
            cls.active_cookies[session] = {
                'dbaseobj': None,
                'persistent': None,
                'dbasename':'',
                'user':'',
                'time':datetime.time(),
                'search':{},
                'last' : {},
                'table': {},
                'current': { 'search':'default', 'table':'default', },
                'modified': { 'search':False, 'table':False, },
            }
        return cls.active_cookies[session]
    
    @classmethod
    def GetDbaseObj( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return sdict['dbaseobj']
    
    @classmethod
    def SetUserDbase( cls, cookie, user, dbasename ):
        sdict = cls._GetSessionDict( cookie )
        sdict['user'] = user
        sdict['database'] = dbasename

        # database object
        dbaseobj = dbaselist.dbaselist( dbasename )
        sdict['dbaseobj'] = dbaseobj

        # persistent database
        sdict['persistent'] = persistent.SQL_persistent( user, dbasename )
        
        ts = sdict['persistent'].GetTable('default')
        if ts is None:
            ts = [(sqlfirst.SqlField(f.field),"1fr") for f in dbaseobj.flist]
            sdict['persistent'].SetTable('default', ts )
        sdict['table'] = ts
        sdict['search'] = sdict['persistent'].GetSearch('default')
    
    @classmethod
    def Persistent( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return sdict['persistent']
        

    @classmethod
    def GetUserDbase( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return tuple( sdict[x] for x in ['user','dbasename'] )
    
    @classmethod
    def SetSearch( cls, cookie, active_search ):
        sdict = cls._GetSessionDict( cookie )
        sdict['search'] = active_search 

    @classmethod
    def GetSearch( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return sdict['search'] 

    @classmethod
    def SetLast( cls, cookie, lastdict ):
        sdict = cls._GetSessionDict( cookie )
        sdict['last'] = lastdict 

    @classmethod
    def GetLast( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return sdict['last']

    @classmethod
    def ResetTable( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        sdict['table']=[(sqlfirst.SqlField(f.field),"1fr") for f in sdict['dbaseobj'].flist]
        
    @classmethod
    def GetTable( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return sdict['table']
        
    @classmethod
    def SetTable( cls, cookie, table ):
        sdict = cls._GetSessionDict( cookie )
        sdict['table'] = table
        
    @classmethod
    def GetTableName( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return sdict['current']['table']
        
    @classmethod
    def SetTableName( cls, cookie, name ):
        sdict = cls._GetSessionDict( cookie )
        sdict['current']['table'] = name
        sdict['modified']['table'] = False
        sdict['persistent'].SetTable( name, sdict['table'] )
        
    @classmethod
    def SetTableMod( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        sdict['modified']['table'] = True
        
    @classmethod
    def GetTableMod( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return sdict['modified']['table']
        
    @classmethod
    def GetSearchName( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return sdict['current']['search']
        
    @classmethod
    def SetSearchName( cls, cookie, name ):
        sdict = cls._GetSessionDict( cookie )
        sdict['current']['search'] = name
        sdict['modified']['search'] = False
        
    @classmethod
    def SetSearchMod( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        sdict['modified']['search'] = True
        
    @classmethod
    def GetSearchMod( cls, cookie ):
        sdict = cls._GetSessionDict( cookie )
        return sdict['modified']['search']
