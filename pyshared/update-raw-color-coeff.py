#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2015-2018 Johann A. Briffa
#
# This file is part of CR2_Scripts.
#
# CR2_Scripts is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CR2_Scripts is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CR2_Scripts.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import shlex
import re

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", required=True,
                     help="input dcraw.c source file to parse")
   parser.add_argument("-o", "--output", required=True,
                     help="output raw-color-coeff.txt file")
   args = parser.parse_args()

   # read dcraw source file
   with open(args.input,'r') as fid:
      # extract colour coefficient table
      table = []
      state = 0
      for line in fid:
         # find start of class
         if state==0:
            if "void CLASS adobe_coeff" in line:
               state = 1
         # find start of table
         elif state==1:
            if "table[] =" in line:
               state = 2
         # read table contents, assuming two-line entries
         elif state==2:
            # end of table reached
            if "};" in line:
               break
            # first line
            entry = line
            state = 3
         elif state==3:
            # second line
            entry += line
            state = 2
            # remove C-style comments
            entry = re.sub('[{}]','',entry)
            # remove braces
            entry = re.sub('/\*.*\*/','',entry)
            # remove all whitespace except for quoted sequences
            entry = ''.join(shlex.split(entry))
            # remove final comma
            entry = entry.rstrip(',')
            # parse and add to table
            entry = entry.split(',')
            table.append(entry)

   # output table
   with open(args.output,'w') as fid:
      for record in table:
         print >> fid, '\t'.join(record)

   return

# main entry point
if __name__ == '__main__':
   main()
