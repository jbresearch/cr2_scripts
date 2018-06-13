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

import sys
import os
import argparse

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'pyshared'))
import jbtiff
import jbcr2

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", required=True,
                     help="input raw file to use as basis")
   parser.add_argument("-b", "--basename", required=True,
                     help="base filename for replacement components (appended with -x.dat for IFD# x)")
   parser.add_argument("-o", "--output", required=True,
                     help="output CR2 file")
   args = parser.parse_args()

   # read input raw file
   tiff = jbtiff.tiff_file(open(args.input, 'rb'))
   # replace data strips where file exists
   for k in range(len(tiff.data)):
      # construct data filename and check it exists
      filename = '%s-%d.dat' % (args.basename, k)
      if not os.path.isfile(filename):
         continue
      # read input data file
      with open(filename, 'rb') as fid:
         data = fid.read()
      # replace data strips with new data
      jbcr2.replace_ifd(tiff, k, data)
   # save updated CR2 file
   tiff.write(open(args.output,'wb'))
   return

# main entry point
if __name__ == '__main__':
   main()
