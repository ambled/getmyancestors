#!/usr/bin/env python3
"""
   mergemyancestors.py - Merge GEDCOM data from FamilySearch Tree
   Copyright (C) 2014-2015 Giulio Genovese (giulio.genovese@gmail.com)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

   Written by Giulio Genovese <giulio.genovese@gmail.com>
"""

from __future__ import print_function

# global import
import os, sys, argparse

# local import
sys.path.append(os.path.dirname(sys.argv[0]))
from getmyancestors import Indi
from getmyancestors import Fam
from getmyancestors import Tree

class Gedcom:

    def __init__(self,file):
        self.f = file
        self.num = None
        self.level = 0
        self.pointer = None
        self.tag = None
        self.data = None
        self.flag = False
        self.indi = dict()
        self.fam = dict()
        self.__parse()
        self.__add_id()

    def __parse(self):
        while self.__get_line():
            if self.tag == 'INDI':
                self.num = int(self.pointer[2:len(self.pointer)-1])
                self.indi[self.num] = Indi(num = self.num)
                self.__get_indi()
            elif self.tag == 'FAM':
                self.num = int(self.pointer[2:len(self.pointer)-1])
                self.fam[self.num] = Fam(num = self.num)
                self.__get_fam()
            else:
                continue

    def __get_line(self):
        # if the flag is set, skip reading a newline
        if self.flag:
            self.flag = False
            return True
        words = self.f.readline().split()

        if not words:
            return False
        self.level = int(words[0])
        if words[1][0] == '@':
            self.pointer = words[1]
            self.tag = words[2]
            self.data = None
        else:
            self.pointer = None
            self.tag = words[1]
            self.data = ' '.join(words[2:])
        return True

    def __get_indi(self):
        while self.f and self.__get_line() and self.level > 0:
            if self.tag == 'NAME':
                name = self.data.split('/')
                self.indi[self.num].given = name[0].strip()
                self.indi[self.num].surname = name[1].strip()
            elif self.tag == 'SEX':
                self.indi[self.num].gender = self.data
            elif self.tag == 'BIRT':
                self.__get_birt()
            elif self.tag == 'CHR':
                self.__get_chr()
            elif self.tag == 'DEAT':
                self.__get_deat()
            elif self.tag == 'BURI':
                self.__get_buri()
            elif self.tag == 'FAMS':
                self.indi[self.num].fams_num.add(int(self.data[2:len(self.data)-1]))
            elif self.tag == 'FAMC':
                self.indi[self.num].famc_num.add(int(self.data[2:len(self.data)-1]))
            elif self.tag == '_FSFTID':
                self.indi[self.num].fid = self.data
        self.flag = True

    def __get_fam(self):
        while self.__get_line() and self.level > 0:
            if self.tag == 'HUSB':
                self.fam[self.num].husb_num = int(self.data[2:len(self.data)-1])
            elif self.tag == 'WIFE':
                self.fam[self.num].wife_num = int(self.data[2:len(self.data)-1])
            elif self.tag == 'CHIL':
                self.fam[self.num].chil_num.add(int(self.data[2:len(self.data)-1]))
            elif self.tag == 'MARR':
                self.__get_marr()
            elif self.tag == '_FSFTID':
                self.fam[self.num].fid = self.data
        self.flag = True

    def __get_birt(self):
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                self.indi[self.num].birtdate = self.data
            elif self.tag == 'PLAC':
                self.indi[self.num].birtplac = self.data
        self.flag = True

    def __get_chr(self):
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                self.indi[self.num].chrdate = self.data
            elif self.tag == 'PLAC':
                self.indi[self.num].chrplac = self.data
        self.flag = True

    def __get_deat(self):
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                self.indi[self.num].deatdate = self.data
            elif self.tag == 'PLAC':
                self.indi[self.num].deatplac = self.data
        self.flag = True

    def __get_buri(self):
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                self.indi[self.num].buridate = self.data
            elif self.tag == 'PLAC':
                self.indi[self.num].buriplac = self.data
        self.flag = True

    def __get_marr(self):
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                self.fam[self.num].marrdate = self.data
            elif self.tag == 'PLAC':
                self.fam[self.num].marrplac = self.data
        self.flag = True

    def __add_id(self):
        for num in self.fam:
            if self.fam[num].husb_num:
                self.fam[num].husb_fid = self.indi[self.fam[num].husb_num].fid
            if self.fam[num].wife_num:
                self.fam[num].wife_fid = self.indi[self.fam[num].wife_num].fid
            for chil in self.fam[num].chil_num:
                self.fam[num].chil_fid.add(self.indi[chil].fid)
        for num in self.indi:
            for famc in self.indi[num].famc_num:
                self.indi[num].famc_fid.add((self.fam[famc].husb_fid,self.fam[famc].wife_fid))
            for fams in self.indi[num].fams_num:
                self.indi[num].fams_fid.add((self.fam[fams].husb_fid,self.fam[fams].wife_fid))
            
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge GEDCOM data from FamilySearch Tree (22 Feb 2015)', add_help=False, usage='mergemyancestors.py -i input1.ged input2.ged ... [options]')
    try:
        parser.add_argument('-i', metavar = 'FILE', nargs = '+', type = argparse.FileType('r', encoding='UTF-8'), default = sys.stdin, help = 'input GEDCOM files [stdin]')
        parser.add_argument('-o', metavar = 'FILE', nargs = '?', type = argparse.FileType('w', encoding='UTF-8'), default = sys.stdout, help = 'output GEDCOM files [stdout]')
    except TypeError:
        sys.stderr.write('Python >= 3.4 is required to run this script\n')
        sys.stderr.write('(see https://docs.python.org/3/whatsnew/3.4.html#argparse)\n')
        exit(2)

    # extract arguments from the command line
    try:
        parser.error = parser.exit
        args = parser.parse_args()
    except SystemExit:
        parser.print_help()
        exit(2)

    tree = Tree()

    indi_counter = 0
    fam_counter = 0

    # read the GEDCOM data
    for file in args.i:
        ged = Gedcom(file)

        # add informations about individuals
        for num in ged.indi:
            fid = ged.indi[num].fid
            if fid not in tree.indi:
                indi_counter += 1
                tree.indi[fid] = Indi(num = indi_counter)
                tree.indi[fid].fid = ged.indi[num].fid
            tree.indi[fid].fams_fid |= ged.indi[num].fams_fid
            tree.indi[fid].famc_fid |= ged.indi[num].famc_fid
            tree.indi[fid].given = ged.indi[num].given
            tree.indi[fid].surname = ged.indi[num].surname
            tree.indi[fid].gender = ged.indi[num].gender
            tree.indi[fid].birtdate = ged.indi[num].birtdate
            tree.indi[fid].birtplac = ged.indi[num].birtplac
            tree.indi[fid].chrdate = ged.indi[num].chrdate
            tree.indi[fid].chrplac = ged.indi[num].chrplac
            tree.indi[fid].deatdate = ged.indi[num].deatdate
            tree.indi[fid].deatplac = ged.indi[num].deatplac
            tree.indi[fid].buridate = ged.indi[num].buridate
            tree.indi[fid].buriplac = ged.indi[num].buriplac

        # add informations about families
        for num in ged.fam:
            husb, wife = (ged.fam[num].husb_fid, ged.fam[num].wife_fid)
            if (husb, wife) not in tree.fam:
                fam_counter += 1
                tree.fam[(husb, wife)] = Fam(husb, wife, fam_counter)
            tree.fam[(husb, wife)].chil_fid |= ged.fam[num].chil_fid
            tree.fam[(husb, wife)].fid = ged.fam[num].fid
            tree.fam[(husb, wife)].marrdate = ged.fam[num].marrdate
            tree.fam[(husb, wife)].marrplac = ged.fam[num].marrplac

    # compute number for family relationships and print GEDCOM file
    tree.reset_num()
    tree.print(args.o)
