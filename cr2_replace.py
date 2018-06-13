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

## component functions

def replace_ifd(tiff, k, data):
   print "IFD#%d: Replacing data strip with length %d" % (k, len(data))
   # get references to required IFD
   IFD, ifd_offset, strips = tiff.data[k]
   # replace data strips with new data
   assert strips
   del strips[:]
   strips.append(data)
   # update IFD data
   if 273 in IFD:
      assert 279 in IFD
      assert 513 not in IFD and 514 not in IFD
      IFD[279] = (4, 1, [len(data)], 0)
   elif 513 in IFD:
      assert 514 in IFD
      assert 273 not in IFD and 279 not in IFD
      IFD[514] = (4, 1, [len(data)], 0)
   else:
      raise AssertionError("Reference to data strip not found in IFD#%d" % k)
   return

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", required=True,
                     help="input raw file to use as basis")
   parser.add_argument("-s", "--sensor", required=True,
                     help="sensor image file to replace input")
   parser.add_argument("-o", "--output", required=True,
                     help="output CR2 file")
   args = parser.parse_args()

   # read input raw file
   tiff = jbtiff.tiff_file(open(args.input, 'rb'))
   # read input data file
   with open(args.sensor, 'rb') as fid:
      data = fid.read()

   # replace data strips for main sensor image (IFD#3)
   replace_ifd(tiff, 3, data)

   # save updated CR2 file
   tiff.write(open(args.output,'wb'))
   return

# main entry point
if __name__ == '__main__':
   main()