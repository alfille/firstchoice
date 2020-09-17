#!/usr/bin/python3

# First choice pack and unpack into sqlite

import sys
import struct
import signal

import click

BLOCKSIZE = 128

def hexdump(block):
    for byte in block:
      sys.stdout.write('%02x ' % byte )
    sys.stdout.write('\n')

@click.command()
@click.argument('dbase',type=click.File('rb'))
def validate( dbase ):
	"""
	First Choice Database File
	*.fol
	"""

	Parser(dbase)

class Parser:
	# database header
	header_format = '<4H14s6H7s'
	nonheader_format = "<H126s"
	gerb = b'\x0cGERBILDB3   \x00'
	more_head = b'\xff\xff\x00\x00\x02\x00\x08'
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
		if self._read():
			self.Header()
			
		allocatedblocks = 0
		usedblocks = 0
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
		
		hexdump(self.block)
		data = self.apply_struct( type(self).header_format, self.block )
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
		if type(self).more_head != data[11]:
			print("Rest of header doesn't match")
		if not self.all_zeros(data[12]):
			print("Header block unzeroed")

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
			
#		if self.byte0 is not None:
#			print('Stack {:02X} {:02X} {:02X}'.format(self.byte0, self.byte1, byte) )
#		elif self.byte1 is not None:
#			print('Stack    {:02X} {:02X}'.format(self.byte1, byte) )
#		else:
#			print('Stack       {:02X}'.format( byte) )

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
		for i in range( self.fields ):
			le,li,d = self.ReadText( d )
			tot_length += le
			print( '[{}]'.format(le)+''.join(self.ReadRichText(b) for b in li)+self.ReadRichText(None) )
		print("Total length = ", tot_length, "0x0d = ",self.ods, " chars = ",self.chars)
		if tot_length != self.fields + self.formlength - 1:
			print("Formlength in header doesn't match computed");
		if xformlength != tot_length + formlines + 1:
			print("xFormlength in record doesn't match computed");

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
			print("Block number ",self.blocknum,"\t","Form Data continuation")
			self.data[-1][1] += blockdata
		elif blocktype == 0x00:
			print("Block number ",self.blocknum,"\t","Empty record")
			self.data.append( [blocktype, blockdata] )
		elif blocktype == 0x08:
			print("Block number ",self.blocknum,"\t","Header half continuation")
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

def signal_handler( signal, frame ):
    # Signal handler
    # signal.signal( signal.SIGINT, signal.SIG_IGN )
    sys.exit(0)

		
if __name__ == '__main__':
    # Set up keyboard interrupt handler
    signal.signal(signal.SIGINT, signal_handler )
    # Start program
    sys.exit(validate())
