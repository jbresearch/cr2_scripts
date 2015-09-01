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
import argparse
import jbtiff

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", required=True,
                     help="input raw file to use as basis")
   parser.add_argument("-j", "--jpeg", required=True,
                     help="input lossles jpeg file with replacement sensor data")
   parser.add_argument("-o", "--output", required=True,
                     help="output CR2 file")
   args = parser.parse_args()

   # read input raw file
   tiff = jbtiff.tiff_file(open(args.input, 'r'))
   # read input lossless jpeg file
   with open(args.jpeg, 'r') as fid:
      jpeg = fid.read()
   # replace lossless jpeg data strip
   assert tiff.cr2
   for k, (IFD, ifd_offset, strips) in enumerate(tiff.data):
      # find IFD with raw sensor data
      if not tiff.cr2_ifd_offset == ifd_offset:
         continue
      # replace data strips with new lossless jpeg data
      assert strips
      assert 273 in IFD
      assert 279 in IFD
      # replace strip
      del strips[:]
      strips.append(jpeg)
      # update IFD data
      IFD[279] = (4, 1, [len(jpeg)], 0)
   # save updated CR2 file
   tiff.write(open(args.output,'w'))
   return

# main entry point
if __name__ == '__main__':
   main()
