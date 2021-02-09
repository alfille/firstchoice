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
            ac = cls.active_cookies[session]
            ac['time'] = datetime.time()
            if ac['dbaseobj'] is None:
                return False
            return True
        return False

    @classmethod
    def NewSession( cls ):
        # Make the cookie
        expiration = datetime.datetime.now() + datetime.timedelta(days=7)
        cookie = cookies.SimpleCookie()
        cookie["session"] = random.randint(1,1000000000)
        cookie["session"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S EST")

        # Initialize and Add to list
        cls.GetSession(cookie) 

        # return cookie
        return cookie

    @classmethod
    def GetSession( cls, cookie ):
        # creates an cookie entry if none exists
        # resets clock
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
        return session
    
    @classmethod
    def GetDbaseObj( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['dbaseobj']
    
    @classmethod
    def SetUserDbase( cls, cookie, user, dbasename ):
        session = cls.GetSession( cookie )
        ac = cls.active_cookies[session]
        ac['user'] = user
        ac['database'] = dbasename

        # database object
        dbaseobj = dbaselist.dbaselist( dbasename )
        ac['dbaseobj'] = dbaseobj

        # persistent database
        ac['persistent'] = persistent.SQL_persistent( user, dbasename )
        
        ts = ac['persistent'].GetTable('default')
        if ts is None:
            ts = [(sqlfirst.SqlField(f.field),"1fr") for f in dbaseobj.flist]
            ac['persistent'].SetTable('default', ts )
        ac['table'] = ts
        ac['search'] = ac['persistent'].GetSearch('default')
    
    @classmethod
    def Persistent( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['persistent']
        

    @classmethod
    def GetUserDbase( cls, cookie ):
        session = cls.GetSession( cookie )
        return tuple( cls.active_cookies[session][x] for x in ['user','dbasename'] )
    
    @classmethod
    def SetSearch( cls, cookie, active_search ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['search'] = active_search 

    @classmethod
    def GetSearch( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['search'] 

    @classmethod
    def SetLast( cls, cookie, lastdict ):
        session = cls.GetSession( cookie )
        #print("setlast",lastdict) 
        cls.active_cookies[session]['last'] = lastdict 

    @classmethod
    def GetLast( cls, cookie ):
        session = cls.GetSession( cookie )
        #print("getlast",cls.active_cookies[session]['last'])
        return cls.active_cookies[session]['last']

    @classmethod
    def ResetTable( cls, cookie ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['table']=[(sqlfirst.SqlField(f.field),"1fr") for f in cls.GetDbaseObj( cookie ).flist]
        
    @classmethod
    def GetTable( cls, cookie ):
        session = cls.GetSession( cookie )
        print("GET TABLE",cls.active_cookies[session]['table'])
        return cls.active_cookies[session]['table']
        
    @classmethod
    def SetTable( cls, cookie, table ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['table'] = table
        print("SET TABLE",cls.active_cookies[session]['table'])
        
    @classmethod
    def GetTableName( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['current']['table']
        
    @classmethod
    def SetTableName( cls, cookie, name ):
        session = cls.GetSession( cookie )
        ac = cls.active_cookies[session]
        ac['current']['table'] = name
        ac['modified']['table'] = False
        ac['persistent'].SetTable( name, ac['table'] )
        
    @classmethod
    def SetTableMod( cls, cookie ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['modified']['table'] = True
        
    @classmethod
    def GetTableMod( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['modified']['table']
        
    @classmethod
    def GetSearchName( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['current']['search']
        
    @classmethod
    def SetSearchName( cls, cookie, name ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['current']['search'] = name
        cls.active_cookies[session]['modified']['search'] = False
        
    @classmethod
    def SetSearchMod( cls, cookie ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['modified']['search'] = True
        
    @classmethod
    def GetSearchMod( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['modified']['search']
