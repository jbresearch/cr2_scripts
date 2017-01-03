#!/usr/bin/python
# coding=utf8
#
# Copyright © 2015-2017 Johann A. Briffa
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

import sys
import os
import argparse

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'pyshared'))
import jbtiff

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", required=True,
                     help="input raw file to read")
   parser.add_argument("-o", "--output",
                     help="output file basename for embedded data in IFDs")
   parser.add_argument("-d", "--display", action="store_true", default=False,
                     help="print read data")
   args = parser.parse_args()

   # read input file
   tiff = jbtiff.tiff_file(open(args.input, 'rb'))
   # print data as needed
   if args.display:
      tiff.display(sys.stdout)
   # save data strips as needed
   if args.output:
      tiff.save_data(args.output)
   return

# main entry point
if __name__ == '__main__':
   main()
