#!/usr/bin/python3

# First choice pack and unpack into sqlite

try:
    import sys
except:
    print("Please install the sys module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
try:
    import struct
except:
    print("Please install the struct module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
try:
    import signal
except:
    print("Please install the signal module")
    print("\tit should be part of the standard python3 distribution")
    raise
    
try:
    import argparse # for parsing the command line
except:
    print("Please install the argparse module")
    print("\tit should be part of the standard python3 distribution")
    raise

try:
    import sqlite3
except:
    print("Please install the sqlite3 module")
    print("\tit should be part of the standard python3 distribution")
    raise
    

BLOCKSIZE = 128


def hexdump( block ):
    if ( len(block) <= 128 ):
        hexdumpall(block)
        return
    hexdumpall( block[:128] )
    hexdump( block[128:] )

def hexdumpall(block):
    length = len(block)
    trail = 0
    while length > 0 and block[length-1] == 0x00:
        length -= 1
        trail += 1
    for byte in block[:length]:
        sys.stdout.write('%02x ' % byte )
    if trail > 0:
        sys.stdout.write('{:02x} * {}'.format(0x00,trail) )
        
    sys.stdout.write('\n')

class HtmlState:
    next_tag = None
        
    @classmethod
    def Set( cls, hs, state ):
        if state == 0:
            cls.Off(hs)
        else:
            cls.On(hs)
    
    @classmethod
    def On( cls, hs ):
        if not hs.state( cls ):
            # need to change state
            #    turn off lower temporarily
            if cls.next_tag is not None:
                cls.next_tag.Pause(hs)
            #    change state
            hs.append( "<"+cls.tag+">" )
            hs.On( cls )
            #    restore lower
            if cls.next_tag is not None:
                cls.next_tag.Resume(hs)
    
    @classmethod
    def Off( cls, hs ):
        if hs.state( cls ):
            # need to change state
            #    turn off lower temporarily
            if cls.next_tag is not None:
                cls.next_tag.Pause(hs)
            #    change state
            hs.append("</"+cls.tag+">")
            hs.Off( cls )
            #    restore lower
            if cls.next_tag is not None:
                cls.next_tag.Resume(hs)
        
    @classmethod
    def Pause( cls, hs ):
        # first pause lower
        if cls.next_tag is not None:
            cls.next_tag.Pause( hs )
        # now pause me
        if hs.state( cls ):
            hs.append("</"+cls.tag+">")
            
    @classmethod
    def Resume( cls, hs ):
        # restore my state
        if hs.state( cls ):
            hs.append( "<"+cls.tag+">" )
        # restore all lower states
        if cls.next_tag is not None:
            cls.next_tag.Resume( hs )
            
class Sub(HtmlState):
    tag = 'sub'
    next_tag = None

class Sup(HtmlState):
    tag = 'sup'
    next_tag = Sub

class Underline(HtmlState):
    tag = 'u'
    next_tag = Sup

class Italic(HtmlState):
    tag = 'i'
    next_tag = Underline

class Bold(HtmlState):
    tag = 'b'
    next_tag = Italic
    
class Close(HtmlState):
    # Wierd class to cleaup up states
    next_tag = Bold
    
    @classmethod
    def All( cls, hs ):
        if cls.next_tag is not None:
            # temporarily set states off
            cls.next_tag.Pause( hs )
            # make permenant
            hs.reset()

class HtmlString:
    def __init__( self ):
        self._string = bytearray(b'')
        self.reset()
        
    def reset( self ):
        # turn html states off
        self._state = {
            Bold:      False,
            Italic:    False,
            Underline: False,
            Sup:       False, 
            Sub:       False,
        }
        
    @property
    def string( self ):
        return self._string
        
    @string.setter
    def string( self, s ):
        self._string = s
    
    def state( self, cls ):
        return self._state[ cls ]
        
    def On( self, cls ):
        self._state[ cls ] = True
        
    def Off( self, cls ):
        self._state[ cls ] = False
        
    def append( self, s ):
        if isinstance(s,bytes):
            self._string+=s
        elif isinstance(s,str):
            self._string+=s.encode('utf-8')
        else:
            self._string.append(s)
        
class TextField:
    # Convert First-choice style text to plain text and HTML
    # First choice uses a unique encoding
    html_esc = {
        ord('<') : '&lt;',
        ord('>') : '&gt;',
        ord('&') : '&amp;',
        ord(' ') : '&nbsp;',
    }
    
    def __init__( self, string ):
        
        self.parsed = None
        
        _text = ''
        _ftext = ''
        _html = HtmlString()
        _fhtml = HtmlString()
        _fieldtype = ' '
        
        try:
            _length = struct.unpack_from('>H',string)[0]
            raw = string[2:]
        except:
            print("Bad string input")
            raw = None
            return
            
        #print('raw',len(raw),raw)
        #hexdump(raw)
        length_count = 0
        array_count = 0
        while length_count < _length:
            #print(_length,array_count,length_count)
            c = raw[array_count]
            array_count += 1
            length_count += 1
            if c < 0x80:
                Close.All(_html)
                Close.All(_fhtml)
                if c == 0x0d:
                    _text += "\n"                
                    _html.append('<br />')
                    length_count += 1
                elif c in type(self).html_esc :
                    _text += chr(c)
                    _html.append(type(self).html_esc[c])
                else:
                    _text += chr(c)
                    _html.append(c)
            else: # C >= 0x80
                c &= 0x7F # peel off first bit
                d = raw[array_count]
                # Background or field
                array_count += 1
                length_count += 1

                if d >= 0xd0 and d <= 0xdf:
                    # background text or field
                    # needs 3rd byte
                    e = raw[array_count]
                    array_count += 1
                    length_count += 1
                    
                    if e & 0x01 == 1:
                        # background
                        Bold.Set(_html, d & 0x02)
                        Italic.Set(_html, d & 0x04)
                        Underline.Set(_html, d & 0x01)
                        Sup.Set(_html,e==0x85)
                        Sub.Set(_html,e==0x83)

                        if c == 0 :
                            _text +=' '
                            _html.append('&nbsp')
                        elif c in type(self).html_esc :
                            _text += chr(c)
                            _html.append(type(self).html_esc[c])
                        else:
                            _text += chr(c)
                            _html.append(c)
                
                    else: # e is even
                        # field
                        Close.All(_html)
                        Bold.Set(_fhtml, d & 0x02)
                        Italic.Set(_fhtml, d & 0x04)
                        Underline.Set(_fhtml, d & 0x01)
                        Sup.Set(_html,e==0x84)
                        Sub.Set(_html,e==0x82)

                        if c == 0 :
                            _ftext +=' '
                            _html.append('&nbsp')
                        elif c in type(self).html_esc :
                            _ftext += chr(c)
                            _html.append(type(self).html_esc[c])
                        else:
                            _ftext += chr(c)
                            _html.append(c)
                
                elif d >= 0x90 and d <= 0x9f:
                    # Field Name
                    Close.All(_html)
                    Bold.Set(_fhtml, d & 0x02)
                    Italic.Set(_fhtml, d & 0x04)
                    Underline.Set(_fhtml, d & 0x01)
                    
                    if c == 0 :
                        _ftext += ' '
                        _fhtml.append('&nbsp')
                    elif c == 1:
                        _fieldtype = ' '
                        Close.All(_fhtml)
                    elif c == 2:
                        _fieldtype = 'N'
                        Close.All(_fhtml)
                    elif c == 3:
                        _fieldtype = 'D'
                        Close.All(_fhtml)
                    elif c == 4:
                        _fieldtype = 'T'
                        Close.All(_fhtml)
                    elif c == 5:
                        _fieldtype = 'Y'
                        Close.All(_fhtml)
                    elif c in type(self).html_esc :
                        _ftext += chr(c)
                        _fhtml.append(type(self).html_esc[c])
                    else:
                        _ftext += chr(c)
                        _fhtml.append(c)
        
                elif d >= 0x81 and d <= 0x8f:
                    # Regular text
                    Bold.Set(_html, d & 0x02)
                    Italic.Set(_html, d & 0x04)
                    Underline.Set(_html, d & 0x01)
                    
                    if c == 0 :
                        _text += ' '
                        _html.append('&nbsp')
                    elif c in type(self).html_esc :
                        _text += chr(c)
                        _html.append(type(self).html_esc[c])
                    else:
                        _text += chr(c)
                        _html.append(c)
        
                elif d >= 0xc0 and d <= 0xcf:
                    # regular text
                    # needs 3rd byte
                    e = raw[array_count]
                    array_count += 1
                    length_count += 1
                    
                    Bold.Set(_html, d & 0x02)
                    Italic.Set(_html, d & 0x04)
                    Underline.Set(_html, d & 0x01)
                    Sup.Set(_html,e==0x84)
                    Sub.Set(_html,e==0x82)


                    if c == 0 :
                        _text +=' '
                        _html.append('&nbsp')
                    elif c in type(self).html_esc :
                        _text += chr(c)
                        _html.append(type(self).html_esc[c])
                    else:
                        _text += chr(c)
                        _html.append(c)
                                
        self.parsed = {
            'text' : _text,
            'html' : _html.string,
            'ftext': _ftext,
            'fhtml': _fhtml.string,
            'fieldtype': _fieldtype,
            'length': _length,
            'rest': raw[array_count:]
            }
            
            
    @property
    def text(self):
        if self.parsed is None:
            return None
        return self.parsed['text']
            
    @property
    def ftext(self):
        if self.parsed is None:
            return None
        return self.parsed['ftext']
            
    @property
    def html(self):
        if self.parsed is None:
            return None
        return self.parsed['html']
            
    @property
    def fhtml(self):
        if self.parsed is None:
            return None
        return self.parsed['fhtml']
            
    @property
    def fieldtype(self):
        if self.parsed is None:
            return None
        return self.parsed['fieldtype']
            
    @property
    def length(self):
        if self.parsed is None:
            return None
        return self.parsed['length']
                
    @property
    def rest(self):
        if self.parsed is None:
            return None
        return self.parsed['rest']
                
class FOLfile_in:
    # database header
    header_format = '<4H14s9HB'
    nonheader_format = "<H126s"
    gerb = b'\x0cGERBILDB3   \x00'
    
    def __init__(self,dbase):
        self.dbase = dbase
        self.filename = sys.argv[-2]
        self.blocknum = 0
        self.data = [] # List or record data tupples
        self.blocks = [[0,""]]

        self.fulldef={
        'form':None,
        'view':None,
        'program':None,
        }
        
        headdata = b""
        for n in range(4):
            if not self._read():
                print("Cannot read full 4 block header")
                return
            headdata += self.block
        self.ReadHeader(headdata)
            
        halfheader = b""
        for n in range(4):
            if not self._read():
                print("Cannot read full second 4 block header")
                return
            halfheader += self.block
        self.ReadEmpties(halfheader)
        
        allocatedblocks = 7
        usedblocks = 7
        while self._read():
            allocatedblocks += 1
            if self.Block2Memory() != 0x00:
                usedblocks = allocatedblocks
                
        if allocatedblocks != self.header['allocatedblocks']:
            print("Allocated blocks count is off")
        if usedblocks != self.header['usedblocks']:
            print("Used blocks count is off")
        
        for [t,d] in self.blocks:
            self.ParseRecord( t,d )
        
        del(self.blocks)
        self.dbase.close()
            
    def apply_struct( self, structure, string ):
        slen = struct.calcsize( structure )
        return struct.unpack( structure, string[:slen] ) + (string[slen:], )
        
    def all_zeros( self, string ):
        for b in string:
            if b != 00:
                return False
        return True
        
    def _read(self):
        self.block = self.dbase.read(BLOCKSIZE)
        self.byte0 = None
        self.byte1 = None
        if len(self.block) == 0:
            return False
        self.blocknum += 1
        return True
    
    def ReadHeader( self, headdata ):
        #hexdump(self.header)
        data = self.apply_struct( type(self).header_format, headdata )
        #print(data)
        self.header = {
            'formdef'        : data[ 0],
            'usedblocks'     : data[ 1],
            'allocatedblocks': data[ 2],
            'records'        : data[ 3],
            'gerb'           : data[ 4],
            'fields'         : data[ 5],
            'formlength'     : data[ 6],
            'formrevisions'  : data[ 7],
            'unknown1'       : data[ 8],
            'emptieslist'    : data[ 9],
            'view'           : data[10],
            'program'        : data[11],
            'proglines'      : data[12],
            'diskvartype'    : data[13],
            'diskvarlen'     : data[14],
            'diskvar'        : data[15][:data[14]],
            }
        #print( self.header )
        self.header['fulldef'] = headdata
        if self.header['usedblocks'] != self.header['allocatedblocks']:
            print("Blocks don't match")
        if type(self).gerb != data[4]:
            print("GERB doesn't match")

    def ReadEmpties( self, halfheader ):
        print("Empties")
        #hexdump(halfheader)
        d = halfheader
        while True:
            try:
                a,b,d = self.apply_struct( "<HH", d )
            except:
                break
            if a==0 and b == 0:
                break
            #print('[{},{}]'.format(a,b),end="  ")
        #print('\n')

    def ReadData( self, d ):
        datalist = []
        for i in range( self.header['fields'] ):
            t = TextField(d)
            d = t.rest
            datalist.append(t.text)
        self.data.append(tuple(datalist))
            
        #print(self.data[-1])
    
    def ReadView( self, d ):
        self.view = []
        for i in range( self.header['fields'] ):
            t = TextField(d)
            d = t.rest
            self.view.append(t.text)
            #print("len=",le,"=>",li)
        #print("Total length = ", tot_length, "0x0d = ",self.ods)
    
    def ReadProgram( self, d ):
        for i in range( 1 ):
            t = TextField(d)
            d = t.rest
            #print(t.text)
            #print(t.html)
    
    def ReadForm( self,d ):
        self.form={}
        self.form['length'], self.form['lines'], d = self.apply_struct( '>2H', d )
        
        #print("Formlength=",self.form['length'],"formlines=",self.form['lines'])
        tot_length = 0
        self.form['fields'] = []
        for i in range( self.header['fields'] ):
            t = TextField(d)
            d = t.rest
            tot_length += t.length
            self.form['fields'].append({'text':t.text,'field':t.ftext,'type':t.fieldtype})
        #if tot_length != self.header['fields'] + self.header['formlength'] - 1:
        #    print("Formlength in header doesn't match computed");
        if self.form['length'] != tot_length + self.form['lines'] + 1:
            print("Form.length in record doesn't match computed");

    def Block2Memory( self ):
        # Note:
        #  will ignore block + continuation field (and not include)
        blocktype, blockdata = ( struct.unpack( type(self).nonheader_format, self.block ) )
        if blocktype == 0x82:
            print("Block number ",self.blocknum,"\t","Form definition")
            self.blocks.append( [blocktype, blockdata[2:]] )
        elif blocktype == 0x02:
            if self.blocks[-1][0] != 0x82:
                print("Bad Continuation")
            print("Block number ",self.blocknum,"\t","Form definition continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x81:
            print("Block number ",self.blocknum,"\t","Data record")
            self.blocks.append( [blocktype, blockdata[2:]] )
        elif blocktype == 0x01:
            if self.blocks[-1][0] != 0x81:
                print("Bad Continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x84:
            print("Block number ",self.blocknum,"\t","Program")
            self.blocks.append( [blocktype, blockdata[2:]] )
        elif blocktype == 0x04:
            if self.blocks[-1][0] != 0x84:
                print("Bad Continuation")
            print("Block number ",self.blocknum,"\t","Program continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x83:
            print("Block number ",self.blocknum,"\t","Table View")
            self.blocks.append( [blocktype, blockdata[2:]] )
        elif blocktype == 0x03:
            if self.blocks[-1][0] != 0x83:
                print("Bad Continuation")
            print("Block number ",self.blocknum,"\t","Table View continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x00:
            print("Block number ",self.blocknum,"\t","Empty record")
            self.blocks.append( [blocktype, blockdata] )
        else:
            print("Block number ",self.blocknum,"\t","Unknown type {:02x}".format(blocktype))
            self.blocks.append( [blocktype, blockdata] )
        return blocktype

    def ParseRecord( self, t, d ):
        if t == 0x82:
            print("Form definition")
            #hexdump(d)
            self.fulldef['form'] = d
            self.ReadForm(d)
        elif t == 0x81:
            print("Data")
            #hexdump(d)
            self.ReadData(d)
        elif t == 0x84:
            print("Program")
            #hexdump(d)
            self.fulldef['program'] = d
            self.ReadProgram(d)
        elif t == 0x83:
            print("Table View")
            #hexdump(d)
            self.fulldef['view'] = d
            self.ReadView(d)
        elif t == 0x00:
            if not self.all_zeros(d):
                print("Unexpected entries")
                hexdump(d)
        else:
            print("Unknown = {:02X}".format(t))
            hexdump(d)
            
class FOLfile_in_sql(FOLfile_in):
    def __init__(self,dbase):
        self.conn = sqlite3.connect('sql.db')
        super().__init__(dbase)
        self.curse = self.conn.cursor()
        
        # Delete old table
        self.curse.execute('DROP TABLE IF EXISTS first')
        
        # Create new table
        print('CREATE TABLE first (' + ','.join([f['field']+' text' for f in self.form['fields']]) + ')') 
        self.curse.execute('CREATE TABLE first (' + ','.join(['\"'+f['field']+'\" text' for f in self.form['fields']]) + ')') 
        
        # Add all data
        self.curse.executemany('INSERT INTO first VALUES ('+ ','.join(list('?'*self.header['fields'])) + ')',self.data)
        self.conn.commit()

    def __del__(self):
        self.conn.close()

class RecordOut:
    def __init__( self, database, fol_fileout ):
        self.database = database
        self.fol_fileout = fol_fileout
        
    def Split_Label_2_Blocks( self, data ):
        # Add block types, continuations, and return
        # blocks, data
        # zero filled to 128 size
        
        length = len( data )
        bt = bytearray(b'XX')
        
        # First block
        blocks = 1
        
        struct.pack_into( "<H", bt, 0, type(self).blocktype )
        working = bt + b'XX'+data[:124] # blocktype, space for block count, and some data
        length -= 124
        data = data[124:]

        # Add additional blocks
        while length > 0:
            blocks += 1
            struct.pack_into( "<H", bt, 0, ( type(self).blocktype & 0x7F ) )
            working += bt + data[:126] # Continuation block type and data
            data = data[126:]
            length -= 126

        # Zero-pad last block
        zpad = (128 - (len(working) % 128)) % 128
        working += b'\x00' * zpad
        
        # Add total block count to first block
        struct.pack_into( "<H", working, 2, blocks )
        
        self.UpdateSizes( blocks )
        self.Write( working )
        
    def UpdateSizes( self, blocks ):
        self.database.header['usedblocks'] += blocks
        self.database.header['allocatedblocks'] += blocks
        
    def Write( self, data ):
        self.fol_fileout.write( data )

class FormRecordOut(RecordOut):
    blocktype = 0x82
    
    def Create( self ):
        self.Split_Label_2_Blocks( self.database.fulldef['form'] )

class ViewRecordOut(RecordOut):
    blocktype = 0x83

    def Create( self ):
        self.Split_Label_2_Blocks( self.database.fulldef['view'] )

class ProgramRecordOut(RecordOut):
    blocktype = 0x84

    def Create( self ):
        self.Split_Label_2_Blocks( self.database.fulldef['program'] )

class EmptyRecordOut(RecordOut):

    def Create( self ):
        self.UpdateSizes( 1 )
        working = b'\x00'*128
        self.Write(working)

class HeaderRecordOut(RecordOut):

    def Create( self ):
        self.database.header['usedblocks'] = 3
        self.database.header['allocatedblocks'] = 3
        working = self.database.header['fulldef']
        self.Write(working)

class DataRecordOut(RecordOut):
    blocktype = 0x81

    def Create( self, field_values ):
        # return blocks and record bytearray
        # field_values is a tuple
        ba = bytearray(b'')
        for f in field_values:
            ba += self.SingleField(f)
        self.Split_Label_2_Blocks( ba )
        
    def SingleField( self, string ):
        # returns bytearray
        ba = bytearray(b'XX')+string.encode('utf-8').replace(b'\n',b'\r')
        cr = ba.count(b'\r')
        struct.pack_into('>H',ba,0,len(string)+cr)
        return ba

class FOLfile_out:
    
    def __init__(self, database, fol_fileout ):
        self.database = database
        self.fol_fileout = fol_fileout
        
        self.Write()
        self.fol_fileout.close()
        
    def Write( self ):

        # Old header (will be updated)
        HeaderRecordOut( self.database, self.fol_fileout ).Create()

        # Empties list
        self.database.header['emptieslist'] = 0
        EmptyRecordOut( self.database, self.fol_fileout ).Create()
        EmptyRecordOut( self.database, self.fol_fileout ).Create()
        EmptyRecordOut( self.database, self.fol_fileout ).Create()
        EmptyRecordOut( self.database, self.fol_fileout ).Create()

        # Form Definition
        self.database.header['formdef'] = self.database.header['allocatedblocks']+1
        FormRecordOut( self.database, self.fol_fileout ).Create()

        # Table View
        if self.database.fulldef['view'] is not None:
            self.database.header['view'] = self.database.header['allocatedblocks']+1
            ViewRecordOut( self.database, self.fol_fileout ).Create()

        # Program
        if self.database.fulldef['program'] is not None:
            self.database.header['program'] = self.database.header['allocatedblocks']+1
            ProgramRecordOut( self.database, self.fol_fileout ).Create()
            
        # All data records
        self.database.header['records'] = 0
        for f in self.database.data:
            DataRecordOut( self.database, self.fol_fileout).Create( f )
            self.database.header[ 'records' ] += 1

        # Update header
        self.fol_fileout.seek(0)
        self.fol_fileout.write( struct.pack(
            '<4H14s9HB',
            self.database.header['formdef'],self.database.header['usedblocks'],self.database.header['allocatedblocks'],
            self.database.header['records'],self.database.header['gerb'],self.database.header['fields'],
            self.database.header['formlength'],self.database.header['formrevisions'],self.database.header['unknown1'],
            self.database.header['emptieslist'],self.database.header['view'],self.database.header['program'],
            self.database.header['proglines'],self.database.header['diskvartype'],self.database.header['diskvarlen']
            )
        )
    
class FOLfile_out_sql(FOLfile_out):
    
    def __init__(self, database, fol_fileout ):
        self.database = database
        self.fol_fileout = fol_fileout
        
        print(list(self.database.curse.execute('SELECT * FROM first')))
        
        self.Write()
        self.fol_fileout.close()
        


def signal_handler( signal, frame ):
    # Signal handler
    # signal.signal( signal.SIGINT, signal.SIG_IGN )
    sys.exit(0)

def CommandLine():
    """Setup argparser object to process the command line"""
    cl = argparse.ArgumentParser(description="Use a PFS:First Choice v3 database file (.FOL) for data access and writing. 2020 by Paul H Alfille")
    cl.add_argument("In",help="Existing database file (type .FOL)",type=argparse.FileType('rb'))
    cl.add_argument("Out",help="New database file",type=argparse.FileType('wb'),nargs='?',default="OUTPUT.FOL")
#    cl.add_argument("O",help="Depth of large Box (default Cube)",type=int,nargs='?',default=None)
#    cl.add_argument("-m","--maximum",help="Maximum size of tiling square allowed",type=int,nargs='?',default=None)
#    cl.add_argument("-s","--show",help="Show the solutions graphically",action="store_true")
#    cl.add_argument("-3","--cube",help="3-D solution -- cubes in box",action="store_true")
#    cl.add_argument("-q","--quiet",help="Suppress more and more displayed info (can be repeated)",action="count")
    return cl.parse_args()
        
if __name__ == '__main__':
    """
    First Choice FOLfile_in File
    *.fol
    """
    args = CommandLine() # Get args from command line

    # Set up keyboard interrupt handler
    signal.signal(signal.SIGINT, signal_handler )
    # Start program
    dbase = FOLfile_in_sql( args.In )
    FOLfile_out_sql( dbase, args.Out )
    sys.exit(None)
