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
import jbtiff

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", required=True,
                     help="input JPEG lossless raw data file to decode")
   parser.add_argument("-o", "--output", required=True,
                     help="output decoded image file (use PNG extension)")
   parser.add_argument("-W", "--width", required=True, type=int,
                     help="sensor image width (from RAW IFD)")
   parser.add_argument("-H", "--height", required=True, type=int,
                     help="sensor image height (from RAW IFD)")
   parser.add_argument("-S", "--slice", required=True, type=int,
                     help="first sensor image slice width")
   parser.add_argument("-d", "--display", action="store_true", default=False,
                     help="display decoded image")
   args = parser.parse_args()

   # Laurent Clévy's example:
   # Image (w x h): 5184 x 3456
   # 4 color components (w x h): 0x538 x 0xdbc = 1336 x 3516 each
   #    interleaved components: 5344 x 3516
   #    border: 160 x 60 on declared image size
   # 3 slices (w): 2x 0x6c0 + 0x760 = 2x 1728 + 1888 = 5344
   #    each slice takes: 432 pixels from each of 4 colors (first two)
   #                      472 pixels from each of 4 colors (last one)

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
   # number of color components
   n = len(components)
   # first assemble color components
   assert all([h == args.height for f,w,h in components])
   assert sum([w for f,w,h in components]) == args.width
   a = np.zeros((args.height, args.width), dtype=np.dtype('>H'))
   for i, (f,w,h) in enumerate(components):
      # read raw data for this color component
      b = np.fromfile(f, dtype=np.dtype('>H'))
      b.shape = (h,w)
      # insert into assembled color image
      a[:,i::n] = b

   # determine the number of slices and the width of each slice
   slices = (args.width + args.slice - 1) // args.slice
   slice_widths = [args.slice] * (slices-1) + [args.width - args.slice*(slices-1)]
   # next unslice image
   I = np.zeros((args.height, args.width), dtype=np.dtype('>H'))
   for i, sw in enumerate(slice_widths):
      col_s = sum(slice_widths[0:i])
      col_e = col_s + sw
      I[:,col_s:col_e] = a.flat[col_s*args.height:col_e*args.height].reshape(args.height,sw)

   # save result
   jbtiff.pnm_file.write(I.astype('>H'), open(args.output,'w'))

   # show user what we've done, as needed
   if args.display:
      # linear display
      plt.figure()
      plt.imshow(I, cmap=plt.cm.gray)
      plt.title('%s' % args.input)
      # show everything
      plt.show()
   return

# main entry point
if __name__ == '__main__':
   main()
