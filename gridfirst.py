# http_server_GET.py

try:
    import http.server
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
    from http import cookies
except:
    print("Please install the http.cookies module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
try:
    import os.path
except:
    print("Please install the os module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
import sqlfirst
import persistent
import searchstate
import sqltable
import dbaselist
import cookiemanager

class GetHandler(http.server.BaseHTTPRequestHandler):
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

    support_files = {
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.ico': 'image/x-icon',
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
        ext = os.path.splitext(self.path)[1] # this extension
        if len(ext)>1:
            if ext == '.csv':
                return self.CSV()
            elif ext in type(self).support_files:
                return self.FILE( self.path[1:])

        self._get_cookie()

        self.PAGE({'button':'First'})


    def do_POST(self):

        self._get_cookie()

        # Parse the form data posted            
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

#        self.wfile.write(('<pre>{}</pre>'.format(self._post_message(form))).encode('utf-8'))

        # Write the form (with headers)
#        print(self._get_message())
        self.PAGE( { field:form[field].value for field in form.keys() } )
    
    def PAGE( self, formdict ):
        # Begin the response
        self._head()            
       
        # Send to record or table view

        # Note: initial entry is from "GET" -- with empty formdict        
        if 'button' not in formdict:
            # Empty dictionary
            formdict['button'] = "Edit"
        
        if formdict['button'] == "OK":
            # Do processing after rendering before pre-forma post is processed
            return self.SPLASH( formdict )

        elif formdict['button'] == 'First' or not cookiemanager.CookieManager.Valid( self.cookie ):
            self.wfile.write('<head>'\
                '<link href="/introstyle.css" rel="stylesheet" type="text/css">'\
                '</head>'.encode('utf-8'))
            self.wfile.write('<meta name="viewport" content="width=device-width, initial-scale=1">'.encode('utf-8'))
            self.wfile.write('<body>'.encode('utf-8') )
            self.INTRO()

        elif formdict['button'] == type(self).buttondict['table']:
            if "table_type" in formdict:
                ttype = formdict['table_type']
                t0 = formdict['table_0']
                t1 = formdict['table_1']
                table = cookiemanager.CookieManager.GetTable(self.cookie)
                if ttype == "reset":
                    cookiemanager.CookieManager.ResetTable( self.cookie )
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
                        cookiemanager.CookieManager.SetTableMod( self.cookie )
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
                    cookiemanager.CookieManager.SetTable( self.cookie, cookiemanager.CookieManager.Persistent(self.cookie).GetTable(t0) )
                    cookiemanager.CookieManager.SetTableName( self.cookie, t0 )
                elif ttype == "name":
                    cookiemanager.CookieManager.SetTableName( self.cookie, t0 )
                elif ttype == 'tremove':
                    if t0 != "default": # cannot delete default
                        p = cookiemanager.CookieManager.Persistent(self.cookie)
                        p.SetTable( t0, None ) # deletes
                        if t0 == cookiemanager.CookieManager.GetTableName( self.cookie ): # change existing to default
                            cookiemanager.CookieManager.SetTable( self.cookie, p.GetTable("default") )
                            cookiemanager.CookieManager.SetTableName( self.cookie, "default" )
                elif ttype == 'trename':
                    p = cookiemanager.CookieManager.Persistent(self.cookie)
                    if t0 != t1:
                        table = p.GetTable(t0)
                        p.SetTable( t1, table )
                        if t0 != "default": # cannot delete default
                            p.SetTable( t0, None ) # deletes
                        tcurrent = cookiemanager.CookieManager.GetTableName( self.cookie )
                        if t0 == tcurrent or t1 == tcurrent: # change current part of rename
                            cookiemanager.CookieManager.SetTable( self.cookie, table )
                            cookiemanager.CookieManager.SetTableName( self.cookie, t1 )
                elif ttype == 'widths':
                    wid = t0.split(',')
                    if len(wid) == len(table):
                        table = list(zip([t[0] for t in table],wid))
                        tname = cookiemanager.CookieManager.GetTableName( self.cookie )
                        cookiemanager.CookieManager.SetTable( self.cookie, table )
                        cookiemanager.CookieManager.SetTableName( self.cookie, tname ) # to clear mod
                            
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
                formdict = cookiemanager.CookieManager.GetLast(self.cookie)
                formdict['button'] = 'Edit' # No infinite loop
            self.wfile.write('<meta name="viewport" content="width=device-width, initial-scale=1">'.encode('utf-8'))
            self.wfile.write('<body>'.encode('utf-8'))
            self.FORM( formdict )

        self.wfile.write('</body>'.encode('utf-8'))

    def SPLASH( self, formdict ):
        # filename and user
        filename = formdict['FOL']
        user = formdict['user']
        
        self.wfile.write('<head>'\
            '<link href="/splashstyle.css" rel="stylesheet" type="text/css">'\
            '</head>'.encode('utf-8'))

        self.wfile.write(
            '<meta name="viewport" content="width=device-width, initial-scale=1">'\
            '<body>'.encode('utf-8') )

        # hidden form choose a line for FORM
        self.wfile.write(
            '<form action={} method="post" id="ID">'\
            '<input type="hidden" name="button" value="Edit">'\
            '</form>'.format(self.path).encode('utf-8') )

        self.wfile.write(
            '<div id="splash" class="firststyle"><h2>loading database {}...</h2></div>'\
            '<script src="splashscript.js"></script>'\
            '</body>'.format(filename).encode('utf-8') )

        # This does everything
        #  Links to persistent database
        #  Opens native database
        #  Parses database
        #  Sets field lists
        cookiemanager.CookieManager.SetUserDbase( self.cookie, user,filename )

    def FORM( self, formdict ):
        # After a "POST" --- clicking one of the submit buttons
        # formdict has the button and field values (if entered)
        # Preserved state is pstate, last_formdict and last_searchdict
        # place in search stored in pstate SearchState
        
        # button = button name from form, translate to local index name
        button = ''
        for b in type(self).buttondict:
            if formdict['button'] == type(self).buttondict[b]:
                button = b
                break;
        
        # default active buttons
        actbut = ['search','clear']
        # default inactive buttons
        deactbut = ['reset']

        active_search = cookiemanager.CookieManager.GetSearch(self.cookie)

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
            cookiemanager.CookieManager.SetSearch( self.cookie, active_search )
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
        cookiemanager.CookieManager.SetLast(self.cookie, formdict )

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

        self.wfile.write('<script src="formscript.js"></script>'.encode('utf-8') )
        self.wfile.write('<br><form action="{}" method="post" id="mainform">'.format(self.path).encode('utf-8') )
        if formdict['_ID'] is not None:
            self.wfile.write( '<input type="hidden" name="_ID" value="{}" >'.format(formdict['_ID']).encode('utf-8') )

        
        # Fields
        self.wfile.write('<div id="form-grid" class="firststyle">'.format(self.path).encode('utf-8') )
        for f in cookiemanager.CookieManager.GetDbaseObj( self.cookie ).flist:
            self._textfield( f,formdict[f.field] )
        self.wfile.write( ('</div>').encode('utf-8') )

        # Buttons
        self.wfile.write('<div id=buttons>{}</div>'.format(self._buttons(actbut,deactbut)).encode('utf-8') )
        self.wfile.write( ('</form>').encode('utf-8') )
        
    def INTRO( self ):
        # With no cookie or a move back from form
        self.wfile.write(
            '<div id="title"><h1>'\
            '<a href="http://github.com/alfille/firstchoice">First Choice to Web</a>'\
            '</h1><h3>&copy; 2021 Paul H Alfille</h3></div><br>'.encode('utf-8') ) 
        
        # button = button name from form, translate to local index name
        self.wfile.write(
        '<form id="intro" action="{}" method="post">'\
        '<fieldset class="firststyle"><legend>User</legend>'\
        '<label for="user">User name:</label><input id="user" name="user" list="users"><datalist id="users">{}</datalist>'\
        '</fieldset><br>'\
        '<fieldset class="firststyle"><legend>Database file</legend>'\
        '<label for="FOL">Select a first choice database</label><select name="FOL" id="FOL">{}</select>'\
        '</fieldset><br>'\
        '<input type="submit" name="button" value="OK"></form>'.format(self.path,self._userlist(),self._filelist()).encode('utf-8') )

    def _userlist( self ):
        #print(persistent.SQL_persistent.Userlist())
        return '<option value="default" select>'+''.join('<option value="{}">'.format(u) for u in persistent.SQL_persistent.Userlist() )
        
    def _filelist( self ):
        return ''.join(['<option value={}>{}</option>'.format(f,f) for f in dbaselist.dbaselist.filelist()])

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
        # script
        self.wfile.write('<script src="tablescript1.js"></script>'.encode('utf-8') )

        # Get field list
        table = cookiemanager.CookieManager.GetTable(self.cookie)

        # Computed style type because the number and size of columnms varies (rest in tablestyle.css file)
        self.wfile.write(
        '<style>'\
        '.ttable {{'\
            'display: inline-grid; '\
            'grid-template-columns: {};'\
            'top: 1.3rem; left:0;'\
            'grid-column-gap:2px;'\
            'background-color:#0000A9; '\
            '}}'\
        '</style>'.format(' '.join([f[1] for f in table])).encode('utf-8') )

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
        table_now = cookiemanager.CookieManager.GetTableName(self.cookie)
        if cookiemanager.CookieManager.GetTableMod(self.cookie):
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

        active_search = cookiemanager.CookieManager.GetSearch(self.cookie)
        if active_search is None or active_search.length==0:
            active_search = searchstate.SearchState({})
            cookiemanager.CookieManager.SetSearch( self.cookie, active_search )

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
        self.wfile.write('<script src="tablescript2.js"></script>'.encode('utf-8') )

    def _tablefields( self, table ):
        flist = [f[0] for f in table]
        checked = '<br>'.join(['<input type="checkbox" id="{}" name="dfield" value={}  onChange="FieldChanger()" checked><label for="{}">{}</label>'.format("c_"+f,f,"c_"+f,sqlfirst.PrintField(f)) for f in flist])
        unchecked = '<br>'.join(['<input type="checkbox" id="{}" name="dfield" value={} onChange="FieldChanger()"><label for="{}">{}</label>'.format("c_"+f.field,f.field,"c_"+f.field,sqlfirst.PrintField(f.field)) for f in cookiemanager.CookieManager.GetDbaseObj(self.cookie).flist if f.field not in flist])
        return '<fieldset id="fsfields"><legend>Choose fields shown</legend>{}'\
        '<button type="button" onClick="fSelect()" id="tablefieldok" class="dialogbutton" disabled>Ok</button>'\
        '</fieldset>'.format('<br>'.join([checked,unchecked]))
        #'<input type="button" onClick="fSelect()" id="tablefieldok" class="dialogbutton" value="Ok" disabled>'\

    def _tablechoose( self ):
        tlist = ['']+cookiemanager.CookieManager.Persistent(self.cookie).TableNames()
        return '<fieldset id="fschoose"><legend>Existing formats</legend>'\
        '<select name="tablechoose" id="tablechoose" onChange="TableChooseChanger()"><option>{}</option></select><br>'\
        '<input type="button" onClick="TableChoose()" class="dialogbutton" id="TCSelect" value="Select" disabled><br>'\
        '<input type="button" onClick="TableRename()" id="TCRename" class="dialogbutton" value="Rename" disabled><br>'\
        '<input type="button" onClick="TableDelete()" id="TCDelete" class="dialogbutton" value="Delete" disabled>'\
        '</fieldset>'.format('</option><option>'.join(tlist))        

    def _tablename( self ):
        tlist = cookiemanager.CookieManager.Persistent( self.cookie ).TableNames()
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

    def CSVescaper( self, string ):
        return '"'+str(string).replace('\n',' ').replace('"','""').replace("'","''")+'"'

    def CSVrow( self, r ):
        return (','.join([self.CSVescaper(rr) if isinstance(rr,str) else str(rr) for rr in r])+'\n').encode('utf-8')

    def FILE( self, filename ):
        ex = os.path.splitext(filename)[1]
        # Begin the response
        self.send_response(200)
        self.send_header('Content-Type',
                         '{}; charset=utf-8'.format(type(self).support_files[ex])
                         )
        self.end_headers()
        #data
        with open(os.path.join(ex[1:],filename),"rb") as f:
            self.wfile.write( f.read() )

    def CSV( self ):
        self._get_cookie()
        if cookiemanager.CookieManager.Valid( self.cookie ):
            table = cookiemanager.CookieManager.GetTable(self.cookie)
            active_search = cookiemanager.CookieManager.GetSearch(self.cookie)
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
                self.wfile.write(self.CSVrow(r[1:])) # First field is _ID -- skip

    def _get_cookie( self ):
        head_cook = self.headers.get('Cookie')
        #print(head_cook)
        if head_cook:
            self.cookie = cookies.SimpleCookie(head_cook)
            if "session" not in self.cookie:
                #print("Cookie=> ",'Bad cookie: no "session" entry')
                self.cookie = None
            else:
                pass
                #print("Cookie=> ","session = ", self.cookie["session"].value)
        else:
            #print("Cookie=> ","session cookie not set!")
            self.cookie = None
        #print("Cookie=> ","done")

    def _set_cookie( self ):
        self.cookie = cookiemanager.CookieManager.NewSession()

if __name__ == '__main__':
    
    addr = 'localhost'
    port = 8080

    #debug
    persistent.ArgSQL = 1
    sqlfirst.ArgSQL = 1

    try:
        server = http.server.HTTPServer((addr, port), GetHandler)
    except:
        print("Could not start server -- is another instance already using that port?")
        exit()
    print('Starting server address={} port={}, use <Ctrl-C> to stop'.format(addr,port))

    server.serve_forever()
