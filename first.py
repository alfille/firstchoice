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


def ehexdump(block):
    global errlog
    for byte in block:
        errlog +='\"{:02x}\",'.format(byte)

@click.command()
@click.argument('dbase',type=click.File('rb'))
def validate( dbase ):
    """
    First Choice Database File
    *.fol
    """

    global errlog
    errlog = '\"'+sys.argv[-1]+'\",'
    Parser(dbase)
    sys.stderr.write(errlog+"\n")

class Parser:
    # database header
    header_format = '<4H14s9HB'
    nonheader_format = "<H126s"
    gerb = b'\x0cGERBILDB3   \x00'
    form_format = '>BxHH'
    form_data_block = '<H'
    half_block = '<H'
    form_field = '>H'
    
    def __init__(self,dbase):
        self.dbase = dbase
        self.blocknum = 0
        self.data = [[0,""]]
        self.textstring = ""
        self.fieldstring = ""
        
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
                
        if allocatedblocks != self.allocatedblocks:
            print("Allocated blocks count is off")
        if usedblocks != self.usedblocks:
            print("Used blocks count is off")
        
        for [t,d] in self.data:
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
        hexdump(self.header)
        data = self.apply_struct( type(self).header_format, self.header )
        print(data)
        self.fieldnameblock = data[0]
        self.usedblocks = data[1]
        self.allocatedblocks = data[2]
        self.records = data[3]
        if self.usedblocks != self.allocatedblocks:
            print("Blocks don't match")
        if type(self).gerb != data[4]:
            print("GERB doesn't match")
        self.fields = int(data[5])
        self.formlength = data[6]
        self.revisions = data[7]
        global errlog
        errlog += "{},{},{},".format(self.fields,self.formlength,self.revisions)
        self.empties = data[9]
        self.tableview = data[10]
        self.programstart = data[11]
        print(data[15][:data[14]])

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
            
    def TextString( self ):
        if self.textstring == "":
            return ""
        f = "{"+self.textstring+"}"
        if len(self.textstring) > 1:
            f += "["+'{:04x}'.format(len(self.textstring))+"]"
        self.textstring = ""
        return f
    
    def FieldLetter( self ):
        if self.byte0 == 0x80:
            # generic field
            self.fieldstring += " "
        elif self.byte0 == 0x81:
            # generic field
            self.fieldstring += ": "
        elif self.byte0 == 0x82:
            # numeric field
            self.fieldstring += ":N"
        elif self.byte0 == 0x83:
            # date field
            self.fieldstring += ":D"
        elif self.byte0 == 0x84:
            # time field
            self.fieldstring += ":T"
        elif self.byte0 == 0x85:
            # yes-no field
            self.fieldstring += ":Y"
        else:
            self.fieldstring += '{:c}'.format(self.byte0 & 0x7F)
        self.byte0 = None
            
    def FieldString( self ):
        if self.fieldstring == "":
            return ""
        f = "<"+self.fieldstring+">"
        self.fieldstring = ""
        return f
    
    def ReadRichText( self,byte ):
        if byte is None:
            return self.FieldString()+self.TextString()+self.hexbyte() + self.hexbyte()
            
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
            return self.FieldString()

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
            s = self.TextString() + self.hexbyte()
            self.chars -= 1
            self.FieldLetter()
            return s
            
        s = self.hexbyte()
        self.byte1 = byte
        if s != "":
            return self.FieldString()+self.TextString()+s
        else:
            return ""
    
    def Data( self, d ):
        formblocks, d = self.apply_struct( type(self).form_data_block, d )
        tot_length = 0
        self.ods = 0
        for i in range( self.fields ):
            le,li,d = self.ReadText( d )
            tot_length += le
            print("len=",le,"=>",li)
        print("Total length = ", tot_length, "0x0d = ",self.ods)
    
    def Table( self, d ):
        formblocks, d = self.apply_struct( type(self).form_data_block, d )
        tot_length = 0
        self.ods = 0
        for i in range( self.fields ):
            le,li,d = self.ReadText( d )
            tot_length += le
            print("len=",le,"=>",li)
        print("Total length = ", tot_length, "0x0d = ",self.ods)
    
    def Program( self, d ):
        formblocks, d = self.apply_struct( type(self).form_data_block, d )
        tot_length = 0
        self.ods = 0
        for i in range( 1 ):
            le,li,d = self.ReadText( d )
            tot_length += le
            print("len=",le,"=>",li)
        print("Total length = ", tot_length, "0x0d = ",self.ods)
    
    def Half( self, d ):
        formoffset, d = self.apply_struct( type(self).half_block, d )
        print("Def offset=",formoffset," is really ",formoffset+10)
        if not self.all_zeros(d):
            print("More half data")
            hexdump(d)
    
    def Form( self,d ):
        formblocks, xformlength, formlines, d = self.apply_struct( type(self).form_format, d )
        print("Formblocks=",formblocks,"xFormlength=",xformlength,"formlines=",formlines)
        tot_length = 0
        self.ods = 0
        self.chars = 0
        dd = d[:]
        for i in range( self.fields ):
            le,li,d = self.ReadText( d )
            tot_length += le
            print( '[{}]'.format(le)+''.join(self.ReadRichText(b) for b in li)+self.ReadRichText(None) )
        print("Total length = ", tot_length, "0x0d = ",self.ods, " chars = ",self.chars)
        if tot_length != self.fields + self.formlength - 1:
            print("Formlength in header doesn't match computed");
        if xformlength != tot_length + formlines + 1:
            print("xFormlength in record doesn't match computed");
        global errlog
        errlog += "{},{},{},{},{},".format(xformlength,formlines,tot_length,self.ods,self.formlength-tot_length)
        if self.formlength != tot_length:
            ehexdump(dd[self.formlength-tot_length:])

    def Block2Memory( self ):
        blocktype, blockdata = ( struct.unpack( type(self).nonheader_format, self.block ) )
        if blocktype == 0x82:
            print("Block number ",self.blocknum,"\t","Form definition")
            self.data.append( [blocktype, blockdata] )
        elif blocktype == 0x02:
            if self.data[-1][0] != 0x82:
                print("Bad Continuation")
            print("Block number ",self.blocknum,"\t","Form definition continuation")
            self.data[-1][1] += blockdata
        elif blocktype == 0x81:
            print("Block number ",self.blocknum,"\t","Form Data")
            self.data.append( [blocktype, blockdata] )
        elif blocktype == 0x01:
            if self.data[-1][0] != 0x81:
                print("Bad Continuation")
            self.data[-1][1] += blockdata
        elif blocktype == 0x84:
            print("Block number ",self.blocknum,"\t","Program")
            self.data.append( [blocktype, blockdata] )
        elif blocktype == 0x04:
            if self.data[-1][0] != 0x84:
                print("Bad Continuation")
            print("Block number ",self.blocknum,"\t","Program continuation")
            self.data[-1][1] += blockdata
        elif blocktype == 0x83:
            print("Block number ",self.blocknum,"\t","Table View")
            self.data.append( [blocktype, blockdata] )
        elif blocktype == 0x03:
            if self.data[-1][0] != 0x83:
                print("Bad Continuation")
            print("Block number ",self.blocknum,"\t","Table View continuation")
            self.data[-1][1] += blockdata
        elif blocktype == 0x00:
            print("Block number ",self.blocknum,"\t","Empty record")
            self.data.append( [blocktype, blockdata] )
        elif blocktype == 0x0c:
            print("Block number ",self.blocknum,"\t","Delete log")
            self.data.append( [blocktype, blockdata] )
        else:
            print("Block number ",self.blocknum,"\t","Unknown type {:02x}".format(blocktype))
            self.data.append( [blocktype, blockdata] )
        return blocktype

    def ParseRecord( self, t, d ):
        if t == 0x82:
            print("Form definition")
            hexdump(d)
            self.Form(d)
        elif t == 0x81:
            print("Form data")
            hexdump(d)
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
        elif t == 0x08:
            print("Half 08")
            self.Half(d)
        elif t == 0x09:
            print("Other Half 09")
            self.Half(d)
        elif t == 0x0c:
            print("Delete log")
            hexdump(d)
        else:
            print("Unknown")
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
        hexdump( self.DataRecord( [b'hello\r', b'more    ',b'123'])[1] )

def signal_handler( signal, frame ):
    # Signal handler
    # signal.signal( signal.SIGINT, signal.SIG_IGN )
    sys.exit(0)

        
if __name__ == '__main__':
    # Set up keyboard interrupt handler
    signal.signal(signal.SIGINT, signal_handler )
    # Start program
    CreateDatabase().Test()
    sys.exit(validate())
