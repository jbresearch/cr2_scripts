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

import argparse
import commands
import numpy as np
import matplotlib.pyplot as plt

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", required=True,
                     help="input JPEG lossless raw data file to process")
   parser.add_argument("-o", "--output", required=True,
                     help="output processed image file")
   parser.add_argument("-W", "--width", required=True, type=int,
                     help="image width")
   parser.add_argument("-H", "--height", required=True, type=int,
                     help="image height")
   parser.add_argument("-S", "--slice", required=True, type=int,
                     help="image slice width")
   args = parser.parse_args()

   # determine the number of slices and the width of each slice
   slices = (args.width + args.slice - 1) // args.slice
   slice_widths = [args.slice] * (slices-1) + [args.width - args.slice*(slices-1)]
   # convert lossless JPEG encoded input file to raw data
   cmd = 'pvrg-jpeg -d -s "%s" -o parts' % args.input
   st, out = commands.getstatusoutput(cmd)
   if st != 0:
      raise AssertionError('Error decoding JPEG file: %s' % out)
   # interpret output to determine color components
   components = []
   for line in out.split('\n'):
      if line.startswith('>> '):
         record = line.split()
         f = record[4]
         w = int(record[6])
         h = int(record[8])
         components.append((f,w,h))
   # assemble raw sensor image from color components
   I = np.zeros((args.height, args.width), dtype=np.dtype('>H'))
   for i, (f,w,h) in enumerate(components):
      a = np.fromfile(f, dtype=np.dtype('>H'))
      a.shape = (h,w)
      if len(components) == 2:
         assert h == args.height
         I[:,i::2] = a
      elif len(components) == 4:
         assert h == args.height/2
         I[:,i::2] = a
      else:
         raise AssertionError('Unsupported number of color components: %d' % len(components))
   # show user what we've done
   plt.imshow(I, cmap=plt.cm.gray)
   plt.show()
   return

# main entry point
if __name__ == '__main__':
   main()
