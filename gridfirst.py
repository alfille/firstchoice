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
        self._list = [ID[0] for ID in first.SQL_record.SearchDict( self.last_dict )]
        self._index = -1
        if self._list is None:
            self._length = 0
        else:
            self._length = len(self._list)
            #print("Search list",self._list)
        
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
        #print("Next",self._index,self._list)
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
        return self._list[self._index]

    @property
    def list(self):
        return self._list

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
    def SetLast( cls, cookie, lastdict ):
        session = cls.GetSession( cookie )
        #print("setlast",lastdict) 
        cls.active_cookies[session]['last'] = lastdict 

    @classmethod
    def GetLast( cls, cookie ):
        session = cls.GetSession( cookie )
        #print("getlast",cls.active_cookies[session]['last'])
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
        'reset'    : ( '#EDA9FB', 'Reset entries' ),
        'table'    : ( '#8CD7EE', 'Table view' ),
        'search'   : ( '#8CD7EE', 'Search' ),
        'research' : ( '#8CD7EE', 'Modify search' ),
        'next'     : ( '#8CD7EE', 'Next' ),
        'back'     : ( '#8CD7EE', 'Back' ),
        'save'     : ( '#B1FABB', 'Update' ),
        'add'      : ( '#B1FABB', 'Add' ),
        'copy'     : ( '#ECF470', 'Duplicate' ),
        'delete'   : ( '#E37791', 'Delete' ),
        'clear'   : ( '#E37791',  'Clear' ),
        'blank'    : ( '#0000A9', '' ),
        }
     
    def statusBar( self, formdict, text=''  ):
        self.wfile.write('<DIV id="head-grid">'.encode('utf-8') )

        self.wfile.write('<DIV class="hcell">Total: {}</DIV>'.format(first.SQL_record.total).encode('utf-8') )
        self.wfile.write('<DIV class="hcell">Added: {}</DIV>'.format(first.SQL_record.added).encode('utf-8') )
        self.wfile.write('<DIV class="hcell">Changed: {}</DIV>'.format(first.SQL_record.updated).encode('utf-8') )
        self.wfile.write('<DIV class="hcell">Deleted: {}</DIV>'.format(first.SQL_record.deleted).encode('utf-8') )

        if '_ID' in formdict:
            self.wfile.write('<DIV class="hcell">Record = {}</DIV>'.format(formdict['_ID']).encode('utf-8') )
        else:
            self.wfile.write('<DIV class="hcell">Not in database</DIV>'.encode('utf-8') )
        self.wfile.write('<DIV class="hcellbig">{}</DIV>'.format(text).encode('utf-8') )
        self.wfile.write('</DIV>'.encode('utf-8') )
    
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

        # button = button name from form, translate to local index name
        button = ''
        for b in type(self).buttondict:
            if formdict['button'] == type(self).buttondict[b][1]:
                button = b
                break;
        
        if button == "table":
            return self.TABLE()
        elif button == "reset":
            # Reset special handling -- get old formdict and reprocess
            formdict = CookieManager.GetLast(self.cookie)
            formdict['button'] = 'Edit' # No infinite loop
            return self.FORM( formdict )

        # default active buttons
        actbut = ['search','clear']
        # default inactive buttons
        deactbut = ['reset']

        searchstate = CookieManager.GetSearch(self.cookie)

        if button == 'research':
            # Modify Last Search
            if searchstate is None:
                self.statusBar( formdict, 'No prior search' )

            else:
                formdict = searchstate.last_dict
                self.statusBar( formdict, 'Modify Search' )

        elif button == 'search':
            # Search
            searchstate = SearchState(formdict)
            CookieManager.SetSearch( self.cookie, searchstate )
            searchID = searchstate.first
            if searchID is None:
                # no matches
                self.statusBar( {},'Search: Not Found')
                deactbut += ['search']
                actbut.remove('search')
            else:
                formdict = first.SQL_record.IDtoDict(searchID)                
                self.statusBar( formdict,'Search: {} of {}'.format(searchstate.index,searchstate.length) )

        elif button == 'next':
            # Next in search
            if searchstate is None:
                self.statusBar( formdict, 'No prior search' )
            else:
                searchID = searchstate.next
                if searchID is None:
                    self.statusBar( {},'Search: Not Found')
                else:
                    formdict = first.SQL_record.IDtoDict(searchID)                
                    self.statusBar( formdict,'Search: {} of {}'.format(searchstate.index,searchstate.length) )
                
        elif button == 'back':
            # Previous in search
            if searchstate is None:
                self.statusBar( formdict, 'No prior search' )
            else:
                searchID = searchstate.back
                if searchID is None:
                    self.statusBar( {},'Search: Not Found')
                else:
                    formdict = first.SQL_record.IDtoDict(searchID)                
                    self.statusBar( formdict,'Search: {} of {}'.format(searchstate.index,searchstate.length) )
                
        elif button == 'add':
            # Add a Record
            if first.SQL_record.IsEmpty( formdict ):
                self.statusBar( formdict, 'Empty record not added')
                formdict['_Id'] = None
            else:
                addID = first.SQL_record.Insert( first.SQL_record.DicttoTup(formdict) )                
                formdict = first.SQL_record.IDtoDict( addID )                
                self.statusBar( formdict, 'Record Added')

        elif button == 'save':
            # Update a Record
            if '_ID' in formdict and formdict['_ID'] is not None:
                formdict['_ID'] = first.SQL_record.Update( formdict['_ID'], first.SQL_record.DicttoTup(formdict) )                
                self.statusBar( formdict, 'Record Updated')
            else:
                self.statusBar( formdict, 'Record should be <U>Added</U>')

        elif button == 'copy':
            #Copy a Record
            if '_ID' not in formdict or formdict['_ID'] is None:
                self.statusBar( formdict, 'Copy only valid for an existing record')
            else:
                formdict['_ID'] = None
                self.statusBar( formdict, 'Copy of record')

        elif button == 'clear':
            # Clear
            formdict = {}
            self.statusBar( formdict, 'Enter record or search')

        elif button == 'delete':
            # Delete
            # has pop-up window for confirmation
            if '_ID' not in formdict or formdict['_ID'] is None:
                self.statusBar( formdict, 'Delete only valid for an existing record')
            else:
                first.SQL_record.Delete( formdict['_ID'])
                formdict['_ID'] = None
                self.statusBar( formdict, 'Record deleted')

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
            deactbut += ['save','add']
        else:
            # not existing record
            actbut += ['save','add']
            deactbut += ['copy','delete']

        if searchstate is not None:
            # old search
            actbut += ['research']
            if searchstate.length > 0 :
                # valid search
                actbut += ['next','back']

        first.SQL_record.PadFields( formdict )

        self.wfile.write(self._changescript().encode('utf-8') )
        #self.wfile.write( ('<form action="{}" method="post" id="mainform"><table width=100%>').format(self.path).encode('utf-8') )
        self.wfile.write( ('<form action="{}" method="post" id="mainform"><div id="form-grid">').format(self.path).encode('utf-8') )
        if formdict['_ID'] is not None:
            self.wfile.write( ('<input type="hidden" name="_ID" value="{}" >').format(formdict['_ID']).encode('utf-8') )
        for f in DbaseField.flist:
            self._textfield( f,formdict[f.field] )
        self.wfile.write( ('<div class="lcellb">{}</div><div class="rcell">{}</div>').format(self._tablebutton(),self._buttons(actbut,deactbut)).encode('utf-8') )
        self.wfile.write( ('</div></form>').encode('utf-8') )
        
    def _textfield( self, datafield, fval ):
        # part of form
        #print("textfield",datafield,datafield.field,fval)
        self.wfile.write( '<div class="lcell"><label for="{}" class="texta"> {}: </label></div>'.format(datafield.field,datafield.field.replace("_"," ")).encode('utf-8') ) 
        if datafield.final:
            self.wfile.write( ('<div class="rcell"><textarea rows=6 cols=78 name=\"{}\" id=\"{}\ autocomplete="on" autocapitalize="none" oninput="ChangeData()">'.format(datafield.field,datafield.field,) + fval + '</textarea></div>').encode('utf-8') ) 
        else:
            self.wfile.write( ('<div class="rcell"><textarea rows={} cols=78 name=\"{}\" id=\"{}\ maxlength={}" autocomplete="on" autocapitalize="none" oninput="ChangeData()">'.format(datafield.lines,datafield.field,datafield.field,datafield.length+datafield.lines) + fval + '</textarea></div>').encode('utf-8') ) 
        
    def TABLE( self ):
        #self.wfile.write(self._scrollscript().encode('utf-8') )
        self.wfile.write( '<div id="ttable">'.encode('utf-8') )
        for f in DbaseField.flist:
            self.wfile.write('<div class="thead">{}</div>'.format(f.field).replace('_',' ').encode('utf-8') )             

        searchstate = CookieManager.GetSearch(self.cookie)
        if searchstate is None or searchstate.length==0:
            searchstate = SearchState({})
            CookieManager.SetSearch( self.cookie, searchstate )

        for i in searchstate.list:
            print(i)
            for f in first.SQL_record.FindID( i ):
                self.wfile.write( '<div class="tcell">{}</div>'.format(f).encode('utf-8') ) 

        self.wfile.write( '</div>'.encode('utf-8') ) 
        
        
    def _tablebutton( self ):
        b = 'table'
        d = type(self).buttondict[b]
        return '<input id={} name="button" type="submit" style="background-color:{}" value="{}">'.format(b,d[0],d[1])
        
    def _buttons( self, active_buttons, disabled_buttons ):
        blist=''
        bd = type(self).buttondict
        nb = 'blank'
        nd = bd[nb]
        for b in ['search','next','back','research','blank','reset','copy','add','save','delete','blank','clear']:
            d = bd[b]
            if b == 'delete':
                if b in active_buttons:
                    blist += '<input id={} name="button" onClick="DeleteRecord()" type="button" style="background-color:{}" value="{}">'.format(b,d[0],d[1])
                elif b in disabled_buttons:
                    blist += '<input id={} name="button" onClick="DeleteRecord()" type="button" style="background-color:{}" value="{}" disabled>'.format(b,d[0],d[1])
                else:
                    blist += '<input id={} name="button" type="submit" style="background-color:{}" value="{}" disabled>'.format(nb,nd[0],nd[1])
            else:
                if b in active_buttons:
                    blist += '<input id={} name="button" type="submit" style="background-color:{}" value="{}">'.format(b,d[0],d[1])
                elif b in disabled_buttons:
                    blist += '<input id={} name="button" type="submit" style="background-color:{}" value="{}" disabled>'.format(b,d[0],d[1])
                else:
                    blist += '<input id={} name="button" type="submit" style="background-color:{}" value="{}" disabled>'.format(nb,nd[0],nd[1])
        return blist

    def _changescript( self ):
        return '''
<script>
function Able(n,v) {
    var x=document.getElementById(n);
    if (x !==null) {x.disabled=!v}
};
function ChangeData() {
    Able("add",true);
    Able("back",false);
    Able("copy",false);
    Able("delete",false);
    Able("clear",true);
    Able("next",false);
    Able("research",true);
    Able("reset",true);
    Able("save",true);
    Able("search",true);
};
function DeleteRecord() {
    var x = confirm("Do you want to delete the record?");
    var d = document.getElementById("delete");
    if ( x == true ) {
        d.setAttribute('type','submit');
        d.value = "Delete";
        document.getElementBiId("mainform").submit();
        }
};</script>'''

    def _scrollscript( self ):
        return '''
<script>
    window.onscroll = function() {myFunction()};

    var header = document.getElementById("myHeader");
    var sticky = header.offsetTop;

    function myFunction() {
        if (window.pageYOffset > sticky) {
            header.classList.add("sticky");
        } else {
            header.classList.remove("sticky");
        }
    }
</script>'''

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
                         'text/css; charset=utf-8')
        self.end_headers()
        self.wfile.write('''
body {
    font-size: 100%
    }
.firststyle {
    background-color:#0000A9;
    font-family: "Lucida Console", Monaco, monospace;
    font-size: 1.5em;
    letter-spacing: 2px;
    word-spacing: 2px;
    color: #A9A9A9;
    font-weight: normal;
    text-decoration: none;
    font-style: normal;
    font-variant: normal;
    text-transform: none;
    }
.texta {
    background-color: #00A9A9;
    color:black;
    }
textarea, input {
    font-size: 1.0em;
    }
#head-grid {
    display: grid;
    grid-template-columns: auto auto auto auto;
    background-color: #CC00CC;
    color: #CC00CC;
    grid-gap: 6px;
}
div.hcell {
    background-color:#0000A9;
    color: #00A9A9;
}    
div.hcellbig {
    background-color:#0000A9;
    color: #00A9A9;
    grid-column-start: 2;
    grid-column-end: 5;
}    
#form-grid {
    display: grid;
    grid-template-columns: auto 80em;
    background-color:#0000A9;
}
div.lcell {
    background-color: #00A9A9;
    color:black;
    text-align: right;
}
div.rcell {
    background-color:#0000A9;
    color:black;
    text-align: left;
}
dev.lcellb {
    background-color: #00A9A9;
    color:black;
    text-align: left;
    vertical-align: bottom;
}
#table-header {
    background-color: #CC00CC;
    color: #CC00CC;
}
#table-content {
  padding: 16px;
}
#table-sticky {
  position: fixed;
  top: 0;
  width: 100%;
}
#table-sticky + #table-content {
  padding-top: 102px;
}
div.thead {
    background-color: #00A9A9;
    color:black;
}
div.tcell {
    background-color:#0000A9;
    color:yellow;
}
'''.encode('utf-8') )
        self.wfile.write('#ttable {{ display: grid; grid-template-columns: Repeat({},auto);grid-column-gap:2px;background-color:#0000A9; }}'.format(len(DbaseField.flist)).encode('utf-8') )
        
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
