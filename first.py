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
    
if __name__ == "__main__":
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
    
try:
    import textwrap
except:
    print("Please install the textwrap module")
    print("\tit should be part of the standard python3 distribution")
    raise
    

BLOCKSIZE = 128
Verbose = 0

class ScreenLoc:
    def __init__(self):
        self._x, self._y = 1,1
        self._fx,self._fy = 1,1
        self._flength = 0
    
    def _string( self, text ):
        if text is None:
            text = ''
        sp = text.split('\n')
        if len(sp) > 1:
            # more than one line
            self._y += len(sp)-1
            self._x = 1
        self._x += len(sp[-1])
    
    def field( self, text, ftext, text2 ):
        self._string(text)
        self._string(ftext+':')
        self._fx,self._fy = self._x,self._y
        self._string(text2)
        self._flength = self._x - self._fx + 78 * ( self._y - self._fy )
        
    @property
    def location( self ):
        return self._x,self._y
        
    @property
    def flocation( self  ):
        return self._fx,self._fy
        
    @property
    def flength( self ):
        return self._flength
        
class DataField(textwrap.TextWrapper):
    prior = None
    # one per field
    def __init__( self, field_dict):
        # convert text into FOL format data field
        
        length = field_dict['length']
        startx, starty = field_dict['location']
        
        # compute line lengths of template
        first = 79 - startx
        if first > length:
            first = length
            self.template = [first]
            self.midtemplate = [first]
        else:
            last = (length - first) % 78
            self.midtemplate = [first] + [78 for x in range( (length-first) // 78)] + [last] 
            self.template = [first] + [78 for x in range( (length-first) // 78)] + [last for x in [1] if last > 0] 
            
        # Easy way to tell last object created
        prior = type(self).prior
        if prior is not None:
            prior._final = False
            prior.template = prior.midtemplate
        type(self).prior = self
        self._final = True
        
        super().__init__(width=78, replace_whitespace=True, drop_whitespace=True, initial_indent=' '*(startx-1) )
        
    def PadLines( self, stringlist ):
        t = len(self.template)
        s = len(stringlist)
        if t < s:
            del stringlist[t:]
        else:
            stringlist += ['']*(t-s)
            
    def LastLine( self, stringlist ):
        if len(stringlist[-1]) > self.template[-1]:
            stringlist[-1] = stringlist[-1][:self.template[-1]]
            
    def SpaceOut( self, stringlist ):
        # last field only
        l = len(stringlist[-1])
        if l > 0 :
            stringlist[-1] += ' '*(self.template[-1]-l)
            
    def FitOld( self, stringlist ):
        if max([len(s) for s in stringlist]) > 78:
            return False
        if not self._final and len(stringlist) > len(self.template):
            return False
        for l,t in zip(stringlist,self.template):
            if len(l) > t:
                return False
        return True
        
    def Parse( self, inputstring ):
        # clean up input
        print("Parse ",bytes(inputstring,'utf-8'))
        
        #strip ends
        ss = inputstring.strip()
        
        #strip trailing space on each line
        while ss.count(' \n')>0:
            ss=ss.replace(' \n','\n')
            
        # add initial space
        ss = ' '+ss

        # split lines
        sl = (ss).split('\n')
        
        if not self.FitOld(sl):
            print("Wrap!")
            sl = self.wrap(ss)
            # get rid of fake indent that takes place of field name
            sl[0] = ' '+sl[0].lstrip()

        if not self._final:
            self.PadLines( sl )
            self.LastLine( sl )
        else:
            sl += ['\n','\n']
        self.SpaceOut( sl )
        return '\n'.join(sl)
                    
def Print1( *args, **kwargs):
    global Verbose
    if Verbose >= 1:
        print( *args, **kwargs)

def Print2( *args, **kwargs):
    global Verbose
    if Verbose >= 2:
        print( *args, **kwargs)

def Print3( *args, **kwargs):
    global Verbose
    if Verbose >= 3:
        print( *args, **kwargs)


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
    field_types = {
        1:' ', # general
        2:'N', # numeric
        3:'D', # date
        4:'T', # time
        5:'Y', # boolian
    }

    def __init__( self, string ):
        
        self.parsed = None
        
        _text = ['']
        _ftext = ['']
        _text2 = ['']
        _html = HtmlString()
        _html2 = HtmlString()
        _fhtml = HtmlString()
        _fieldtype = ' '
        
        postftext = False
        
        try:
            _length = struct.unpack_from('>H',string)[0]
            raw = string[2:]
        except:
            Print1("Bad string input")
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
                    if postftext:
                        _text2[0] += "\n"                
                        _html2.append('<br />')
                    else:
                        _text[0] += "\n"                
                        _html.append('<br />')
                    length_count += 1
                else:
                    if postftext:
                        self.AddChar( c, _text2, _html2 )
                    else:
                        self.AddChar( c, _text, _html )
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
                        if postftext:
                            self.BoIlUn( d, _html2 )
                            self.SupSub( e, _html2 )
                            self.AddChar( c, _text2, _html2 )
                        else:
                            self.BoIlUn( d, _html )
                            self.SupSub( e, _html )
                            self.AddChar( c, _text, _html )
                
                    else: # e is even
                        # field
                        Close.All(_html)
                        self.BoIlUn( d, _fhtml )
                        self.SupSub( e, _fhtml )

                        self.AddChar( c, _ftext, _fhtml )
                
                        postftext = True

                elif d >= 0x90 and d <= 0x9f:
                    # Field Name
                    Close.All(_html)
                    self.BoIlUn( d, _fhtml )
                    
                    if c in type(self).field_types:
                        _fieldtype = type(self).field_types[c]
                        Close.All(_fhtml)
                    else:
                        self.AddChar( c, _ftext, _fhtml )
        
                        postftext = True

                elif d >= 0x81 and d <= 0x8f:
                    # Regular text
                    if postftext:
                        self.BoIlUn( d, _html2 )
                        self.AddChar( c, _text2, _html2 )
                    else:
                        self.BoIlUn( d, _html )
                        self.AddChar( c, _text, _html )
        
                elif d >= 0xc0 and d <= 0xcf:
                    # regular text
                    # needs 3rd byte
                    e = raw[array_count]
                    array_count += 1
                    length_count += 1
                    
                    if postftext:
                        self.BoIlUn( d, _html2 )
                        self.SupSub( e, _html2 )
                        self.AddChar( c, _text2, _html2 )
                    else:
                        self.BoIlUn( d, _html )
                        self.SupSub( e, _html )
                        self.AddChar( c, _text, _html )
                                
        print("Data",len(_text[0]),_length,bytes(_text[0],'utf-8'))
        self.parsed = {
            'text' : _text[0],
            'html' : _html.string,
            'text2': _text2[0],
            'html2' : _html2.string,
            'ftext': _ftext[0],
            'fhtml': _fhtml.string,
            'fieldtype': _fieldtype,
            'length': _length,
            'rest': raw[array_count:]
            }

            
    def AddChar( self, c, text, html ):
        if c == 0 :
            text[0] +=' '
            html.append('&nbsp')
        elif c in type(self).html_esc :
            text[0] += chr(c)
            html.append(type(self).html_esc[c])
        else:
            text[0] += chr(c)
            html.append(c)

    def BoIlUn( self, d, xhtml ):
        Bold.Set( xhtml, d & 0x02 )
        Italic.Set( xhtml, d & 0x04 )
        Underline.Set( xhtml, d & 0x01 )

    def SupSub( self, e, xhtml ):
        Sup.Set( xhtml,( e & 0xFE ) == 0x84 )
        Sub.Set( xhtml,( e & 0xFE ) == 0x82 )

    @property
    def text(self):
        if self.parsed is None:
            return None
        return self.parsed['text']
            
    @property
    def text2(self):
        if self.parsed is None:
            return None
        return self.parsed['text2']
            
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
    def html2(self):
        if self.parsed is None:
            return None
        return self.parsed['html2']
            
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
                
class FOL_handler:
    # FOLdatabase header
    header_format = '<4H14s9HB'
    nonheader_format = "<H126s"
    gerb = b'\x0cGERBILDB3   \x00'
    
    def __init__( self, FOLfile, FOLout='OUTPUT.FOL' ):
        # FOLfile is either handle (main from command line) or filename (in a module)
        # FOLout is name of output FOL file
        # module true if called as mondule rather than standalone
        
        if type(FOLfile)==str:
            # given filename, need to open
            self.filename = FOLfile
            self.FOLfile = open( FOLfile, "rb" )
        else: # command line
            #given open file, need filename
            self.FOLfile = FOLfile
            self.filename = sys.argv[-2]
                
        self.blocknum = 0
        self.data = [] # List of record data tupples
        self.blocks = [[0,""]] # FOL file read in with continuations merged

        # literal blocks that don't change because we don's support it
        self.fulldef={
        'form':None,
        'view':None,
        'program':None,
        }
        
        headdata = b""
        for n in range(4):
            if not self._read():
                Print1("Cannot read full 4 block header")
                return
            headdata += self.block
        self.ReadHeader(headdata)
            
        halfheader = b""
        for n in range(4):
            if not self._read():
                Print1("Cannot read full second 4 block header")
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
            Print1("Allocated blocks count is off")
        if usedblocks != self.header['usedblocks']:
            Print1("Used blocks count is off")
        
        for [t,d] in self.blocks:
            self.ParseRecord( t,d )

        del(self.blocks)
        self.FOLfile.close()            

        if type(FOLout)==str:
            # given filename, need to open
            self.fileoutname = FOLout
            self.FOLout = open( FOLout, 'wb' )
        else: # command line
            #given open file, need filename
            self.FOLout = FOLout
        
        
    def apply_struct( self, structure, string ):
        slen = struct.calcsize( structure )
        return struct.unpack( structure, string[:slen] ) + (string[slen:], )
        
    def all_zeros( self, string ):
        for b in string:
            if b != 00:
                return False
        return True
        
    def _read(self):
        self.block = self.FOLfile.read(BLOCKSIZE)
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
        Print3( self.header )
        self.header['fulldef'] = headdata
        if self.header['usedblocks'] != self.header['allocatedblocks']:
            Print2("Blocks don't match")
        if type(self).gerb != data[4]:
            Print1("GERB doesn't match")

    def ReadEmpties( self, halfheader ):
        Print3("Empties")
        #hexdump(halfheader)
        d = halfheader
        while True:
            try:
                a,b,d = self.apply_struct( "<HH", d )
            except:
                break
            if a==0 and b == 0:
                break
            Print3('[{},{}]'.format(a,b),end="  ")
        Print3('\n')

    def ReadData( self, d ):
        datalist = []
        for i in range( self.header['fields'] ):
            t = TextField(d)
            d = t.rest
            
            # strip white spaace and extra line-end padding
            print(len(t.text),"<",bytes(t.text,'utf-8'),">")
            s = t.text.strip()
            while s.count(' \n') > 0:
                s = s.replace(' \n','\n')
            datalist.append(s)
            
        self.data.append(tuple(datalist))
            
        Print3(self.data[-1])
    
    def ReadView( self, d ):
        self.view = []
        for i in range( self.header['fields'] ):
            t = TextField(d)
            d = t.rest
            self.view.append(t.text)
            
    def ReadProgram( self, d ):
        for i in range( 1 ):
            t = TextField(d)
            d = t.rest
            Print3(t.text)
            Print3(t.html)
    
    def ReadForm( self,d ):
        self.form={}
        self.form['length'], self.form['lines'], d = self.apply_struct( '>2H', d )
        
        Print3("Formlength=",self.form['length'],"formlines=",self.form['lines'])
        tot_length = 0
        self.form['fields'] = []
        self.form['textwrap'] = []
        sl = ScreenLoc()
        for i in range( self.header['fields'] ):
            t = TextField(d)
            d = t.rest
            tot_length += t.length
            ftext = t.ftext
            if ftext == '':
                ftext = 'Scribbles'
            sl.field( t.text,t.ftext,t.text2)
            self.form['fields'].append(
                {
                'text':t.text,
                'field':ftext,
                'type':t.fieldtype,
                'location':sl.flocation,
                'length':sl.flength,
                }
                )
            self.form['textwrap'].append( DataField(self.form['fields'][-1]) )
            print(t.ftext,sl.flocation," length=",sl.flength,self.form['textwrap'][-1].template)
        if tot_length != self.header['fields'] + self.header['formlength'] - 1:
            Print2("Formlength in header doesn't match computed");
        if self.form['length'] != tot_length + self.form['lines'] + 1:
            Print3("Form.length in record doesn't match computed");

    def Block2Memory( self ):
        # Note:
        #  will ignore block + continuation field (and not include)
        blocktype, blockdata = ( struct.unpack( type(self).nonheader_format, self.block ) )
        if blocktype == 0x82:
            Print2("Block number ",self.blocknum,"\t","Form definition")
            self.blocks.append( [blocktype, blockdata[2:]] )
        elif blocktype == 0x02:
            if self.blocks[-1][0] != 0x82:
                Print1("Bad Continuation form")
            Print2("Block number ",self.blocknum,"\t","Form definition continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x81:
            Print2("Block number ",self.blocknum,"\t","Data record")
            self.blocks.append( [blocktype, blockdata[2:]] )
        elif blocktype == 0x01:
            if self.blocks[-1][0] != 0x81:
                Print1("Bad Continuation Data")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x84:
            Print2("Block number ",self.blocknum,"\t","Program")
            self.blocks.append( [blocktype, blockdata[2:]] )
        elif blocktype == 0x04:
            if self.blocks[-1][0] != 0x84:
                Print1("Bad Continuation program")
            Print2("Block number ",self.blocknum,"\t","Program continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x83:
            Print2("Block number ",self.blocknum,"\t","Table View")
            self.blocks.append( [blocktype, blockdata[2:]] )
        elif blocktype == 0x03:
            if self.blocks[-1][0] != 0x83:
                Print1("Bad Continuation view")
            Print2("Block number ",self.blocknum,"\t","Table View continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x00:
            Print2("Block number ",self.blocknum,"\t","Empty record")
            self.blocks.append( [blocktype, blockdata] )
        else:
            Print2("Block number ",self.blocknum,"\t","Unknown type {:02x}".format(blocktype))
            self.blocks.append( [blocktype, blockdata] )
        return blocktype

    def ParseRecord( self, t, d ):
        if t == 0x82:
            Print2("Form definition")
            #hexdump(d)
            self.fulldef['form'] = d
            self.ReadForm(d)
        elif t == 0x81:
            Print2("Data")
            #hexdump(d)
            self.ReadData(d)
        elif t == 0x84:
            Print2("Program")
            #hexdump(d)
            self.fulldef['program'] = d
            self.ReadProgram(d)
        elif t == 0x83:
            Print2("Table View")
            #hexdump(d)
            self.fulldef['view'] = d
            self.ReadView(d)
        elif t == 0x00:
            if not self.all_zeros(d):
                Print1("Unexpected entries")
                hexdump(d)
        else:
            Print2("Unknown = {:02X}".format(t))
            hexdump(d)
            
    def Write( self ):
        
        # Old header (will be updated)
        HeaderRecordOut( self, self.FOLout ).Create()

        # Empties list
        self.header['emptieslist'] = 0
        EmptyRecordOut( self, self.FOLout ).Create()
        EmptyRecordOut( self, self.FOLout ).Create()
        EmptyRecordOut( self, self.FOLout ).Create()
        EmptyRecordOut( self, self.FOLout ).Create()

        # Form Definition
        self.header['formdef'] = self.header['allocatedblocks']+1
        FormRecordOut( self, self.FOLout ).Create()

        # Table View
        if self.fulldef['view'] is not None:
            self.header['view'] = self.header['allocatedblocks']+1
            ViewRecordOut( self, self.FOLout ).Create()

        # Program
        if self.fulldef['program'] is not None:
            self.header['program'] = self.header['allocatedblocks']+1
            ProgramRecordOut( self, self.FOLout ).Create()
            
        # All data records
        self.header['records'] = 0
        for f in self.data:
            DataRecordOut( self, self.FOLout).Create( f )
            self.header[ 'records' ] += 1

        # Update header
        self.FOLout.seek(0)
        self.FOLout.write( struct.pack(
            '<4H14s9HB',
            self.header['formdef'],    self.header['usedblocks'],   self.header['allocatedblocks'],
            self.header['records'],    self.header['gerb'],         self.header['fields'],
            self.header['formlength'], self.header['formrevisions'],self.header['unknown1'],
            self.header['emptieslist'],self.header['view'],         self.header['program'],
            self.header['proglines'],  self.header['diskvartype'],  self.header['diskvarlen']
            )
        )
        
        self.FOLout.close()


            
class SQL_FOL_handler(FOL_handler):
    def __init__(self, FOLfile,  FOLout='OUTPUT.FOL' , sqlfile=None, **kwargs):
        # Read in the FOL file (dbase) into an sql database sqlfile -- None for memory
        # Alternatively use the connection to use an already opened database file

        super().__init__( FOLfile,  FOLout, **kwargs)
        print(sqlfile)

        if sqlfile is not None:
            self.conn = sqlite3.connect(sqlfile)
        else:
            self.conn = sqlite3.connect(":memory:")
            
        self.conn.create_function('regexp', 2, lambda x, y: 1 if x is not Null and y is not Null and re.search(x,y) else 0)

        self.curse = self.conn.cursor()
        
        # Delete old table
        if sqlfile is not None:
            self.curse.execute('DROP TABLE IF EXISTS first')
        
        # Create new table
        self.Fields()
        self.curse.execute('CREATE TABLE first ( _ID INTEGER PRIMARY KEY,' + ','.join([f['field'].replace(' ','_')+' TEXT' for f in self.form['fields']]) + ')') 
        
        # For interest -- the maximum field length
        #print(max([len(f) for r in self.data for f in r]))
        self.AddData()

        self.curse.execute('SELECT *  FROM first WHERE _ID<?',(100,))
        for f in self.curse.fetchall():
            print(f)
        
        s = SQL_record().findID(self.curse,13)
        print(s)
        print(s.tup)
        print(self.fields)
        print(SQL_record().Search( self.curse, {'Color' : '..red..' } ) )
        
    
    def Fields( self ):
        self.fields = [f['field'].replace(" ","_") for f in self.form['fields']]
        SQL_record.RegisterFields(self.fields)
        Print3(self.fields)

    def AddData( self ):
        # Add all data
        self.curse.executemany('INSERT INTO first (' + ','.join(self.fields) + ') VALUES ('+ ','.join(list('?'*self.header['fields'])) + ')',self.data)
        self.conn.commit()
        
    def Insert( self, sqlrec ):
        # Add all data
        self.curse.execute('INSERT INTO first (' + ','.join(self.fields) + ') VALUES ('+ ','.join(list('?'*self.header['fields'])) + ')',sqlreq.tup())
        self.conn.commit()
        
    def Write( self ):
        self.curse.execute('SELECT ' + ','.join(self.fields) + ' FROM first')
        self.data = self.curse.fetchall()
        Print2(self.data)

        super().Write()


    def __del__(self):
        self.conn.close()


def FC2SQLquery( fld, fol_string ):
    # converts an first choice query to sqlite3 syntax
    
    # returns a tuple of
    # 1. query text wit hplaceholders
    # 2. list of params
    
    # None if no query
    # 
    if fol_string is None:
        return None
    
    # trim off leading and training whitespace
    fol = fol_string.strip()
    if fol == '':
        return None
    
    # Test for negation
    if fol[0] == '/':
        negate = " NOT "
        fol = fol[1:]
    else:
        negate = ""
        
    # Test for Wildcard
    if fol.find('..')>=0 or fol.find('?')>=0:
        return (
            fld + negate + ' LIKE ?', 
            [fol.replace('..','_').replace('?','%')] 
            )
        
    # Test for Range
    if fol.find('->')>0:
        return (
            fld + negate + ' BETWEEN ? AND ?',
            fol.split('->',1)
            )
        
    # Test for conditions
    if fol[0] == '=':
        if negate == '':
            return (
                fld + '= ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '!= ?',
                [fol[1:]]
                )
    if fol[0].find('<=') == 0:
        if negate == '':
            return (
                fld + '<= ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '> ?',
                [fol[1:]]
                )
    if fol[0].find('>=') == 0:
        if negate == '':
            return (
                fld + '>= ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '< ?',
                [fol[1:]]
                )
    if fol[0] == '>':
        if negate == '':
            return (
                fld + '> ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '<= ?',
                [fol[1:]]
                )
    if fol[0] == '<':
        if negate == '':
            return (
                fld + '< ?',
                [fol[1:]]
                )
        else:
            return (
                fld + '>= ?',
                [fol[1:]]
                )
        
    return (
        fld + ' LIKE ?',
        [fol]
        )


class SQL_record:
    field_list = None

    @classmethod
    def RegisterFields( cls, field_list ):
        cls.field_list = field_list

    def __init__( self ):
        if type(self).field_list is None:
            print("SQL_record uninitialized with field list")
            raise ValueError
        self.clear()
        
    def __setitem__(self,key,value):
        self._record[key] = value
    
    def __getitem__(self,key):
        if key in self._record:
            return self._record[key]
        return ''
    
    @property
    def tup(self):
        return tuple( [ self.__getitem__(f) for f in type(self).field_list] )
    
    @tup.setter
    def tup(self, t):
        for i,f in enumerate(type(self).field_list):
            self._record[f] = t[i]
    
    def id_tup(self):
        if '_ID' in self._record:
            return (self.__getitem__('_ID'),*self.tup)
        else:
            return (None,*self.tup)
            
    def clear( self ):
        self._record = {}      
    
    def Search( self, cursor, search_dict ):
        print(search_dict)
        where, params = self.where( search_dict )
        print(where,params)
        print('SELECT _ID FROM first ' + where , params )
        return cursor.execute('SELECT _ID FROM first ' + where , params ).fetchall()

    def where( self, search_dict ):
        # returns the WHERE clause (if needed, else '')
        # and the parameters for placeholders
        # as a tuple of string and tuple)
        where_clause = []
        where_param = []
        for s in search_dict:
            print(s,search_dict[s])
            if s not in type(self).field_list:
                continue
            q = FC2SQLquery( s, search_dict[s] )
            if q is None:
                continue
            where_clause.append(q[0])
            where_param += q[1]
            print( where_clause, where_param )
        if where_clause == []:
            return ( '', [])
        return (
            ' WHERE ' + ' AND '.join(where_clause),
            tuple(where_param)
            )

    def findID( self, cursor, ID ):
        cursor.execute('SELECT ' + ','.join(type(self).field_list) + ' FROM first WHERE _ID=?',(ID,))
        result = cursor.fetchone()
        print(ID,"  --->  ",result)
        if result is None:
            self.clear()
        else:
            self.tup = result
        return self

class RecordOut:
    def __init__( self, FOLclass, FOLout ):
        self.FOLclass = FOLclass
        self.FOLout = FOLout
        
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
        self.FOLclass.header['usedblocks'] += blocks
        self.FOLclass.header['allocatedblocks'] += blocks
        
    def Write( self, data ):
        self.FOLout.write( data )

class FormRecordOut(RecordOut):
    blocktype = 0x82
    
    def Create( self ):
        self.Split_Label_2_Blocks( self.FOLclass.fulldef['form'] )

class ViewRecordOut(RecordOut):
    blocktype = 0x83

    def Create( self ):
        self.Split_Label_2_Blocks( self.FOLclass.fulldef['view'] )

class ProgramRecordOut(RecordOut):
    blocktype = 0x84

    def Create( self ):
        self.Split_Label_2_Blocks( self.FOLclass.fulldef['program'] )

class EmptyRecordOut(RecordOut):

    def Create( self ):
        self.UpdateSizes( 1 )
        working = b'\x00'*128
        self.Write(working)

class HeaderRecordOut(RecordOut):

    def Create( self ):
        self.FOLclass.header['usedblocks'] = 3
        self.FOLclass.header['allocatedblocks'] = 3
        working = self.FOLclass.header['fulldef']
        self.Write(working)

class DataRecordOut(RecordOut):
    blocktype = 0x81

    def Create( self, field_values ):
        # return blocks and record bytearray
        # field_values is a tuple
        ba = bytearray(b'')
        for tw,v in zip(self.FOLclass.form['textwrap'],field_values):
            ba += self.SingleField(tw,v)
        self.Split_Label_2_Blocks( ba )
        
    def SingleField( self, tw, string ):
        # returns bytearray
        ba = bytearray(b'XX')+tw.Parse(string).encode('utf-8').replace(b'\n',b'\r')
        cr = ba[2:].count(b'\r')
        struct.pack_into('>H',ba,0,len(ba)-2+cr)
        return ba
    

if __name__ == '__main__':
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
        cl.add_argument("-v","--verbose",help="Add more output",action="count")
        return cl.parse_args()
        
if __name__ == '__main__': # command line
    """
    First Choice FOL_handler File
    *.fol
    """
    args = CommandLine() # Get args from command line
    Verbose = args.verbose or 0
    print("Verbose",Verbose,args)
    
    # Set up keyboard interrupt handler
    signal.signal(signal.SIGINT, signal_handler )
    
    # Start program
    
    # Read in databaase (FOL file already open from command line)
    dbase_class = SQL_FOL_handler( args.In, args.Out )
    
    # Changes could happen here,
    # If nothing else, this is a test of parsing
    
    # Write out file to new database
    dbase_class.Write()

    sys.exit(None)
    
else: #module
    dbase_class = None
    def OpenDatabase( databasename ):
        global dbase
        dbase_class = SQL_FOL_handler( databasename )
        
    def Fields():
        global dbase_class
        return dbase_class.fields;
        
    def SaveDatabase( newdatabase ):
        global dbase_class
        if dbase_class is not None:
            dbase_class.Write()
    
    
