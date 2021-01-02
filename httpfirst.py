# http_server_GET.py

try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
except:
    print("Please install http.server module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
try:
    from urllib import parse
except:
    print("Please install the urllib module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
try:
    import cgi
except:
    print("Please install the cgi module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
try:
    import random
except:
    print("Please install the random module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
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
    
import first


class SearchState:
    def __init__(self, dictionary):
        self._last_dict = self.FieldDict( dictionary )
        self.list = [ID[0] for ID in first.SQL_record.SearchDict( self.last_dict )]
        self._index = -1
        if self.list is None:
            self._length = 0
        else:
            self._length = len(self.list)
            #print("Search list",self.list)
        
    def FieldDict( self, dictionary ):
        d = {}
        for k in dictionary:
            if k in first.SQL_table.field_list:
                d[k] = dictionary[k]
        return d
        
    @property
    def last_dict(self):
        return self._last_dict

    @property
    def first( self ):
        if self._length == 0:
            return None
        else:
            self._index = 0
            return self.list[0]
        
    @property
    def next( self ):
        #print("Next",self._index,self.list)
        if self._length == 0:
            return None

        self._index += 1

        return self.index_check()
    
    @property
    def back( self ):
        if self._length == 0:
            return None

        self._index -= 1

        return self.index_check()

    def index_check( self ):
        if self._index < 0:
            self._index = 0
        elif self._index >= self.length:
            self._index = self._length-1
        return self.list[self._index]

    @property
    def length( self):
        return self._length

    @property
    def index( self ):
        # Not Zero-based
        return self._index + 1

class CookieManager:
    active_cookies = {}

    @classmethod
    def GetSession( cls, cookie ):
        # creates an cookie entry if none exists
        # resets clock
        session = cookie['session'].value
        if session in cls.active_cookies:
            cls.active_cookies[session]['time'] = datetime.time()
        else:
            if len(cls.active_cookies) > 100:
                # Too long, trim oldest 30%
                t = sorted([ v['time'] for v in cls.active_cookies.values() ])[30]
                cls.active_cookies = { s:cls.active_cookies[s] for s in cls.active_cookies and cls.active_cookies[s]['time'] > t }

            # time used to trim list
            # search is a SearchState object
            # last is prior formdict
            cls.active_cookies[session] = {
                'time':datetime.time(),
                'search':None,
                'last' : {},
            }
        return session

    @classmethod
    def SetSearch( cls, cookie, searchstate ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['search'] = searchstate 

    @classmethod
    def GetSearch( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['search'] 

    @classmethod
    def SetLast( cls, cookie, last ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['last'] = last 

    @classmethod
    def GetLast( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['last'] 
        
class DbaseField:
    # Convenience class to make finding field information easier
    # Looks at the dbase_class.form object and both the fields list and the textwrap list
    # 
    flist = None

    @classmethod
    def Generate( cls, dbase_class ):
        cls.flist = [ DbaseField(f) for f in dbase_class.form['fields'] ]         

    def __init__(self,field):
        self._field = field['field'].replace(' ','_')
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
        
class GetHandler(BaseHTTPRequestHandler):
    buttondict = {
        'reset'    : ( 14, '#EDA9FB', 'Reset entries' ),
        'search'   : ( 10, '#8CD7EE', 'Search' ),
        'research' : ( 11, '#8CD7EE', 'Modify search' ),
        'next'     : ( 11, '#8CD7EE', 'Next' ),
        'back'     : ( 12, '#8CD7EE', 'Previous' ),
        'save'     : ( 13, '#B1FABB', 'Update' ),
        'add'      : ( 13, '#B1FABB', 'Add' ),
        'copy'     : ( 79, '#ECF470', 'Duplicate' ),
        'new'      : ( 20, '#B1FABB', 'New' ),
        'delete'   : ( 30, '#E37791', 'Delete' ),
        'cancel'   : ( 99, '#E37791', 'Cancel' ),
        }
     
    def statusBar( self, formdict, text=''  ):
        self.wfile.write('<TABLE width=100% class=htable><TR>'.encode('utf-8') )
        self.wfile.write('<TD>Total: {}</TD>'.format(first.SQL_record.total).encode('utf-8') )
        self.wfile.write('<TD>Added: {}</TD>'.format(first.SQL_record.added).encode('utf-8') )
        self.wfile.write('<TD>Changed: {}</TD>'.format(first.SQL_record.updated).encode('utf-8') )
        self.wfile.write('<TD>Deleted: {}</TD>'.format(first.SQL_record.deleted).encode('utf-8') )
        if '_ID' in formdict:
            self.wfile.write('</TR><TR><TD>Record = {}'.format(formdict['_ID']).encode('utf-8') )
        else:
            self.wfile.write('</TR><TR><TD>Not in database'.encode('utf-8') )
        self.wfile.write('</TD><TD colspan=3>{}</TD>'.format(text).encode('utf-8') )
        self.wfile.write('</TR></TABLE><BR>'.encode('utf-8') )
    
    def do_GET(self):        
        # Parse out special files
        if self.path == '/style.css':
            return self.CSS()
        elif self.path == '/favicon.ico':
            return self.ICON()

        self._get_cookie()

        # Begin the response
        self._head()
        self.wfile.write('<head><link href="/style.css" rel="stylesheet" type="text/css"></head>'.encode('utf-8'))
        self.wfile.write('<body><div class="firststyle">'.encode('utf-8'))
        #self.wfile.write('<pre>{}</pre>'.format(self._get_message()).encode('utf-8'))
        self.FORM({})
        self.wfile.write('</div></body>'.encode('utf-8'))


    def do_POST(self):
        self._get_cookie()

        # Parse the form data posted            
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # Begin the response
        self._head()
        self.wfile.write('<head><link href="/style.css" rel="stylesheet" type="text/css"></head>'.encode('utf-8'))
        self.wfile.write(('<body><div class="firststyle">').encode('utf-8'))
        #self.wfile.write(('<pre>{}</pre>'.format(self._post_message(form))).encode('utf-8'))

        # Write the form (with headers)
        self.FORM( { field:form[field].value for field in form.keys() } )
        self.wfile.write(('</div></body>').encode('utf-8'))
    
    def FORM( self, formdict ):
        # After a "POST" --- clicking one of the submit buttons
        # formdict has the button and field values (if entered)
        # Preserved state is pstate, last_formdict and last_searchdict
        # place in search stored in pstate SearchState
        
        # Note: initial entry is from "GET" -- with empty formdict
        
        if 'button' not in formdict:
            # Empty dictionary
            formdict['button'] = "Edit"
        
        if formdict['button'] == "Reset":
            # Reset
            formdict = CookieManager.GetLast(self.cookie)
            if 'button' in formdict and formdict['button'] == 'Reset':
                formdict['button'] = 'Edit' # No infinite loop
            self.statusBar( formdict, 'Reset record')
            return self.FORM( formdict )

        actbut = ['search','new','cancel']
        deactbut = ['add','reset']

        searchstate = CookieManager.GetSearch(self.cookie)

        if formdict['button'] == 'Modify search':
            # Modify Last Search
            if searchstate is None:
                self.statusBar( formdict, 'No prior search' )

            else:
                formdict = searchstate.last_dict
                self.statusBar( formdict, 'Modify Search' )

        elif formdict['button'] == 'Search':
            # Search
            searchstate = SearchState(formdict)
            CookieManager.SetSearch( self.cookie, searchstate )
            search = searchstate.first
            if search is None:
                self.statusBar( {},'Search: Not Found')
            else:
                formdict = first.SQL_record.IDtoDict(search)                
                self.statusBar( formdict,'Search: {} of {}'.format(searchstate.index,searchstate.length) )

        elif formdict['button'] == 'Next':
            # Next in search
            if searchstate is None:
                self.statusBar( formdict, 'No prior search' )
            else:
                search = searchstate.next
                if search is None:
                    self.statusBar( {},'Search: Not Found')
                else:
                    formdict = first.SQL_record.IDtoDict(search)                
                    self.statusBar( formdict,'Search: {} of {}'.format(searchstate.index,searchstate.length) )
                
        elif formdict['button'] == 'Previous':
            # Previous in search
            if searchstate is None:
                self.statusBar( formdict, 'No prior search' )
            else:
                search = searchstate.back
                if search is None:
                    self.statusBar( {},'Search: Not Found')
                else:
                    formdict = first.SQL_record.IDtoDict(search)                
                    self.statusBar( formdict,'Search: {} of {}'.format(searchstate.index,searchstate.length) )
                
        elif formdict['button'] == 'Add':
            # Add a Record
            if first.SQL_record.IsEmpty( formdict ):
                self.statusBar( formdict, 'Empty record not added')
                formdict['_Id'] = None
            else:
                formdict = first.SQL_record.IDtoDict( first.SQL_record.Insert(first.SQL_record.DicttoTup(formdict)) )                
                self.statusBar( formdict, 'Record Added')

        elif formdict['button'] == 'Copy':
            #Copy a Record
            if '_ID' not in formdict['button'] or formdict['button'] is None:
                self.statusBar( formdict, 'Copy only valid for existing record')
            else:
                formdict['_Id'] = None
                self.statusBar( formdict, 'Copy of record')

        elif formdict['button'] == 'Cancel' or formdict['button'] == 'New':
            # Clear
            formdict = {}
            self.statusBar( formdict, 'Enter record or search')

        elif formdict['button'] == 'Delete':
            # Delete
            # not implemented yet
            # needs pop-up window and confirmation
            formdict['button'] = 'New'
            self.statusBar( formdict, 'Cannot Delete (yet)')
            return self.FORM( formdict )

        else:
            # Nothing
            self.statusBar( formdict, 'Welcome')
            
        formdict['button'] = 'Edit'    
        CookieManager.SetLast(self.cookie, formdict )

        if '_ID' not in formdict:
            formdict['_ID'] = None
            
        if formdict['_ID'] is not None:
            # existing record
            actbut += ['copy','delete']
            deactbut += ['save']

        if searchstate is not None:
            # old search
            actbut += ['research']
            if searchstate.length > 0 :
                # valid search
                actbut += ['next','back']
            else:
                deactbut += ['search']
                actbut.remove('search')

        first.SQL_record.PadFields( formdict )

        self.wfile.write(self._changescript().encode('utf-8') )
        self.wfile.write( ('<form action="' + self.path + '" method="post"><table width=100%>').encode('utf-8') )
        if formdict['_ID'] is not None:
            self.wfile.write( ('<input type="hidden" name="_ID" value="{}" >').format(formdict['_ID']).encode('utf-8') )
        for f in DbaseField.flist:
            self._textfield( f,formdict[f.field] )
        self.wfile.write( ('<td></td><td>{}</td>').format(self.BUTTONS(actbut,deactbut)).encode('utf-8') )
        self.wfile.write( ('</table></form>').encode('utf-8') )
        
    def _textfield( self, datafield, fval ):
        # part of form
        #print("textfield",datafield,datafield.field,fval)
        self.wfile.write( '<tr>'.encode('utf-8') ) 
        self.wfile.write( '<td class="tda"><label for="{}" class="texta"> {}: </label></td>'.format(datafield.field,datafield.field.replace("_"," ")).encode('utf-8') ) 
        if datafield.final:
            self.wfile.write( ('<td><textarea rows=6 cols=78 name=\"{}\" id=\"{}\ autocomplete="on" autocapitalize="none" oninput="ChangeData()">'.format(datafield.field,datafield.field,) + fval + '</textarea></td>').encode('utf-8') ) 
        else:
            self.wfile.write( ('<td><textarea rows={} cols=78 name=\"{}\" id=\"{}\ maxlength={}" autocomplete="on" autocapitalize="none" oninput="ChangeData()">'.format(datafield.lines,datafield.field,datafield.field,datafield.length+datafield.lines) + fval + '</textarea></td>').encode('utf-8') ) 
        self.wfile.write( '</tr>'.encode('utf-8') ) 
        
    def  _button( self, bname, bdisabled=False ):
        if bdisabled:
            return '<input id={} name="button" type="submit" style="background-color:{}" value="{}" disabled>'.format(bname,type(self).buttondict[bname][1],type(self).buttondict[bname][2])
        else:
            return '<input id={} name="button" type="submit" style="background-color:{}" value="{}">'.format(bname,type(self).buttondict[bname][1],type(self).buttondict[bname][2])
    
    def BUTTONS( self, active_buttons, disabled_buttons ):
        return ''.join([ self._button(n,n in disabled_buttons) for n in sorted( set( active_buttons + disabled_buttons), key=lambda b:type(self).buttondict[b][1] in disabled_buttons ) ])

    def _changescript( self ):
        return '''
<script>
function Able(n,v) {
    x=document.getElementById(n);
    if (x !==null) {x.disabled=!v}
};
function ChangeData() {
    Able("add",true);
    Able("back",false);
    Able("copy",false);
    Able("delete",false);
    Able("new",false);
    Able("next",false);
    Able("research",true);
    Able("reset",true);
    Able("save",true);
    Able("search",true);
}</script>'''

    def _post_message( self, form ):
        message_parts = [
        'Client: %s\n' % str(self.client_address),
        'User-agent: %s\n' % str(self.headers['user-agent']),
        'Path: %s\n' % self.path,
        'FORM fields:',
        ]
        # Echo back information about what was posted in the form
        for field in form.keys():
            #print(field,form[field].value)
            # Regular form value
            message_parts.append('%s=%s<br>' % (field, form[field].value))
        message_parts.append('')
        return '\r\n'.join(message_parts)

    def _get_message( self ):
        parsed_path = parse.urlparse(self.path)
        #print("PP:",type(parsed_path),parsed_path)
        message_parts = [
            'CLIENT VALUES:',
            'client_address={} ({})'.format(
                self.client_address,
                self.address_string()),
            'command={}'.format(self.command),
            'path={}'.format(self.path),
            'real path={}'.format(parsed_path.path),
            'query={}'.format(parsed_path.query),
            'request_version={}'.format(self.request_version),
            '',
            'SERVER VALUES:',
            'server_version={}'.format(self.server_version),
            'sys_version={}'.format(self.sys_version),
            'protocol_version={}'.format(self.protocol_version),
            '',
            'HEADERS RECEIVED:',
        ]
        for name, value in sorted(self.headers.items()):
            message_parts.append(
                '{}={}'.format(name, value.rstrip())
            )
        message_parts.append('')
        return '\r\n'.join(message_parts)

    def _head( self ):
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/html; charset=utf-8')
        # cookie part
        if self.cookie is None:
            self._set_cookie()
        for morsel in self.cookie.keys():
            self.send_header("Set-Cookie", self.cookie[morsel].OutputString())

        self.end_headers()
    
    def CSS( self ):
        # Begin the response
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write('''
body {
    font-size: 100%
    }
.firststyle {
    background-color:#0000A9;
    font-family: "Lucida Console", Monaco, monospace;
    font-size: 2.0em;
    letter-spacing: 2px;
    word-spacing: 2px;
    color: #A9A9A9;
    font-weight: normal;
    text-decoration: none;
    font-style: normal;
    font-variant: normal;
    text-transform: none;
    }
.htable {
    color: #00A9A9;
    }
.tda {
    text-align: right;
    }
.texta {
    background-color: #00A9A9;
    color:black;
    }
table {
    border: 5px;
    border-color: #A95500;
    font-size: 1.0em;
    border-collapse: separate;
    }
td {
    vertical-align: top;
    }
textarea, input {
    font-size: 1.0em;
    }

'''.encode('utf-8')
        )
        
    def ICON( self ):
        self.send_response(200)
        self.send_header('Content-Type',
                         'image/x-icon; charset=utf-8')
        self.end_headers()
        global icon_data
        self.wfile.write(icon_data)

    def _get_cookie( self ):
        head_cook = self.headers.get('Cookie')
        #print(head_cook)
        if head_cook:
            self.cookie = cookies.SimpleCookie(head_cook)
            if "session" not in self.cookie:
                #print('Bad cookie: no "session" entry')
                self.cookie = None
            else:
                pass
                #print("session = ", self.cookie["session"].value)
        else:
            print("session cookie not set!")
            self.cookie = None

    def _set_cookie( self ):
        expiration = datetime.datetime.now() + datetime.timedelta(days=7)
        self.cookie = cookies.SimpleCookie()
        self.cookie["session"] = random.randint(1,1000000000)
        self.cookie["session"]["expires"] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S EST")
#        cookie["session"]["samesite"] = "Strict"

if __name__ == '__main__':
    
    addr = 'localhost'
    port = 8080
    
    dbase_class = first.OpenDatabase('../wines.fol')
    DbaseField.Generate(dbase_class)
    first.ArgSQL = 1    

    try:
        server = HTTPServer((addr, port), GetHandler)
    except:
        print("Could not start server -- is another instance already using that port?")
        exit()
    print('Starting server address={} port={}, use <Ctrl-C> to stop'.format(addr,port))

    with open('favicon.ico','rb') as f:
        icon_data = f.read()


    server.serve_forever()
