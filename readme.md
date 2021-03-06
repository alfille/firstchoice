# First Choice Convertor

This is a python program to convert PFS:First Choice database files.

## Author
Paul H Alfille 2020

## First Choice

![Screenshot](images/FirstChoice.png)

- [First Choice Convertor](#first-choice-convertor)
  * [Author](#author)
  * [First Choice](#first-choice)
  * [History](#history)
    + [Why First Choice](#why-first-choice)
    + [Data Extraction](#data-extraction)
    + [Current Approach](#current-approach)
    + [Design](#design)
  * [Alternatives](#alternatives)
  * [License](#license)
- [Get the program](#get-the-program)
- [Run the program (server)](#run-the-program--server-)
- [Web browser](#web-browser)
  * [Choose Database file and user](#choose-database-file-and-user)
  * [Form view](#form-view)
  * [Table view](#table-view)
- [First Choice Database Format Information](#first-choice-database-format-information)
  * [Details](#details)
    + [Size](#size)
    + [Numbers](#numbers)
    + ["Magic" File ID](#-magic--file-id)
    + [Record types](#record-types)
    + [Header](#header)
    + [Empties list](#empties-list)
    + [Text Encoding](#text-encoding)
      - [Types](#types)
      - [Additive attributes](#additive-attributes)
      - [Exclusive attributes](#exclusive-attributes)
      - [General format](#general-format)
      - [Text bytes -- 1 byte char](#text-bytes----1-byte-char)
      - [Text bytes -- 2 byte char](#text-bytes----2-byte-char)
      - [Text bytes -- 3 byte char](#text-bytes----3-byte-char)
    + [Form Description Record](#form-description-record)
      - [Screen Layout](#screen-layout)
      - [Form Field](#form-field)
      - [Field Name Encoding](#field-name-encoding)
    + [Data Record](#data-record)
      - [Data Field](#data-field)
    + [Table View](#table-view)
      - [Field width](#field-width)
    + [Program Record](#program-record)
      - [Program line](#program-line)
    + [Deleted Record / Empty Block](#deleted-record---empty-block)
    + [Continuation Record](#continuation-record)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

## History
### Why First Choice
I found First Choice a great solution for indexing collections for myself and my wife, back in the early DOS days. Although Windows and other developments left that program behind, the program still functions, especially in DOSBOX. I run it on Windows, Linux, Mac and even a Chromebook.

The problem with this approach is that in a multi-computer environment (it's 2020!) the program needs to run locally. While the file can be copied over the network prior to program start, and back at the end, it's a fragile process.

![Classing PFS:First Choice](images/Traditional.svg)

### Data Extraction
My first conversion programs were quite successful. See the Sourceforge page: [first2html](http://first2html.sourceforge.net/)

This is a set of perl and C programs that can extract the data to HTML (Which is easy to manipulate for display).

### Current Approach
While extracting data is nice, it would be nice to have a server-based multiuser database with conversion from and to the original First Choice format. The goal is to make the database view and editing web-based.

### Design
* Data extraction with Python3
* Data conversion to SQLite3 for on-line use
* Data conversion back to FirstChoice .FOL with python3
* Add journal and backup in SQL

![Web based](images/Web.svg)

## Alternatives
* [FirstOut](https://file-convert.com/fout.htm) -- Comercial, extract only
* [First2html](http://first2html.sourceforge.net/) -- Open Source, extract only
* The module first.py can as standalone to parse and write a FOL file. It is used by web program for the FOL parsing.

## License

FirstChoice  is released under the terms of MIT License.

# Get the program
[Source](http://github.com/alfille/firstchoice) (pure python3)

# Run the program (server)
* Should be run as a web server (port 8080 by default)
* FOL files should be in the parent directory (scanned recursively)
* Needs many of the standard python modules
 * sqlite3
 * http.server, cgi
 * random, os, textwrap, argparse, sys, struct, signal
* From the command line:`python3 webfirst.py`
* Command line arguments are all optional (localhost:8080 is the default)
![Command Line Options](images/Help.png)

# Web browser
Find URL of server
## Choose Database file and user
![Choose](images/Choose.png)

* user name is arbitrary
 * Setting like table column layout follow user/file pair
 * Authorization or auditing could be implemented
* File must end in <.fol> or <.FOL>
* File integrity not yet tested

## Form view
![Form](images/Form.png)

* From here is possible to put a search pattern
* Add a new record
* Edit an existing record
* Copy / Delete a record

## Table view
![Table](images/Table.png)

* Tables follow the last search
 * Listed in order by column contents left to right 
* Click on a record to open it in Form view
* Columns names can be dragged around
* Column widths can be dragged (it's tricky)
* Contents can be downloaded to an Excel-compatible CSV file
* Columns can layout can be customized in the menu:

![Column menu](images/Columns.png)

 

# First Choice Database Format Information

## Details
Here follows a summary of the discovered fields in a FirstChoice Database.

### Size
All files are in 128 byte blocks. The blocks have relatively set content, and if a record extends beyond 128 bytes, a continuation record follows
### Numbers
Numbers are generally 2-byte little endian unsigned integers. Big Endian is used in some form definition fields!

### "Magic" File ID
* The file extension is ".FOL"
* There is a special string at byte 9 [GERBILDB](http://fileformats.archiveteam.org/wiki/PFS:First_Choice)

### Record types
* Header
* "Empties list" (Always Record 4 = 5th block)
* Empty
* Form description (+ continuations)
* Data record (+ continuations)

| Pos | Size |Value|Description| 
|----:|-----:|:---|:-----------|
|0|2|0x81|Data record|
|0|2|0x01|Data continuation|
|0|2|0x82|Form Description View|
|0|2|0x02|Form Description continuation|
|0|2|0x83|Table View|
|0|2|0x03|Table View continuation|
|0|2|0x84|Formula|
|0|2|0x04|Formula continuation|

### Header
Always first block (block 0)

| Pos | Size |Type| Description |
|----:|-----:|:---|:------------|
|0|2|int|Form definition location (block#-1)|
|2|2|int|Last used block **not always accurate** |
|4|2|int|Total file blocks - 1|
|6|2|int|Data records|
|8|14|chars|Magic string '0x0cGERBILDB3   0x00'|
|22|2|int|Number of Database fields (+1)|
|24|2|int|Form length in chars? |
|26|2|int|Form revisions (starts at 1)|
|28|2|int|more2|
|30|2|int|entries in empties list, 0 for none|
|32|2|int|Table View location (block#-1), 0xFFFF for none|
|34|2|int|Block number of program record (block#-1)|
|36|2|int|more 6|
|38|2|int|more 7|
|40|1|byte|size of next field (8 byte minimum)||
|41||chars|@DISKVAR value for formulas|

### Empties list
Always 5th block (block 4)

* List of paired numbers (can go on for several records)
* Number of pairs in Header field
* Some extra repeated pairs can persist

| Location | Size |
|----:|-----:|
|Int (2byte) block# -1|Int number of blocks|

### Text Encoding

#### Types
* Field names
* Background text
* Data text

#### Additive attributes
* **Bold** on/off
* *Italic* on/off
* _Underline_ on/off
* These attributes are addative

#### Exclusive attributes
* Normal
* Superscript
* Subscript
* These attributes are mutually exclusive, but can be combined with Bold/Italic/Underline

#### General format
| Size |Type| Description |
|-----:|:---|:------------|
|2|int-BE|Field size (in bytes)|
|multiple|bytes|text bytes|

#### Text bytes -- 1 byte char
| Position |Type|Value|Description |
|-----:|:---|:---|:---------|
|1|all|0x13|Carriage Return (counts as 2 bytes in field length)|
|1|data|0x00-0x7F|Ascii character (counts as one byte)|

#### Text bytes -- 2 byte char
|Position|Type|Value|Description |
|-----:|:---|:---|:---------|
|1|all|0x80|space|
|1|field|0x81|Text (default)|
|1|field|0x82|Numeric|
|1|field|0x83|Date|
|1|field|0x84|Time|
|1|field|0x85|Yes/No|
|2|field|0x90|normal|
|2|field|0x91|_Underline_|
|2|field|0x92|**Bold**|
|2|field|0x94|*Italic*|
|2|data|0x81|_Underline_|
|2|data|0x82|**Bold**|
|2|data|0x84|*Italic*|

#### Text bytes -- 3 byte char
|Position|Type|Value|Description |
|-----:|:---|:---|:---------|
|1|all|0x80|space|
|1|field|0x81|Text (default)|
|1|field|0x82|Numeric|
|1|field|0x83|Date|
|1|field|0x84|Time|
|1|field|0x85|Yes/No|
|2|background,field|0xd0|normal|
|2|background,field|0xd1|_Underline_|
|2|background,field|0xd2|**normal**|
|2|background,field|0xd4|Italic|
|2|data|0xd0|normal|
|2|data|0xd1|_Underline_|
|2|data|0xd2|**normal**|
|2|data|0xd4|Italic|
|3|field,data|0x82|subscript|
|3|field,data|0x84|superscript|
|3|background|0x81|normal|
|3|background|0x83|subscript|
|3|background|0x85|superscript|

### Form Description Record
note that "int-BE" is Big Endian integer

| Pos | Size |Type| Description |
|----:|-----:|:---|:------------|
|0|2|int|0x82 Form description start (only one)|
|2|2|int|total blocks (this + continuations)|
|4|2|int-BE|lines in form screen|
|6|2|int-BE|length+lines+1|
|8|120|data|form fields| 

#### Screen Layout
![Record screen shot](Record.png)

* Fixed width ascii chars
* 78 char width (border line lanes 2 chars)
* 20 displays lines (but will scroll down)
* No position addressing. All layout from upper left.
* Move to next line with 0x0d or line wrap

#### Form Field 
Background text, CR and spaces are optional and may be multiple.


#### Field Name Encoding
Field names are 2 bytes per char plus a field type char:

### Data Record
| Pos | Size |Type| Description |
|----:|-----:|:---|:------------|
|0|2|int|0x81 Data record start|
||||Data Fields|

#### Data Field
A 0x0d is added to end if next field in on another line

Data entry length cannot extend past location of next field on screen. (I.e. long fields do not move next field).

### Table View
| Pos | Size |Type| Description |
|----:|-----:|:---|:------------|
|0|2|int|0x83 Data record start|
|2|2|int|total blocks (this + continuations)|

#### Field width
A 0x0d is added to end if next field in on another line

### Program Record
| Pos | Size |Type| Description |
|----:|-----:|:---|:------------|
|0|2|int|0x84 Data record start|
|2|2|int|total blocks (this + continuations)|

#### Program line
A 0x0d is added to end if next field in on another line

Data entry length cannot extend past location of next field on screen. (I.e. long fields do not move next field).

### Deleted Record / Empty Block
| Pos | Size |Type| Description |
|----:|-----:|:---|:------------|
|0|2|int|0|
|2|126|chars|all 0x00|

### Continuation Record
| Pos | Size |Type| Description |
|----:|-----:|:---|:------------|
|0|2|int|0x01 Data continuation|
|0|2|int|0x02 Form continuation|
|0|2|int|0x04 Program continuation|
|2|126|data|continuation of prior block payload|

