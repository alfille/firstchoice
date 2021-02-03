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
    
try:
    import csv
except:
    print("Please install the csv module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
import sqlfirst
import persistent
import searchstate
import sqltable

try:
    import textwrap
except:
    print("Please install the textwrap module")
    print("\tit should be part of the standard python3 distribution")
    raise

# Connection to persistent_state database
persistent_state_state = None

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

            global persistent_state_state
            ps = persistent_state_state.GetSearch("default")
            ts = persistent_state_state.GetTable("default")
            if ts is None:
                ts = [(sqlfirst.SqlField(f.field),"1fr") for f in DbaseField.flist]
                persistent_state_state.SetTable( "default", ts )

            # time used to trim list
            # search is a SearchState object
            # last is prior formdict
            # table is list of fields and sizes
            cls.active_cookies[session] = {
                'time':datetime.time(),
                'search':ps,
                'last' : {},
                'table':ts,
                'current': { 'search':'default', 'table':'default', },
                'modified': { 'search':False, 'table':False, },
            }
        return session

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
        cls.active_cookies[session]['table']=[(sqlfirst.SqlField(f.field),"1fr") for f in DbaseField.flist]
        
    @classmethod
    def GetTable( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['table']
        
    @classmethod
    def SetTable( cls, cookie, table ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['table'] = table
        
    @classmethod
    def GetTableName( cls, cookie ):
        session = cls.GetSession( cookie )
        return cls.active_cookies[session]['current']['table']
        
    @classmethod
    def SetTableName( cls, cookie, name ):
        session = cls.GetSession( cookie )
        cls.active_cookies[session]['current']['table'] = name
        cls.active_cookies[session]['modified']['table'] = False
        
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
        
class DbaseField:
    # Convenience class to make finding field information easier
    # Looks at the dbase_class.form object and both the fields list and the textwrap list
    # 
    flist = None

    @classmethod
    def Generate( cls, dbase_class ):
        cls.flist = [ DbaseField(f) for f in dbase_class.form['fields'] ]         

    def __init__(self,field):
        self._field = sqlfirst.SqlField(field['field'])
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
        'reset'    : 'Reset entries',
        'table'    : 'Table view',
        'search'   : 'Search',
        'savesearch': 'Save search',
        'getsearch': 'Get search',
        'research' : 'Modify search',
        'next'     : 'Next',
        'back'     : 'Back',
        'save'     : 'Update',
        'add'      : 'Add',
        'copy'     : 'Duplicate',
        'delete'   : 'Delete',
        'clear'    : 'Clear',
        'id'       : 'id',
        'resize'   : 'resize',
        }
     
    def _searchBar( self, formdict, active_search ):
        self._statusBar( formdict,'<meter value={0} min=1 max={1}></meter> Search: {0} of {1}'.format(active_search.index,active_search.length) )


    def _statusBar( self, formdict, text=''  ):
        self.wfile.write('<DIV id="head-grid" class="firststyle">'.encode('utf-8') )

        self.wfile.write('<DIV class="hcell">Total: {}</DIV>'.format(sqltable.SQL_record.total).encode('utf-8') )
        self.wfile.write('<DIV class="hcell">Added: {}</DIV>'.format(sqltable.SQL_record.added).encode('utf-8') )
        self.wfile.write('<DIV class="hcell">Changed: {}</DIV>'.format(sqltable.SQL_record.updated).encode('utf-8') )
        self.wfile.write('<DIV class="hcell">Deleted: {}</DIV>'.format(sqltable.SQL_record.deleted).encode('utf-8') )

        if '_ID' in formdict:
            self.wfile.write('<DIV class="hcell">Record = {}</DIV>'.format(formdict['_ID']).encode('utf-8') )
        else:
            self.wfile.write('<DIV class="hcell">Not in database</DIV>'.encode('utf-8') )
        self.wfile.write('<DIV class="hcellbig">{}</DIV>'.format(text).encode('utf-8') )
        self.wfile.write('</DIV>'.encode('utf-8') )
    
    def do_GET(self):        
        # Parse out special files
        if self.path == '/formstyle.css':
            return self.FORMCSS()
        elif self.path == '/tablestyle.css':
            self._get_cookie()
            return self.TABLECSS()
        elif self.path == '/favicon.ico':
            return self.ICON()
        elif self.path.endswith(".csv"):
            return self.CSV()

        self._get_cookie()

        self.PAGE({})


    def do_POST(self):
        self._get_cookie()

        # Parse the form data posted            
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        #self.wfile.write(('<pre>{}</pre>'.format(self._post_message(form))).encode('utf-8'))

        # Write the form (with headers)
        print(self._get_message())
        self.PAGE( { field:form[field].value for field in form.keys() } )
    
    def PAGE( self, formdict ):
        global persistent_state_state

        # Begin the response
        self._head()
       
        # Send to record or table view

        # Note: initial entry is from "GET" -- with empty formdict        
        if 'button' not in formdict:
            # Empty dictionary
            formdict['button'] = "Edit"
        
        if formdict['button'] == type(self).buttondict['table']:
            if "table_type" in formdict:
                ttype = formdict['table_type']
                t0 = formdict['table_0']
                t1 = formdict['table_1']
                table = CookieManager.GetTable(self.cookie)
                if ttype == "reset":
                    CookieManager.ResetTable( self.cookie )
                elif ttype == "cancel":
                    pass
                elif ttype == "resize":
                    table[t0][1] = t1
                elif ttype == "remove":
                    if len(table) > 1:
                        del( table[t0] )
                elif ttype == "select":
                    nlist = t0.split(',')
                    if len(nlist) > 0:
                        flist = [f[0] for f in table]
                        # Add new fields
                        for n in nlist:
                            if n not in flist:
                                table.append( (n,"1fr") )
                        # Remove extra fields (back to front)
                        for i in range(len(table)-1,-1,-1):
                            if table[i][0] not in nlist:
                                del(table[i])
                        CookieManager.SetTableMod( self.cookie )
                elif ttype == "move":
                    # from 0 to before 1
                    t0 = int(t0)
                    t1 = int(t1)
                    e = table[t0]
                    table.remove(e)
                    table.insert(t1,e)
                elif ttype == "restore":
                    table.append( (t0,"1fr") )
                elif ttype == "choose":
                    CookieManager.SetTableName( self.cookie, t0 )
                    CookieManager.SetTable( self.cookie, persistent_state_state.GetTable(t0) )
                elif ttype == "name":
                    CookieManager.SetTableName( self.cookie, t0 )
                    persistent_state_state.SetTable( t0, table )
                elif ttype == 'tremove':
                    if t0 != "default": # cannot delete default
                        persistent_state_state.SetTable( t0, None ) # deletes
                        if t0 == CookieManager.GetTableName( self.cookie ): # change existing to default
                            CookieManager.SetTableName( self.cookie, "default" )
                            CookieManager.SetTable( self.cookie, persistent_state_state.GetTable("default") )
                elif ttype == 'trename':
                    if t0 != t1:
                        table = persistent_state_state.GetTable(t0)
                        persistent_state_state.SetTable( t1, table )
                        if t0 != "default": # cannot delete default
                            persistent_state_state.SetTable( t0, None ) # deletes
                        tcurrent = CookieManager.GetTableName( self.cookie )
                        if t0 == tcurrent or t1 == tcurrent: # change current part of rename
                            CookieManager.SetTableName( self.cookie, t1 )
                            CookieManager.SetTable( self.cookie, table )
                elif ttype == 'widths':
                    wid = t0.split(',')
                    if len(wid) == len(table):
                        table = list(zip([t[0] for t in table],wid))
                        tname = CookieManager.GetTableName( self.cookie )
                        persistent_state_state.SetTable( tname, table )
                        CookieManager.SetTableName( self.cookie, tname ) # to clear mod
                        CookieManager.SetTable( self.cookie, table )
                            
            self.wfile.write('<head>'\
                '<link href="/tablestyle.css" rel="stylesheet" type="text/css">'\
                '</head>'.encode('utf-8'))
            self.wfile.write('<meta name="viewport" content="width=device-width, initial-scale=1">'.encode('utf-8'))
            self.wfile.write('<body>'.encode('utf-8') )
            self.TABLE()

        else:
            self.wfile.write('<head>'\
                '<link href="/formstyle.css" rel="stylesheet" type="text/css">'\
                '</head>'.encode('utf-8'))
            if formdict['button'] == type(self).buttondict['reset']:
                formdict = CookieManager.GetLast(self.cookie)
                formdict['button'] = 'Edit' # No infinite loop
            self.wfile.write('<meta name="viewport" content="width=device-width, initial-scale=1">'.encode('utf-8'))
            self.wfile.write('<body>'.encode('utf-8'))
            self.FORM( formdict )

        self.wfile.write('</body>'.encode('utf-8'))

    def FORM( self, formdict ):
        # After a "POST" --- clicking one of the submit buttons
        # formdict has the button and field values (if entered)
        # Preserved state is pstate, last_formdict and last_searchdict
        # place in search stored in pstate SearchState
        
        # button = button name from form, translate to local index name
        print("formdict",formdict)
        button = ''
        for b in type(self).buttondict:
            if formdict['button'] == type(self).buttondict[b]:
                button = b
                break;
        
        # default active buttons
        actbut = ['search','clear']
        # default inactive buttons
        deactbut = ['reset']

        active_search = CookieManager.GetSearch(self.cookie)

        if button == 'research':
            # Modify Last Search
            if active_search is None:
                self._statusBar( formdict, 'No prior search' )

            else:
                formdict = active_search.last_dict
                self._statusBar( formdict, 'Modify Search' )

        elif button == 'search':
            # Search
            active_search = searchstate.SearchState(formdict)
            CookieManager.SetSearch( self.cookie, active_search )
            searchID = active_search.first
            if searchID is None:
                # no matches
                self._statusBar( {},'Search: Not Found')
                deactbut += ['search']
                actbut.remove('search')
            else:
                formdict = sqltable.SQL_record.IDtoDict(searchID)                
                self._searchBar( formdict,active_search )

        elif button == 'next':
            # Next in search
            if active_search is None:
                self._statusBar( formdict, 'No prior search' )
            else:
                searchID = active_search.next
                if searchID is None:
                    self._statusBar( {},'Search: Not Found')
                else:
                    formdict = sqltable.SQL_record.IDtoDict(searchID)                
                    self._searchBar( formdict,active_search )
                
        elif button == 'back':
            # Previous in search
            if active_search is None:
                self._statusBar( formdict, 'No prior search' )
            else:
                searchID = active_search.back
                if searchID is None:
                    self._statusBar( {},'Search: Not Found')
                else:
                    formdict = sqltable.SQL_record.IDtoDict(searchID)                
                    self._searchBar( formdict,active_search )
                
        elif button == 'add':
            # Add a Record
            if sqltable.SQL_record.IsEmpty( formdict ):
                self._statusBar( formdict, 'Empty record not added')
                formdict['_Id'] = None
            else:
                addID = sqltable.SQL_record.Insert( first.SQL_record.DicttoTup(formdict) )                
                formdict = sqltable.SQL_record.IDtoDict( addID )                
                self._statusBar( formdict, 'Record Added')

        elif button == 'save':
            # Update a Record
            if '_ID' in formdict and formdict['_ID'] is not None:
                formdict['_ID'] = first.SQL_record.Update( formdict['_ID'], first.SQL_record.DicttoTup(formdict) )                
                self._statusBar( formdict, 'Record Updated')
            else:
                self._statusBar( formdict, 'Record should be <U>Added</U>')

        elif button == 'copy':
            #Copy a Record
            if '_ID' not in formdict or formdict['_ID'] is None:
                self._statusBar( formdict, 'Copy only valid for an existing record')
            else:
                formdict['_ID'] = None
                self._statusBar( formdict, 'Copy of record')

        elif button == 'clear':
            # Clear
            formdict = {}
            self._statusBar( formdict, 'Enter record or search')

        elif button == 'delete':
            # Delete
            # has pop-up window for confirmation
            if '_ID' not in formdict or formdict['_ID'] is None:
                self._statusBar( formdict, 'Delete only valid for an existing record')
            else:
                sqltable.SQL_record.Delete( formdict['_ID'])
                formdict['_ID'] = None
                self._statusBar( formdict, 'Record deleted')

        elif button == 'id':
            # Back from Table with just record Id -- need to populate
            if '_ID' in formdict and formdict['_ID'] is not None:
                formdict = sqltable.SQL_record.IDtoDict( formdict['_ID'] )
                self._statusBar( formdict, "Record selected" )
            else:
                self._statusBar( formdict, "Record not selected" )

        else:
            # Nothing
            self._statusBar( formdict, 'Welcome')
            
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

        if active_search is not None:
            # old search
            actbut += ['research']
            if active_search.length > 0 :
                # valid search
                actbut += ['next','back']

        sqltable.SQL_record.PadFields( formdict )

        self.wfile.write(self.FORMSCRIPT().encode('utf-8') )
        self.wfile.write('<br><form action="{}" method="post" id="mainform">'.format(self.path).encode('utf-8') )
        if formdict['_ID'] is not None:
            self.wfile.write( '<input type="hidden" name="_ID" value="{}" >'.format(formdict['_ID']).encode('utf-8') )

        
        # Fields
        self.wfile.write('<div id="form-grid" class="firststyle">'.format(self.path).encode('utf-8') )
        for f in DbaseField.flist:
            self._textfield( f,formdict[f.field] )
        self.wfile.write( ('</div>').encode('utf-8') )

        # Buttons
        self.wfile.write('<div id=buttons>{}</div>'.format(self._buttons(actbut,deactbut)).encode('utf-8') )
        self.wfile.write( ('</form>').encode('utf-8') )
        
    def _textfield( self, datafield, fval ):
        # part of form
        self.wfile.write(
            '<div class="lcell">'\
            '<label for="{}" class="texta">{}:</label>'\
            '</div>'.format(datafield.field,sqlfirst.PrintField(datafield.field[:10])).encode('utf-8') ) 
        if datafield.final:
            self.wfile.write(
                '<div class="rcell">'\
                '<textarea rows=6 cols=78 name="{}" id="{}" autocomplete="on" autocapitalize="none" oninput="ChangeData()">'\
                '{}</textarea>'\
                '</div>'.format(datafield.field,sqlfirst.PrintField(datafield.field),fval).encode('utf-8') )
        elif len(fval) > 0:
            lines = len(fval.split('\n'))
            if lines < datafield.lines:
                lines = datafield.lines
            self.wfile.write(
                '<div class="rcell">'\
                '<textarea rows={} cols=78 name="{}" id="{}" maxlength={} autocomplete="on" autocapitalize="none" oninput="ChangeData()">'\
                '{}</textarea>'\
                '</div>'.format(lines,datafield.field,datafield.field,datafield.length+datafield.lines,fval).encode('utf-8') )              
        else:
            self.wfile.write(
                '<div class="rcell">'\
                '<textarea rows={} cols=78 name="{}" id="{}" maxlength={} autocomplete="on" autocapitalize="none" oninput="ChangeData()">'\
                '{}</textarea>'\
                '</div>'.format(datafield.lines,datafield.field,datafield.field,datafield.length+datafield.lines,fval).encode('utf-8') ) 
        
    def TABLE( self ):
        global persistent_state_state

        # script
        self.wfile.write(self.TABLESCRIPTpre().encode('utf-8') )

        # Get field list
        table = CookieManager.GetTable(self.cookie)
        
        # hidden form choose a line for FORM
        self.wfile.write(
            '<form action={} method="post" id="ID">'\
            '<input type="hidden" name="_ID" id="_ID">'\
            '<input type="hidden" name="button" value="id">'\
            '</form>'.format(self.path).encode('utf-8') )

        # hidden form resize etc.. for replot TABLE
        self.wfile.write(
            '<form action={} method="post" id="table_back">'\
            '<input type="hidden" name="table_type" id="table_type" value="0">'\
            '<input type="hidden" name="table_0" id="table_0" value="0">'\
            '<input type="hidden" name="table_1" id="table_1" value="0">'\
            '<input type="hidden" name="button" value="{}">'\
            '</form>'.format(self.path,type(self).buttondict['table']).encode('utf-8') )

        # Flex container
        self.wfile.write('<div class="tallflex">'.encode('utf-8') )        

        #dialog (hidden)
        table_now = CookieManager.GetTableName(self.cookie)
        if CookieManager.GetTableMod(self.cookie):
            table_now += " (modified)"
        self.wfile.write(
            '<div id="tabledialog">'\
                '<center><h2>Table formatting management</h2></center>'\
                '<h3>Currrent format: {}</h3>'\
                '<div class="wideflex">'\
                    '<div class="tallflex">{}</div>'\
                    '<div class="tallflex">{}</div>'\
                    '<div class="tallflex">'\
                    '<button type="button" onClick="fColumns()" class="dialogbutton">Save Column Sizes</button>'\
                    '{}'\
                    '<button type="button" onClick="fReset()" class="dialogbutton">Reset Fields</button>'\
                    '<button type="button" onClick="fCancel()" class="dialogbutton">Cancel</button>'\
                    '</fieldset></div>'\
                '</div>'\
            '</div>'.format(table_now, self._tablefields(table), self._tablechoose(), self._tablename() ).encode('utf-8') )
        
        # Status and menu
        self.wfile.write(
            '<div id="tstatus">'\
            '<button id="bhead" onClick="showDialog()">Menu...</button>'\
            ' <a class="tlink" href="{}.csv" download>CSV file</a> '\
            '<span id="status"></span>'\
            '</div>'.format(parse.quote(table_now)).encode('utf-8') )

        # Table header
        self.wfile.write( '<div class="ttable">'.encode('utf-8') )
        for i,f in enumerate(table):
            self.wfile.write(
                '<div class="thead" ondrop="drop(event,{})" ondragover="allowDrop(event)" data-n="{}">'\
                '<span class="shead" draggable="true" onDragStart="dragStart(event,{})" onDragEnd="dragEnd(event)">{}</span>'\
                '</div>'.format(i,i,i,sqlfirst.PrintField(table[i][0])).encode('utf-8') )

        active_search = CookieManager.GetSearch(self.cookie)
        if active_search is None or active_search.length==0:
            active_search = searchstate.SearchState({})
            CookieManager.SetSearch( self.cookie, active_search )

        # Table contents
        stripe = False

        full_list = sqltable.SQL_record.SortedSearchDict( [f[0] for f in table], active_search.last_dict )
        for r in full_list:
            i = r[0]
            stripe = not stripe
            for f in r[1:] :
                self.wfile.write(
                    '<div class="{}" onClick="chooseFunction({})">'\
                    '{}'\
                    '</div>'.format("tcell0" if stripe else "tcell1",i, f).encode('utf-8') ) 

        self.wfile.write( '</div>'.encode('utf-8') ) 

        # End Flex container
        self.wfile.write('</div>'.encode('utf-8') )        
        
        # script
        self.wfile.write(self.TABLESCRIPTpost().encode('utf-8') )

    def _tablefields( self, table ):
        flist = [f[0] for f in table]
        checked = '<br>'.join(['<input type="checkbox" id="{}" name="dfield" value={}  onChange="FieldChanger()" checked><label for="{}">{}</label>'.format("c_"+f,f,"c_"+f,sqlfirst.PrintField(f)) for f in flist])
        unchecked = '<br>'.join(['<input type="checkbox" id="{}" name="dfield" value={} onChange="FieldChanger()"><label for="{}">{}</label>'.format("c_"+f.field,f.field,"c_"+f.field,sqlfirst.PrintField(f.field)) for f in DbaseField.flist if f.field not in flist])
        return '<fieldset id="fsfields"><legend>Choose fields shown</legend>{}'\
        '<button type="button" onClick="fSelect()" id="tablefieldok" class="dialogbutton" disabled>Ok</button>'\
        '</fieldset>'.format('<br>'.join([checked,unchecked]))
        #'<input type="button" onClick="fSelect()" id="tablefieldok" class="dialogbutton" value="Ok" disabled>'\

    def _tablechoose( self ):
        global persistent_state_state
        tlist = ['']+persistent_state_state.TableNames()
        return '<fieldset id="fschoose"><legend>Existing formats</legend>'\
        '<select name="tablechoose" id="tablechoose" onChange="TableChooseChanger()"><option>{}</option></select><br>'\
        '<input type="button" onClick="TableChoose()" class="dialogbutton" id="TCSelect" value="Select" disabled><br>'\
        '<input type="button" onClick="TableRename()" id="TCRename" class="dialogbutton" value="Rename" disabled><br>'\
        '<input type="button" onClick="TableDelete()" id="TCDelete" class="dialogbutton" value="Delete" disabled>'\
        '</fieldset>'.format('</option><option>'.join(tlist))        

    def _tablename( self ):
        global persistent_state_state
        tlist = persistent_state_state.TableNames()
        return '<fieldset id="fsnames"><legend>New format name</legend>'\
        '<input list="tablenames" name="tablename" id="tablename" onInput="NameChanger()"><datalist id="tablenames">{}</datalist><br>'\
        '<input type="button" onClick="TableName()" class="dialogbutton" id="tablenameok" value="Ok" disabled>'\
        '</fieldset>'.format(''.join(['<option value={}>'.format(t) for t in tlist]))        

    def _buttons( self, active_buttons, disabled_buttons ):
        blist=''
        for bl in [['Table','table',],['Search','search','next','back','research',],['Form','reset','clear',],['Record','copy','add','save','delete'],]:
            blist += '<fieldset><legend>{}</legend>'.format(bl[0])
            for b in bl[1:]:
                disabled = "disabled" if b in disabled_buttons else ""
                if b == 'delete':
                    blist += '<input id={} name="button" onClick="DeleteRecord()" type="button" value="{}" {}>'.format(b,type(self).buttondict[b],disabled)
                else:
                    blist += '<input id={} name="button" type="submit" value="{}" {}>'.format(b,type(self).buttondict[b],disabled)
            blist += '</fieldset>'
        return blist

    def FORMSCRIPT( self ):
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
        document.getElementById("mainform").submit();
        }
};</script>'''

    def TABLESCRIPTpre( self ):
        # Column widths (in table) need to be defined prior to creation
        return '''
<script>
function Able(n,v) {
    var x=document.getElementById(n);
    if (x !==null) {x.disabled=!v}
    };
function chooseFunction(id) {
    document.getElementById("_ID").value = id;
    document.getElementById("ID").submit();
    }
function fResize( indx ) {
    document.getElementById("table_type").value = "resize";
    document.getElementById("table_0").value = indx;
    document.getElementById("table_1").value = this.outerWidth;
    document.getElementById("table_back").submit();
    }
function fMove( from, to ) {
    document.getElementById("table_type").value = "move";
    document.getElementById("table_0").value = from;
    document.getElementById("table_1").value = to;
    document.getElementById("table_back").submit();
    }
function fSelect( indx ) {
    document.getElementById("table_type").value = "select";
    let values = [];
    document.querySelectorAll(`input[name="dfield"]:checked`).forEach((checkbox) => {
        values.push(checkbox.value);
    });
    document.getElementById("table_0").value = values;
    document.getElementById("table_back").submit();
    }
function fRestore( field ) {
    document.getElementById("table_type").value = "restore";
    document.getElementById("table_0").value = field;
    document.getElementById("table_back").submit();
    }
function fReset( ) {
    document.getElementById("table_type").value = "reset";
    document.getElementById("table_back").submit();
    }
function fCancel( ) {
    document.getElementById("table_type").value = "cancel";
    document.getElementById("table_back").submit();
    }
function TableChoose( ) {
    document.getElementById("table_type").value = "choose";
    document.getElementById("table_0").value = document.getElementById("tablechoose").value;
    document.getElementById("table_back").submit();
    }
function TableName( ) {
    document.getElementById("table_type").value = "name";
    document.getElementById("table_0").value = document.getElementById("tablename").value;
    document.getElementById("table_back").submit();
    }
function drop(event,to) {
    event.preventDefault();
    var from = event.dataTransfer.getData("Text");
    fMove( from, to.toString() ) ;
    }
function dragStart(event,n) {
    document.getElementById("status").innerHTML = "Moving a column position"
    event.dataTransfer.setData("text",n.toString())
    }
function dragEnd(event) {
    document.getElementById("status").innerHTML = ""
    }
function allowDrop(event) {
    event.preventDefault();
}
function FieldChanger() {
    Able("fschoose",false);
    Able("fsnames",false);
    Able("tablefieldok",true);
    }
function TableChooseChanger() {
    Able("fsnames",false);
    Able("fsfields",false);
    Able("TCSelect",true);
    Able("TCRename",true);
    Able("TCDelete",true);
    }
function NameChanger() {
    Able("fschoose",false);
    Able("fsfields",false);
    Able("tablenameok",true);
    }
function TableRename( ) {
    var d = document.getElementById("tablechoose").value;
    var x = prompt("Rename this table format?",d);
    if ( x != null ) {
        document.getElementById("table_type").value = "trename";
        document.getElementById("table_0").value = d;
        document.getElementById("table_1").value = x;
        document.getElementById("table_back").submit();
        }
    }
function TableDelete( ) {
    var d = document.getElementById("tablechoose").value;
    var x = confirm("Do you want to delete the '" + d +"' table format?");
    if ( x == true ) {
        document.getElementById("table_type").value = "tremove";
        document.getElementById("table_0").value = d;
        document.getElementById("table_back").submit();
        }
    }
function showDialog() {
    document.getElementById("tabledialog").style.display = "block";
    }
// Observe column widths
for (th of document.getElementsByClassName("thead")) {
    widths.push(0)
    ro.observe(th);
    }
</script>'''

    def TABLESCRIPTpost( self ):
        # Column monitoring can only happen after creation
        return '''
<script>
function fColumns() {
    document.getElementById("table_type").value = "widths";
    var wid = [];
    for (const w of widths) {
        wid.push(Math.max(parseInt(w),10).toString()+"px");
    }
    document.getElementById("table_0").value = wid.toString();
    document.getElementById("table_back").submit();
    }
var widths=[]
var ro = new ResizeObserver(entrylist => {
  for (let entry of entrylist) {
    const cr = entry.contentRect;
    widths[parseInt(entry.target.getAttribute("data-n"))]=cr.width+2*cr.left;
  }
});
// Observe column widths
for (th of document.getElementsByClassName("thead")) {
    widths.push(0)
    ro.observe(th);
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

    def FORMCSS( self ):
        # Begin the response
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/css; charset=utf-8')
        self.end_headers()
        self.wfile.write('''
body {
    font-size: 100%;
    background: #0000A9;
    }
.firststyle {
    background-color:#0000A9;
    font-family: "Lucida Console", Monaco, monospace;
    font-size: 1.5rem;
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
    font-size: 1.5rem;
    }
#head-grid {
    display: grid;
    grid-template-columns: auto auto auto auto;
    background-color: #CC00CC;
    color: #CC00CC;
    grid-gap: 6px;
}
.hcell {
    background-color:#0000A9;
    color: #00A9A9;
}    
.hcellbig {
    background-color:#0000A9;
    color: #00A9A9;
    grid-column-start: 2;
    grid-column-end: 5;
}    
#form-grid {
    display: grid;
    grid-template-columns: 13rem 80rem;
    background-color:#0000A9;
}
.lcell {
    background-color: #00A9A9;
    color:black;
    text-align: right;
}
#buttons {
    display: flex;
    width: 100%;
    background-color: #00A9A9;
    color:black;
    text-align: left;
    vertical-align: bottom;
}
input[type="button"], input[type="submit"]  {
    border-radius: 8px;
}
#reset { background-color:#EDA9FB }
#table { background-color: #CCCC00 }
#search { background-color: #8CD7EE }
#savesearch { background-color: #8CD7EE }
#getsearch { background-color: #8CD7EE }
#research { background-color: #66B3FF }
#next { background-color: #8CD7EE }
#back { background-color: #8CD7EE }
#save { background-color: #B1FABB }
#add { background-color: #B1FABB }
#copy { background-color: #00CC66 }
#delete { background-color: #E37791 }
#clear { background-color: #EDA9FB }
#id { background-color: #000000 }
#resize { background-color: #000000 }
'''.encode('utf-8') )
                
    def TABLECSS( self ):
        # Begin the response
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/css; charset=utf-8')
        self.end_headers()
        self.wfile.write('''
body {
    font-size: 100%;
    margin: 0px;
    }
.firststyle {
    background-color:#0000A9;
    font-family: "Lucida Console", Monaco, monospace;
    font-size: 1.5rem;
    letter-spacing: 2px;
    word-spacing: 2px;
    color: #A9A9A9;
    font-weight: normal;
    text-decoration: none;
    font-style: normal;
    font-variant: normal;
    text-transform: none;
    }
#tabledialog {
  display: none; /* Hidden by default */
  position: fixed; /* Stay in place */
  z-index: 1000; /* Sit on top */
  left: 8px;
  top: 8px;
  /*width: 100%; */ /* Full width */
  /*height: 100%; */ /* 0 -> Full height */
  overflow: auto; /* Enable scroll if needed */
  color: black;
  outline: 8px ridge threedface;
  background-color: rgb(0,255,255); /* Fallback color */
  background-color: rgba(0,255,255,0.9); /* Black w/ opacity */
}
.dialogbutton {
    padding: .5rem;
    font-size: 1rem;
    background-color: #CCCCFF;
    color: #0000A9;
    margin: 10px;
    float: right;
    border-radius: 8px;
}
.dialogbutton:disabled {
    background-color: lightgray;
    }
.tallflex {
    display: flex;
    flex-direction: column;
    }
.wideflex {
    display: flex;
    flex-direction: row;
    justify-content: space-evenly;
    }
#tstatus {
    background-color:#0000A9;
    color: white;
    z-index: 10;
    top: 0;
    position: sticky;
    }
#bhead {
    background-color: #00FFCC;
    border-color: white;
    border-style: groove;
    height: 100%
    position: sticky;
    }
.tlink {
    background-color: #00FFCC;
    border-color: white;
    border-style: groove;
    height: 100%
    position: sticky;
    }
.thead {
    background-color: #00A9A9;
    color:black;
    resize: horizontal;
    vertical-align: top;
    overflow: auto;
    z-index: 10;
    top: 1.3rem;
    position: -webkit-sticky;
    position: sticky;
    }
.shead {
    position: sticky;
}
.tcell0 {
    background-color:#0000A9;
}
.tcell1 {
    background-color:#0000D9;
}
.tcell0, .tcell1 {
    color:yellow;
    max-height: 5rem;
    position: relative;
    resize: horizontal;
    z-index: 0;
}
.tcell0:hover, .tcell1:hover {
    background-color: grey;
}
'''.encode('utf-8') )
        table = CookieManager.GetTable( self.cookie )
        self.wfile.write(
            '.ttable {{'\
                'display: inline-grid; '\
                'grid-template-columns: {};'\
                'top: 1.3rem; left:0;'\
                'grid-column-gap:2px;'\
                'background-color:#0000A9; '\
                '}}'.format(' '.join([f[1] for f in table])).encode('utf-8') )

    def ICON( self ):
        self.send_response(200)
        self.send_header('Content-Type',
                         'image/x-icon; charset=utf-8')
        self.end_headers()
        global icon_data
        self.wfile.write(icon_data)

    def CSVescaper( self, string ):
        return '"'+str(string).replace('\n',' ').replace('"','""').replace("'","''")+'"'

    def CSVrow( self, r ):
        return (','.join([self.CSVescaper(rr) if isinstance(rr,str) else str(rr) for rr in r])+'\n').encode('utf-8')

    def CSV( self ):
        self._get_cookie()
        table = CookieManager.GetTable(self.cookie)
        active_search = CookieManager.GetSearch(self.cookie)
        fields = [f[0] for f in table]

        # Begin the response
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/csv; charset=utf-8')
        self.end_headers()

        #header row
        self.wfile.write( self.CSVrow( [sqlfirst.PrintField(f) for f in fields] ) )

        #data rows
        for r in sqltable.SQL_record.SortedSearchDict( fields, active_search.last_dict ):
            self.wfile.write(self.CSVrow(r))

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

    #debug
    persistent.ArgSQL = 1
    sqlfirst.ArgSQL = 1

    filename = '../wines.fol'
    dbase_class = sqlfirst.OpenDatabase(filename)
    DbaseField.Generate(dbase_class)
    persistent_state_state = persistent.SQL_persistent( "default",filename)     

    try:
        server = HTTPServer((addr, port), GetHandler)
    except:
        print("Could not start server -- is another instance already using that port?")
        exit()
    print('Starting server address={} port={}, use <Ctrl-C> to stop'.format(addr,port))

    with open('favicon.ico','rb') as f:
        icon_data = f.read()


    server.serve_forever()
