#!/usr/bin/env python3
"""
   getmyancestors.py - Retrieve GEDCOM data from FamilySearch Tree
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
import sys, argparse, time

try:
    import requests
except ImportError:
    sys.stderr.write('You need to install the requests module first\n')
    sys.stderr.write('(run this in your terminal: "pip install requests" or "pip install --user requests")\n')
    exit(2)

global fs # FamilySearch session
global tree # family tree

class Fs:

    # login (https://familysearch.org/developers/docs/guides/oauth1/login)
    # retrieve a FamilySearch session ID
    def __init__(self, key, username, password, logfile, verbose):
        url = 'https://api.familysearch.org/identity/v2/login'
        values = {'key' : key,
                  'username' : username,
                  'password' : password}
        r = requests.post(url, values)
        self.fssessionid = r.cookies['fssessionid'] # FamilySearch session ID
        self.logfile = logfile # file with logging information
        self.verbose = verbose # verbose output flag
    
    # retrieve JSON structure from URL
    def get_url(self, url):
        while True:
            try:
                if self.verbose:
                    self.logfile.write('Downloading: ' + url + '\n')
                r = requests.get(url, cookies = { 'fssessionid' : self.fssessionid })
                if self.verbose:
                    self.logfile.write('Status code: ' + str(r.status_code) + '\n')
                if r.status_code == 204:
                    return None
                elif r.status_code == 500 or r.status_code == 502:
                    time.sleep(1)
                    continue
                else:
                    return r.json()
            except requests.exceptions.ConnectionError as e:
                error_msg = e.args[0].reason.strerror
                self.logfile.write('requests.exceptions.ConnectionError: ' + error_msg + '\n')
                time.sleep(1)
            except:
                self.logfile.write('Unexpected error\n')
                time.sleep(1)
    
    # return the FamilySearch ID of the current user
    def get_userid(self):
        url = 'https://familysearch.org/platform/users/current.json'
        data = self.get_url(url)
        return data['users'][0]['personId'] if data else None



# GEDCOM individual class
class Indi:

    counter = 0

    # initialize individual
    def __init__(self, fid = None, num = None, ascnum = None, desnum = None):
        if num:
            self.num = num
        else:
            Indi.counter += 1
            self.num = Indi.counter
        self.fid = fid
        self.famc_fid = set()
        self.fams_fid = set()
        self.famc_num = set()
        self.fams_num = set()
        self.ascnum = ascnum
        self.desnum = desnum
        self.given = ''
        self.surname = 'Unknown'
        self.gender = self.birtdate = self.birtplac = self.deatdate = self.deatplac = None
        self.chrdate = self.chrplac = self.buridate = self.buriplac = None
        if fid:
            url = 'https://familysearch.org/platform/tree/persons/' + self.fid + '.json'
            data = fs.get_url(url)
            if data:
                x = data['persons'][0]
                if x['names']:
                    for y in x['names'][0]['nameForms'][0]['parts']:
                        if y['type'] == u'http://gedcomx.org/Given':
                            self.given = y['value']
                        if y['type'] == u'http://gedcomx.org/Surname':
                            self.surname = y['value']
                if 'gender' in x:
                    if x['gender']['type'] == "http://gedcomx.org/Male":
                        self.gender = "M"
                    elif x['gender']['type'] == "http://gedcomx.org/Female":
                        self.gender = "F"
                else:
                    self.gender = None
                for y in x['facts']:
                    if y['type'] == u'http://gedcomx.org/Birth':
                        self.birtdate = y['date']['original'] if 'date' in y else None
                        self.birtplac = y['place']['original'] if 'place' in y else None
                    if y['type'] == u'http://gedcomx.org/Christening':
                        self.chrdate = y['date']['original'] if 'date' in y else None
                        self.chrplac = y['place']['original'] if 'place' in y else None
                    if y['type'] == u'http://gedcomx.org/Death':
                        self.deatdate = y['date']['original'] if 'date' in y else None
                        self.deatplac = y['place']['original'] if 'place' in y else None
                    if y['type'] == u'http://gedcomx.org/Burial':
                        self.buridate = y['date']['original'] if 'date' in y else None
                        self.buriplac = y['place']['original'] if 'place' in y else None
        self.parents = None
        self.children = None
        self.spouses = None

    # retrieve parents
    def get_parents(self):
        if not self.parents:
            url = 'https://familysearch.org/platform/tree/persons/' + self.fid + '/parents.json'
            data = fs.get_url(url)
            if data:
                x = data['childAndParentsRelationships'][0]
                self.parents = (x['father']['resourceId'] if 'father' in x else None,
                                x['mother']['resourceId'] if 'mother' in x else None)
            else:
                self.parents = (None, None)
            return self.parents

    # retrieve children relationships
    def get_children(self):
        if not self.children:
            url = 'https://familysearch.org/platform/tree/persons/' + self.fid + '/children.json'
            data = fs.get_url(url)
            if data:
                self.children = [(x['father']['resourceId'] if 'father' in x else None,
                                  x['mother']['resourceId'] if 'mother' in x else None,
                                  x['child']['resourceId']) for x in data['childAndParentsRelationships']]
        return self.children

    # retrieve spouse relationships
    def get_spouses(self):
        if not self.spouses:
            url = 'https://familysearch.org/platform/tree/persons/' + self.fid + '/spouses.json'
            data = fs.get_url(url)
            if data and 'relationships' in data:
                self.spouses = [(x['person1']['resourceId'],x['person2']['resourceId'],x['id']) for x in data['relationships']]
        return self.spouses

    # print individual information in GEDCOM format
    def print(self, file = sys.stdout):
        file.write('0 @I' + str(self.num) + '@ INDI\n')
        file.write('1 NAME ' + self.given + ' /' + self.surname + '/\n')
        if self.gender:
            file.write('1 SEX ' + self.gender + '\n')
        if self.birtdate or self.birtplac:
            file.write('1 BIRT\n')
            if self.birtdate:
                file.write('2 DATE ' + self.birtdate + '\n')
            if self.birtplac:
                file.write('2 PLAC ' + self.birtplac + '\n')
        if self.chrdate or self.chrplac:
            file.write('1 CHR\n')
            if self.chrdate:
                file.write('2 DATE ' + self.chrdate + '\n')
            if self.chrplac:
                file.write('2 PLAC ' + self.chrplac + '\n')
        if self.deatdate or self.deatplac:
            file.write('1 DEAT\n')
            if self.deatdate:
                file.write('2 DATE ' + self.deatdate + '\n')
            if self.deatplac:
                file.write('2 PLAC ' + self.deatplac + '\n')
        if self.buridate or self.buriplac:
            file.write('1 BURI\n')
            if self.buridate:
                file.write('2 DATE ' + self.buridate + '\n')
            if self.buriplac:
                file.write('2 PLAC ' + self.buriplac + '\n')
        for num in self.fams_num:
            file.write('1 FAMS @F' + str(num) + '@\n')
        for num in self.famc_num:
            file.write('1 FAMC @F' + str(num) + '@\n')
        file.write('1 _FSFTID ' + self.fid + '\n')



# GEDCOM family class
class Fam:

    counter = 0

    # initialize family
    def __init__(self, husb = None, wife = None, num = None, chil = None, fid = None):
        if num:
            self.num = num
        else:
            Fam.counter += 1
            self.num = Fam.counter
        self.husb_fid = husb if husb else None
        self.wife_fid = wife if wife else None
        self.chil_fid = {chil} if chil else set()
        self.husb_num = self.wife_num = self.fid = self.marrdate = self.marrplac = None
        self.chil_num = set()
        if fid:
            self.get_marriage(fid)

    # retrieve marriage information
    def get_marriage(self,fid):
        self.fid = fid
        url = 'https://familysearch.org/platform/tree/couple-relationships/' + self.fid + '.json'
        data = fs.get_url(url)
        if data and 'facts' in data['relationships'][0]:
            x = data['relationships'][0]['facts'][0]
            self.marrdate = x['date']['original'] if 'date' in x else None
            self.marrplac = x['place']['original'] if 'place' in x else None
        else:
            self.marrdate = self.marrplac = None

    # print family information in GEDCOM format
    def print(self, file = sys.stdout):
        file.write('0 @F' + str(self.num) + '@ FAM\n')
        if self.husb_num:
            file.write('1 HUSB @I' + str(self.husb_num) + '@\n')
        if self.wife_num:
            file.write('1 WIFE @I' + str(self.wife_num) + '@\n')
        for num in self.chil_num:
            file.write('1 CHIL @I' + str(num) + '@\n')
        if self.marrdate or self.marrplac:
            file.write('1 MARR\n')
            if self.marrdate:
                file.write('2 DATE ' + self.marrdate + '\n')
            if self.marrplac:
                file.write('2 PLAC ' + self.marrplac + '\n')
        if self.fid:
            file.write('1 _FSFTID ' + self.fid + '\n')



# family tree class
class Tree:

    def __init__(self):
        self.indi = dict()
        self.fam = dict()

    def reset_num(self):
        for husb, wife in self.fam:
            self.fam[(husb, wife)].husb_num = self.indi[husb].num if husb else None
            self.fam[(husb, wife)].wife_num = self.indi[wife].num if wife else None
            self.fam[(husb, wife)].chil_num = set([self.indi[chil].num for chil in self.fam[(husb, wife)].chil_fid])
        for fid in self.indi:
            self.indi[fid].famc_num = set([self.fam[(husb, wife)].num for husb, wife in self.indi[fid].famc_fid])
            self.indi[fid].fams_num = set([self.fam[(husb, wife)].num for husb, wife in self.indi[fid].fams_fid])

    # print GEDCOM file
    def print(self, file = sys.stdout):
        file.write('0 HEAD\n')
        file.write('1 CHAR UTF-8\n')
        file.write('1 GEDC\n')
        file.write('2 VERS 5.5\n')
        file.write('2 FORM LINEAGE-LINKED\n')
        for fid in sorted(self.indi, key = lambda x: self.indi.__getitem__(x).num):
            self.indi[fid].print(file)
        for husb, wife in sorted(self.fam, key = lambda x: self.fam.__getitem__(x).num):
            self.fam[(husb,wife)].print(file)
        file.write('0 TRLR\n')



def process_trio(father,mother,child):
    if not (father,mother) in tree.fam:
        tree.fam[(father,mother)] = Fam(father,mother,chil=child)
    if father and not father in tree.indi:
        tree.indi[father] = Indi(father)
    if mother and not mother in tree.indi:
        tree.indi[mother] = Indi(mother)
    if not child in tree.indi:
        tree.indi[child] = Indi(child)
    if not child in tree.fam[(father,mother)].chil_fid:
        tree.fam[(father,mother)].chil_fid.add(child)
    if father and not (father,mother) in tree.indi[father].fams_fid:
        tree.indi[father].fams_fid.add((father,mother))
    if mother and not (father,mother) in tree.indi[mother].fams_fid:
        tree.indi[mother].fams_fid.add((father,mother))
    if not (father,mother) in tree.indi[child].famc_fid:
        tree.indi[child].famc_fid.add((father,mother))

def process_duo(father,mother,fid):
    if not (father,mother) in tree.fam:
        tree.fam[(father,mother)] = Fam(father,mother,fid=fid)
    if not father in tree.indi:
        tree.indi[father] = Indi(father)
    if not mother in tree.indi:
        tree.indi[mother] = Indi(mother)
    if father and not (father,mother) in tree.indi[father].fams_fid:
        tree.indi[father].fams_fid.add((father,mother))
    if mother and not (father,mother) in tree.indi[mother].fams_fid:
        tree.indi[mother].fams_fid.add((father,mother))
    if not tree.fam[(father,mother)].fid:
        tree.fam[(father,mother)].get_marriage(fid)

# get all spouses and children of a given person
def get_family(fid):
    children = []

    # when you get spouses, populate the FAM database
    rels = tree.indi[fid].get_spouses()
    if rels:
        for father, mother, relfid in rels:
            process_duo(father,mother,relfid)

    # when you get children, populate the FAM database
    rels = tree.indi[fid].get_children()
    if rels:
        for father, mother, child in rels:
            process_trio(father,mother,child)
            children.append(child)

    return children

# to get the developer key: wget -O- https://familysearch.org/auth/familysearch 2>&1 | grep client_id

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Retrieve GEDCOM data from FamilySearch Tree (22 Feb 2015)', add_help = False, usage = 'getmyancestors.py -u username -p password [options]')
    parser.add_argument('-u', metavar = 'STR', required = True, type = str, help = 'FamilySearch username')
    parser.add_argument('-p', metavar = 'STR', required = True, type = str, help = 'FamilySearch password')
    parser.add_argument('-k', metavar = 'STR', nargs='?', type = str, default = '3Z3L-Z4GK-J7ZS-YT3Z-Q4KY-YN66-ZX5K-176R', help = 'FamilySearch developer key [3Z3L-Z4GK-J7ZS-YT3Z-Q4KY-YN66-ZX5K-176R]')
    parser.add_argument('-i', metavar = 'STR', nargs='?', type = str, help = 'Comma separated (no spaces) list of individual FamilySearch IDs for whom to retrieve ancestors')
    parser.add_argument('-a', metavar = 'INT', nargs='?', type = int, default = 4, help = 'Number of generations to ascend')
    parser.add_argument('-d', metavar = 'INT', nargs='?', type = int, default = 1, help = 'Number of generations to descend')
    try:
        parser.add_argument('-o', metavar = 'FILE', nargs='?', type = argparse.FileType('w', encoding = 'UTF-8'), default = sys.stdout, help = 'output GEDCOM file [stdout]')
        parser.add_argument('-l', metavar = 'FILE', nargs='?', type = argparse.FileType('w', encoding = 'UTF-8'), default = sys.stderr, help = 'output log file [stderr]')
    except TypeError:
        sys.stderr.write('Python >= 3.4 is required to run this script\n')
        sys.stderr.write('(see https://docs.python.org/3/whatsnew/3.4.html#argparse)\n')
        exit(2)
    parser.add_argument("-v", action = "store_true", default = False, help = "increase output verbosity")
    
    # extract arguments from the command line
    try:
        parser.error = parser.exit
        args = parser.parse_args()
    except SystemExit:
        parser.print_help()
        exit(2)
    
    # initialize a FamilySearch session
    fs = Fs(args.k, args.u, args.p, args.l, args.v)

    tree = Tree()    
    
    # create list of ascendancy individuals
    asc = list()
    asc.append(set())
    for i in range(args.a):
        asc.append(set())
    
    # create list of descendancy individuals
    des = list()
    des.append(set())
    for i in range(args.d):
        des.append(set())
    
    # populate set of individuals to retrieve
    for fid in (args.i.split(",") if args.i else [fs.get_userid()]):
        tree.indi[fid] = Indi(fid)
        tree.indi[fid].ascnum = 0
        asc[0].add(fid)
        tree.indi[fid].desnum = 0
        des[0].add(fid)
    
    # recursively download all ancestors
    for ascnum in range(args.a):
        while asc[ascnum]:
            # select an individual to process
            fid = asc[ascnum].pop()
    
            # collect the indiviuals parents and populate the FAM and INDI database
            father, mother = tree.indi[fid].get_parents()
            if father or mother:
                process_trio(father,mother,fid)
                for fid in filter(None,(father,mother)):
                    if not tree.indi[fid].ascnum or tree.indi[fid].ascnum > ascnum:
                        asc[ascnum+1].add(fid)
                        tree.indi[fid].ascnum = ascnum + 1
                    for child in get_family(fid):
                        if not tree.indi[child].ascnum:
                            tree.indi[child].desnum = 0
                            des[0].add(child)
    
    # recursively download all descendants
    for desnum in range(args.d):
        while des[desnum]:
            # select an individual to process
            fid = des[desnum].pop()
    
            for child in get_family(fid):
                if not tree.indi[child].desnum or tree.indi[child].desnum > desnum:
                    des[desnum+1].add(child)
                    tree.indi[child].desnum = desnum + 1
                    # when you get spouses, populate the FAM database
                    rels = tree.indi[child].get_spouses()
                    if rels:
                        for father, mother, fidrel in rels:
                            process_duo(father,mother,fidrel)

    # compute number for family relationships and print GEDCOM file
    tree.reset_num()
    tree.print(args.o)
