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
    
import first

class ProcessState:
    lastSearch = None
    def FieldDict( self, dictionary ):
        d = {}
        for k in dictionary:
            if k in first.SQL_table.field_list:
                d[k] = dictionary[k]
        return d

class EmptyState(ProcessState):
    @property
    def button_lists( self ):
        return ['research','search'],['add','reset','cancel']

class EditState(ProcessState):
    @property
    def button_lists( self ):
        return ['research','delete','new','copy'],['search','save','reset']

class SearchState(ProcessState):
    def __init__(self, dictionary):
        d = self.FieldDict( dictionary )
        type(self).lastSearch = d
        self.list = first.SQL_record.SearchDict( d )
        self.index = -1
        if self.list is None:
            self.length = 0
        else:
            self.length = len(self.list)
        
    @property
    def first( self ):
        if self.length == 0:
            return None
        else:
            self.index = 0
            return self.list[0]
        
    @property
    def next( self ):
        self.index += 1
        if self.index <0 or self.length==0:
            return self.first()
        elif self.index == self.length:
            self.index -= 1
        return self.list[self.index]
    
    @property
    def back( self ):
        self.index -= 1
        if self.index <0 or self.length==0:
            return self.first()
        return self.list[self.index]

    def _status( self ):
        return 'Search {} of {} matching records'.format(self.index+1,self.length)

    @property
    def button_lists( self ):
        if self.length == 0:
            # Null search result
            return ['research','new','cancel' ],['search','save','next','back']
        elif self.length == 1:
            #single result
            return ['research','cancel', 'delete' ],['search','save','next','back','copy','delete']
        elif self.index == 0:
            # at start
            return ['research','next','cancel', 'delete' ],['search','save','back','copy','delete']
        elif self.index == self.length-1:
            # at end
            return ['research','cancel', 'back','delete' ],['search','save','next','copy','delete']
        else:
            return ['research','cancel', 'next','back','delete' ],['search','save','copy','delete']

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
        'reset'    : ( 14, '#EDA9FB' , 'Reset entries' ),
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
        searchstate = None
    
    def __init__( self, *args, **kwargs ):
        self.pstate = EmptyState()
        self.last_formdict = {}
        self.last_searchdict={}
        super().__init__( *args, **kwargs )
    
    def statusBar( self, id_text='', text=''  ):
        self.wfile.write('<TABLE width=100% class=htable><TR>'.encode('utf-8') )
        self.wfile.write('<TD>Total: {}</TD>'.format(first.SQL_record.total).encode('utf-8') )
        self.wfile.write('<TD>Added: {}</TD>'.format(first.SQL_record.added).encode('utf-8') )
        self.wfile.write('<TD>Changed: {}</TD>'.format(first.SQL_record.updated).encode('utf-8') )
        self.wfile.write('<TD>Deleted: {}</TD>'.format(first.SQL_record.deleted).encode('utf-8') )
        self.wfile.write('</TR><TR><TD>{}</TD><TD colspan=3>{}</TD>'.format(id_text,text).encode('utf-8') )
        self.wfile.write('</TR></TABLE><BR>'.encode('utf-8') )
    
    def do_GET(self):        
        # Parse out special files
        if self.path == '/style.css':
            return self.CSS()
        elif self.path == '/favicon.ico':
            return self.ICON()

        # Begin the response
        self._head()
        self.wfile.write('<head><link href="/style.css" rel="stylesheet" type="text/css"></head>'.encode('utf-8'))
        self.wfile.write('<body><div class="firststyle"><pre>{}</pre>'.format(self._get_message()).encode('utf-8'))
        self.FORM({})
        self.wfile.write('</div></body>'.encode('utf-8'))


    def do_POST(self):
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
        self.wfile.write(('<pre>{}</pre>'.format(self._form_message(form))).encode('utf-8'))

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
            formdict['button'] = "Edit"
        
        if formdict['button'] == "Reset":
            formdict = self.last_formdict
            if 'button' is in formdict and formdict['button'] == 'Reset':
                formdict['button'] = 'Edit' # No infinite loop
            self.statusBar( '', 'Reset record')
            return self.FORM( formdict )
        elif formdict['button'] == 'Modify search':
            formdict = last_searchdict
            formdict['button'] = 'Edit'
        elif formdict['button'] == 'Next':
            pass
        elif formdict['button'] == 'Previous':
            pass
        elif formdict['button'] == 'Search':
            
            pass
        elif formdict['button'] == 'Add':
            if SQL_record.IsEmpty( formdict ):
                self.statusBar( '', 'Empty record not added')
                formdict['button'] = 'Edit'
                formdict['_Id'] = None
            else:
                ID = SQL_record.Insert(formdict)
                self.statusBar( 'Record {}'.format(ID), 'Record Added')
                formdict['button'] = 'Edit'
                formdict['_ID'] = ID
        elif formdict['button'] == 'Cancel' or formdict['button'] == 'New':
            SQL_record.RemoveFields( formdict )
                formdict['button'] = 'Edit'
                formdict['_Id'] = None
                self.statusBar( ''.format(ID), 'Enter record or search')
        else:
            ID = None
            self.pstate = EmptyState()
            
        # for Reset    
        self.last_formdict = formdict

        self.statusBar()
        self.wfile.write(self._changescript().encode('utf-8') )
        self.wfile.write( ('<form action="' + self.path + '" method="post"><table width=100%>').encode('utf-8') )
        if ID is None:
            self.pstate=EmptyState()
            for f in DbaseField.flist:
                self._textfield( f,'' )
        else:
            self.wfile.write( ('<input type="hidden" name="_ID" value="{}" >').format(ID).encode('utf-8') )
            for f,v in zip(DbaseField.flist,first.SQL_record.FindID(ID)):
                self._textfield( f,v )
        print('debug',self.pstate,self.pstate.button_lists)
        self.wfile.write( ('<td></td><td>{}</td>').format(self.BUTTONS(*self.pstate.button_lists)).encode('utf-8') )
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
            print(bname,' disabled')
            return '<input id={} name="{}" type="submit" style="background-color:{}" value="{}" disabled>'.format(bname,bname,type(self).buttondict[bname][1],type(self).buttondict[bname][2])
        else:
            print(bname,' enabled')
            return '<input id={} name="{}" type="submit" style="background-color:{}" value="{}">'.format(bname,bname,type(self).buttondict[bname][1],type(self).buttondict[bname][2])
    
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
    Able("cancel",true);
    Able("copy",false);
    Able("delete",false);
    Able("new",false);
    Able("next",false);
    Able("research",false);
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
            print(field,form[field].value)
            # Regular form value
            message_parts.append('%s=%s<br>' % (field, form[field].value))
        message_parts.append('')
        return '\r\n'.join(message_parts)

    def _get_message( self ):
        parsed_path = parse.urlparse(self.path)
        print("PP:",type(parsed_path),parsed_path)
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
        self.end_headers()
    
    def CSS( self ):
        # Begin the response
        self._head()
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
        
if __name__ == '__main__':
    
    addr = 'localhost'
    port = 8080
    
    dbase_class = first.OpenDatabase('../wines.fol')
    DbaseField.Generate(dbase_class)    

    try:
        server = HTTPServer((addr, port), GetHandler)
    except:
        print("Could not start server -- is another instance already using that port?")
        exit()
    print('Starting server address={} port={}, use <Ctrl-C> to stop'.format(addr,port))

    with open('favicon.ico','rb') as f:
        icon_data = f.read()


    server.serve_forever()
