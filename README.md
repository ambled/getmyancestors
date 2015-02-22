getmyancestors
==============

getmyancestors.py is a python script that downloads family trees in GEDCOM format from FamilySearch.

It is meant to be a replacement for the GetMyAncestors program from Ohana Software (previously available at http://www.ohanasoftware.com/?sec=downloads&page=GetMyAncestors).

This program is now in production phase, but bugs might still be present. Features will be added on request. It is provided as is.

This script requires the requests module to work. To install this module, run this in your terminal: "pip install requests" (or "pip install --user requests" if you don't have admin rights on your machine).

This script requires python 3.4 to run due to some novel features in the argparse module (https://docs.python.org/3/whatsnew/3.4.html#argparse)

Current version was updated on February 22nd 2015.

Examples
========

Download four generations of ancestors for individual LF7T-Y4C including all children and their spouses for each ancestor:

getmyancestors.py -a 4 -d 0 -u username -p password -i LF7T-Y4C -o out.ged

Download four generations of ancestors for individual LF7T-Y4C and generate a verbose log file:

getmyancestors.py -a 4 -d 0 -u username -p password -i LF7T-Y4C -o out.ged -l out.log -v

Download six generations of ancestors for individuals L4S5-9X4 and LHWG-18F including all children, grandchildren and their spouses for each ancestor:

getmyancestors.py -a 6 -d 1 -u username -p password -i L4S5-9X4,LHWG-18F -o out.ged

Support
=======

Send questions, suggestions, or feature requests to giulio.genovese@gmail.com
