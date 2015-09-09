#!/usr/bin/python
# coding=utf8
#
# Copyright (c) 2015 Johann A. Briffa
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import sys
import os
import argparse
import jbtiff

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
   tiff = jbtiff.tiff_file(open(args.input, 'r'))
   # replace data strips where file exists
   for k, (IFD, ifd_offset, strips) in enumerate(tiff.data):
      # construct data filename and check it exists
      filename = '%s-%d.dat' % (args.basename, k)
      if not os.path.isfile(filename):
         continue
      # read input data file
      with open(filename, 'r') as fid:
         data = fid.read()
      print "IFD#%d: Replacing data strip with length %d" % (k, len(data))
      # replace data strips with new data
      assert strips
      del strips[:]
      strips.append(data)
      # update IFD data
      if 273 in IFD:
         assert 279 in IFD
         assert 513 not in IFD and 514 not in IFD
         IFD[279] = (4, 1, [len(data)], 0)
         continue
      if 513 in IFD:
         assert 514 in IFD
         assert 273 not in IFD and 279 not in IFD
         IFD[514] = (4, 1, [len(data)], 0)
         continue
      raise AssertionError("Reference to data strip not found in IFD#%d" % k)
   # save updated CR2 file
   tiff.write(open(args.output,'w'))
   return

# main entry point
if __name__ == '__main__':
   main()
