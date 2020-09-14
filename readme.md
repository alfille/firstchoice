# First Choice Convertor

This is a python program to convert PFS:First Choice database files.

## Author
Paul H Alfille 2020

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