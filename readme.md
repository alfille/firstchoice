# First Choice Convertor

This is a python program to convert PFS:First Choice database files.

## Author
Paul H Alfille 2020

![Screenshot](FirstChoice.png)

## History
### Why First Choice
I found First Choice a great solution for indexing collections for myself and my wife, back in the early DOS days. Although Windows and other developements left that program behind, the program still functions, especially in DOSBOX. I run it on Windows, Linux, Mac and even a Chromebook.

The problem with this approach is that in a multi-computer environment (it's 2020!) the program needs to run locally. While the file can be copied over the network prior to program start, and back at the end, it's a fragile process.

### Data Extraction
My first conversion programs were quite successful. See the Sourceforge page: [first2html](http://first2html.sourceforge.net/)

This is a set of perl and C programs that can extract the data to HTML (Which is easy to manipulate for display).

### Current Approach
While extracting data is nice, it would be nice to have a server-based multiuser database with conversion from and to the original First Choice format. The goal is to make the database view and editting web-based.

### Design
* Data extraction with Python3
* Data conversion to SQLite3 for on-line use (via Flask)
* Data converion back to FirstChoice .FOL with python3
* Add journal and backup in SQL.

## Alternatives
* [FirstOut](https://file-convert.com/fout.htm) -- Comercial, extract only
* [First2html](http://first2html.sourceforge.net/) -- Open Source, extract only

## License

FirstChoice  is released under the terms of MIT License.

## Details
Here follows a summary of the discovered fields in a FirstChoice Database.

### Size
All files are in 128 byte blocks. The blocks have relatively set content, and if a record extends beyond 128 bytes, a continuation record follows
### Numbers
Numbers are 2-byte little endian unsigned integers. 
### Text Encoding
Text (for the "background text" in the form and the text entries in the records are 3-bytes per character:

1. 0x80 normal, 0x83 subscript, 0x85 superscript
2. 0xd0 nornal, 0xd1 _Underline_, 0xd2 **Bold**, 0xd4 *Italic*
3. Ascii char | 0x80 (high bit set)

### Field Encoding
Field names are 2 bytes per char plus a field type char:

1. 0x90 normal, 0x91 Underline, 0x92 Bold, 0x94 Italic
2. Ascii char | 0x80 (high bit set), 0x80 is a space

Special case for chars -- end of field:

* 0x81 Freeform field type
* 0x82 Numeric
* 0x83 Date
* 0x84 Time
* 0x85 Yes/No

### Magic fields
* The file extension is ".FOL"
* There is a special string at byte 9 [GERBILDB](http://fileformats.archiveteam.org/wiki/PFS:First_Choice)

### Record types
* Header
* "Half Header" (Optional record 4)
* Empty
* Form description (+ continuations)
* Data record (+ continuations)

### Header
| Pos | Size | Description |
|----:|-----:|:------------|
|0|2|Post-header block - 1|
|2|2|Last used block - 1|
|4|2|File blocks - 1|
|6|2|Data records|
|8|13|Magic string|
|21|2||
### Form Description
### Data Record
### Deleted Record
### Continuation
