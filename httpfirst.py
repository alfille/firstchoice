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

class GetHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        # Parse the form data posted
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # Begin the response
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write('<head><link href="/style.css" rel="stylesheet" type="text/css"></head>'.encode('utf-8'))
        self.wfile.write(('<body><div id="firststyle"><pre>').encode('utf-8'))
        self.wfile.write( ('Client: %s\n' % str(self.client_address)).encode('utf-8') )
        self.wfile.write( ('User-agent: %s\n' % str(self.headers['user-agent'])).encode('utf-8') )
        self.wfile.write( ('Path: %s\n' % self.path).encode('utf-8') )
        self.wfile.write( ('Form data:\n').encode('utf-8') )
        self.wfile.write(('</pre>').encode('utf-8'))

        # Echo back information about what was posted in the form
        print("POST",form)
        for field in form.keys():
            field_item = form[field]
            print(field,form[field].value)
            print('terd',form['terd'].value)
            if field_item.filename:
                # The field contains an uploaded file
                file_data = field_item.file.read()
                file_len = len(file_data)
                del file_data
                self.wfile.write( ('Uploaded %s as "%s" (%d bytes)<br>' % \
                        (field, field_item.filename, file_len)).encode('utf-8') )
            else:
                # Regular form value
                self.wfile.write( ('%s=%s<br>' % (field, form[field].value)).encode('utf-8') )
        self.wfile.write(('</body>').encode('utf-8'))
    
    def do_GET(self):
        parsed_path = parse.urlparse(self.path)
        print("PP:",type(parsed_path),parsed_path)
        if self.path == '/style.css':
            return self.CSS()
        elif self.path == '/favicon.ico':
            return self.ICON()
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
        message = '\r\n'.join(message_parts)
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write('<head><link href="/style.css" rel="stylesheet" type="text/css"></head>'.encode('utf-8'))
        self.wfile.write(('<body><div id="firststyle"><pre>'+message+'</pre>').encode('utf-8'))
        self.FORM([("First"," ","Primary data field"),("Sec"," ","Two data field"),("terd"," ","")])
        self.wfile.write(('post-test:\n\n</div></body>').encode('utf-8'))

    def CSS( self ):
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write('''
#firststyle, textarea {
    background-color:#0000A9;
    font-family: "Lucida Console", Monaco, monospace;
    font-size: 16px;
    letter-spacing: 2px;
    word-spacing: 2px;
    color: #A9A9A9;
    font-weight: normal;
    text-decoration: none;
    font-style: normal;
    font-variant: normal;
    text-transform: none;
    }
#labl {
    vertical-align:top;
    text-align:right;
    background-color: #0000A9;
    color: black;
    }
#texta {
    background-color: #00A9A9;
    }
table, th, td {
    border: 2px 
    border-color: #A95500;
    border-collapse: collapse;
    vertical-align:top;
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
        
    def FORM( self, ftupple_list ):
        # each tupple a (fname,ftype,fvalue) -- ftype currently ignored)
        if ftupple_list is not None:
            self.wfile.write( ('<form action="' + self.path + '" method="post"><table>').encode('utf-8') )
            for f in ftupple_list:
                print(f)
                self.FIELD( *f )
            self.wfile.write( ('</table width=100%><input name="submit" type="submit" value="Submit"><input name="cancel" type="submit" value="Cancel"></form>').encode('utf-8') )
        
    def FIELD( self, fname, ftype, fval ):
        # part of form
        if fname[0] == '_':
            self.wfile.write( ('<input type="hidden" name="' + fname + '" value="' + fval + '">').encode('utf-8') )
        else:
            #self.wfile.write( ( '<label><div id="labl">' + fname + ': </div><div id="texta"><textarea rows="2" cols="' + str(flen) + '" name="' + fname + '">' + fval + '</textarea></div></label><br>').encode('utf-8') ) 
            self.wfile.write( '<tr><td style="text-align:right">'.encode('utf-8') ) 
            self.wfile.write( ( '<label for="'+fname+'" style="color:black;background-color:#00A9A9">' + fname + ': </label>' ).encode('utf-8') ) 
            self.wfile.write( '</td><td>'.encode('utf-8') ) 
            self.wfile.write( ('<textarea rows=2 cols=90 name="' + fname + '" id=" + fname + ''">' + fval + '</textarea>' ).encode('utf-8') ) 
#            self.wfile.write( ('<textarea rows="2" cols=90 name="' + fname + '" id=" + fname + ''" style="firststyle">' + fval + '</textarea>' ).encode('utf-8') ) 
            self.wfile.write( '</td></tr>'.encode('utf-8') ) 
            


if __name__ == '__main__':
    
    addr = 'localhost'
    port = 8080
    
    try:
        server = HTTPServer((addr, port), GetHandler)
    except:
        print("Could not start server -- is another instance already using that port?")
        exit()
    print('Starting server address={} port={}, use <Ctrl-C> to stop'.format(addr,port))

    with open('favicon.ico','rb') as f:
        icon_data = f.read()

    server.serve_forever()
