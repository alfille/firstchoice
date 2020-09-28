#!/usr/bin/python3

# First choice pack and unpack into sqlite

import sys
import struct
import signal

import click

BLOCKSIZE = 128

def hexdump(block):
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

@click.command()
@click.argument('dbase',type=click.File('rb'))
def validate( dbase ):
    """
    First Choice Database File
    *.fol
    """
    d = Database(dbase)
    

class Database:
    # database header
    header_format = '<4H14s9HB'
    nonheader_format = "<H126s"
    gerb = b'\x0cGERBILDB3   \x00'
    
    def __init__(self,dbase):
        self.dbase = dbase
        self.filename = sys.argv[-1]
        self.blocknum = 0
        self.data = []
        self.blocks = [[0,""]]
        self.program = None
        self.view = None
        
        self.header = b""
        for n in range(4):
            if not self._read():
                print("Cannot read full 4 block header")
                return
            self.header += self.block
        self.Header()
            
        self.halfheader = b""
        for n in range(4):
            if not self._read():
                print("Cannot read full second 4 block header")
                return
            self.halfheader += self.block
        self.HalfHeader()
        
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
            
    def apply_struct( self, structure, string ):
        slen = struct.calcsize( structure )
        return struct.unpack( structure, string[:slen] ) + (string[slen:], )
        
    def all_zeros( self, string ):
        for b in string:
            if b != 00:
                return False
        return True
        
    def ReadText( self, string ):
        l, d = self.apply_struct( '>H', string )
        ll = 0
        while ll < l:
            # \r counts for 2
            if d[ll] == 0x0d:
                l -= 1
                self.ods += 1
            ll += 1 
        #hexdump(string[:2])
        return (l, d[:l], d[l:])     
        
    def _read(self):
        self.block = self.dbase.read(BLOCKSIZE)
        self.byte0 = None
        self.byte1 = None
        if len(self.block) == 0:
            return False
        self.blocknum += 1
        return True
    
    def Header( self ):
        #hexdump(self.header)
        data = self.apply_struct( type(self).header_format, self.header )
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
            'tableview'      : data[10],
            'program'        : data[11],
            'unknown2'       : data[12],
            'unknown3'       : data[13],
            'diskvarlen'     : data[14],
            'diskvar'        : data[15][:data[14]],
            }
        print( self.header )
        if self.header['usedblocks'] != self.header['allocatedblocks']:
            print("Blocks don't match")
        if type(self).gerb != data[4]:
            print("GERB doesn't match")

    def HalfHeader( self ):
        print("Half Header")
        hexdump(self.halfheader)
        d = self.halfheader
        while True:
            try:
                a,b,d = self.apply_struct( "<HH", d )
            except:
                break
            if a==0 and b == 0:
                break
            print('[{},{}]'.format(a,b),end="  ")
        print('\n')

    def hexbyte( self ):
        if self.byte0 is None:
            s = ""
        elif self.byte0 == 0 :
            s = "*"
        else:
            s = '{:02x}'.format(self.byte0)
        self.byte0 = self.byte1
        self.byte1 = None

        return s
        
    def TextLetter( self ):
        if self.byte0 == 0x80:
            self.textstring += " "
        else:
            self.textstring += '{:c}'.format(self.byte0 & 0x7F)
        self.byte0 = None
        self.byte1 = None
            
    def FieldLetter( self ):
        if self.byte0 == 0x80:
            # generic field
            self.fieldstring += " "
        elif self.byte0 == 0x81:
            # generic field
            self.fieldtype = " "
        elif self.byte0 == 0x82:
            # numeric field
            self.fieldtype = "N"
        elif self.byte0 == 0x83:
            # date field
            self.fieldtype = "D"
        elif self.byte0 == 0x84:
            # time field
            self.fieldtype = "T"
        elif self.byte0 == 0x85:
            # yes-no field
            self.fieldtype = "Y"
        else:
            self.fieldstring += '{:c}'.format(self.byte0 & 0x7F)
        self.byte0 = None
            
    def ReadRichText( self,byte ):
        if byte is None:
            self.textstring += self.hexbyte() + self.hexbyte()
            return
            
#        if self.byte0 is not None:
#            print('Stack {:02X} {:02X} {:02X}'.format(self.byte0, self.byte1, byte) )
#        elif self.byte1 is not None:
#            print('Stack    {:02X} {:02X}'.format(self.byte1, byte) )
#        else:
#            print('Stack       {:02X}'.format( byte) )

        self.chars += 1 # All bytes, then substract 2 for background text and 1 for field name
        if byte == 0x0d:
            #purely informational
            self.ods += 1

        if byte == 0x81:
            script = 'normal'
        elif byte == 0x85:
            script = 'super'
        elif byte == 0x83:
            script = 'sub'
        else:
            script = None
            
        if self.byte1 == 0xd0:
            font = 'normal'
        elif self.byte1 == 0xd2:
            font = 'bold'
        elif self.byte1 == 0xd1:
            font = 'underline'
        elif self.byte1 == 0xd4:
            font = 'italic'
        else:
            font = None
            
        if script is not None and font is not None and self.byte0 is not None:
            # Background text
            self.TextLetter()
            self.chars -= 2
            return

        if byte == 0x90:
            font = 'normal'
        elif byte == 0x92:
            font = 'bold'
        elif byte == 0x91:
            font = 'underline'
        elif byte == 0x94:
            font = 'italic'
        else:
            font = None
        if font is not None and self.byte1 is not None:
            # Field name
            self.textstring += self.hexbyte() # clear out old
            self.chars -= 1
            self.FieldLetter()
            return
            
        self.textstring += self.hexbyte()
        self.byte1 = byte
        return
    
    def Data( self, d ):
        formblocks, d = self.apply_struct( '<H', d )
        tot_length = 0
        self.ods = 0
        self.data.append([])
        for i in range( self.header['fields'] ):
            le,li,d = self.ReadText( d )
            self.data[-1].append(li)
            tot_length += le
            
            #print("len=",le,"=>",li)
        print(self.data[-1])
        print("Total length = ", tot_length, "0x0d = ",self.ods)
    
    def Table( self, d ):
        formblocks, d = self.apply_struct( '<H', d )
        tot_length = 0
        self.ods = 0
        self.view = []
        for i in range( self.header['fields'] ):
            le,li,d = self.ReadText( d )
            self.view.append(li)
            tot_length += le
            print("len=",le,"=>",li)
        print("Total length = ", tot_length, "0x0d = ",self.ods)
    
    def Program( self, d ):
        formblocks, d = self.apply_struct( '<H', d )
        tot_length = 0
        self.ods = 0
        for i in range( 1 ):
            le,li,d = self.ReadText( d )
            self.program = li
            tot_length += le
            #print("len=",le,"=>",li)
        print("Total length = ", tot_length, "0x0d = ",self.ods)
    
    def Form( self,d ):
        self.form = {
        'fulldef' : d,
        }
        formblocks, d = self.apply_struct( '<H', d )
        self.form['length'], self.form['lines'], d = self.apply_struct( '>2H', d )
        
        print("Formblocks=",formblocks,"xFormlength=",self.form['length'],"formlines=",self.form['lines'])
        tot_length = 0
        self.ods = 0
        self.chars = 0
        dd = d[:]
        self.form['fields'] = []
        for i in range( self.header['fields'] ):
            self.textstring = ""
            self.fieldstring = ""
            self.fieldtype = " "
            le,li,d = self.ReadText( d )
            for b in li:
                self.ReadRichText(b)
            self.ReadRichText(None)
            tot_length += le
            self.form['fields'].append({'text':self.textstring,'field':self.fieldstring,'type':self.fieldtype})
        print("Total length = ", tot_length, "0x0d = ",self.ods, " chars = ",self.chars)
        print(self.form['fields'])
        #if tot_length != self.header['fields'] + self.header['formlength'] - 1:
        #    print("Formlength in header doesn't match computed");
        if self.form['length'] != tot_length + self.form['lines'] + 1:
            print("Form.length in record doesn't match computed");

    def Block2Memory( self ):
        blocktype, blockdata = ( struct.unpack( type(self).nonheader_format, self.block ) )
        if blocktype == 0x82:
            print("Block number ",self.blocknum,"\t","Form definition")
            self.blocks.append( [blocktype, blockdata] )
        elif blocktype == 0x02:
            if self.blocks[-1][0] != 0x82:
                print("Bad Continuation")
            print("Block number ",self.blocknum,"\t","Form definition continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x81:
            print("Block number ",self.blocknum,"\t","Form Data")
            self.blocks.append( [blocktype, blockdata] )
        elif blocktype == 0x01:
            if self.blocks[-1][0] != 0x81:
                print("Bad Continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x84:
            print("Block number ",self.blocknum,"\t","Program")
            self.blocks.append( [blocktype, blockdata] )
        elif blocktype == 0x04:
            if self.blocks[-1][0] != 0x84:
                print("Bad Continuation")
            print("Block number ",self.blocknum,"\t","Program continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x83:
            print("Block number ",self.blocknum,"\t","Table View")
            self.blocks.append( [blocktype, blockdata] )
        elif blocktype == 0x03:
            if self.blocks[-1][0] != 0x83:
                print("Bad Continuation")
            print("Block number ",self.blocknum,"\t","Table View continuation")
            self.blocks[-1][1] += blockdata
        elif blocktype == 0x00:
            print("Block number ",self.blocknum,"\t","Empty record")
            self.blocks.append( [blocktype, blockdata] )
        elif blocktype == 0x0c:
            print("Block number ",self.blocknum,"\t","Delete log")
            self.blocks.append( [blocktype, blockdata] )
        else:
            print("Block number ",self.blocknum,"\t","Unknown type {:02x}".format(blocktype))
            self.blocks.append( [blocktype, blockdata] )
        return blocktype

    def ParseRecord( self, t, d ):
        if t == 0x82:
            print("Form definition")
            #hexdump(d)
            self.Form(d)
        elif t == 0x81:
            print("Form data")
            #hexdump(d)
            self.Data(d)
        elif t == 0x84:
            print("Program")
            hexdump(d)
            self.Program(d)
        elif t == 0x83:
            print("Table View")
            hexdump(d)
            self.Table(d)
        elif t == 0x00:
            if not self.all_zeros(d):
                print("Unexpected entries")
                hexdump(d)
        elif t == 0x0c:
            print("Delete log")
            hexdump(d)
        else:
            print("Unknown = {:02X}".format(t))
            hexdump(d)
            
class CreateDatabase:
    def Fixup( self, blocktype, data ):
        # Add block types, continuations, and return
        # blocks, data
        # zero filled to 128 size
        
        length = len( data )
        blocks = 1
        working = bytearray(b'XX')
        while True:
            print(length)
            if length >= 126:
                working += data[:126]
                data = data[126:]
                length -= 126
                if length != 0:
                    working += b"XX"
                    blocks += 1
            else:
                working += data
                zpad = (128 - (len(working) % 128)) % 128
                working += b'\x00' * zpad
                break
        
        # Add continuations (and overwrite primary blocktype at end)
        for b in range(blocks):
            struct.pack_into( "<H", working, 128*b, blocktype & 0x7F )
        struct.pack_into( "<H", working, 0, blocktype )
        
        return blocks, working
            
    
    def DataRecord( self, field_values ):
        # return blocks and record bytearray
        ba = bytearray(b'')
        for f in field_values:
            print(f)
            ba += self.WriteDataField(f)
        return self.Fixup( 0x81, ba )
        
        
    def WriteDataField( self, string ):
        # returns bytearray
        ba = bytearray(b'XX')
        cr = 0
        for b in string:
            ba.append(b)
            if b == 0x0d:
                cr += 1
        struct.pack_into('>H',ba,0,len(string)+cr)
        return ba
        
    def Test( self ):
        hexdump( self.blocksRecord( [b'hello\r', b'more    ',b'123'])[1] )

def signal_handler( signal, frame ):
    # Signal handler
    # signal.signal( signal.SIGINT, signal.SIG_IGN )
    sys.exit(0)

        
if __name__ == '__main__':
    # Set up keyboard interrupt handler
    signal.signal(signal.SIGINT, signal_handler )
    # Start program
    #CreateDatabase().Test()
    sys.exit(validate())
