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
   parser.add_argument("-r", "--raw", required=True,
                     help="input RAW file for image parameters")
   parser.add_argument("-i", "--input", required=True,
                     help="input JPEG lossless raw data file to decode")
   parser.add_argument("-o", "--output", required=True,
                     help="output decoded image file (PGM)")
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

   # obtain required parameters from RAW file
   tiff = jbtiff.tiff_file(open(args.raw, 'r'))
   width,height = tiff.get_image_size(3)
   slices = tiff.get_slices(3)

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
   assert all([h == height for f,w,h in components])
   assert sum([w for f,w,h in components]) == width
   a = np.zeros((height, width), dtype=np.dtype('>H'))
   for i, (f,w,h) in enumerate(components):
      # read raw data for this color component
      b = np.fromfile(f, dtype=np.dtype('>H'))
      b.shape = (h,w)
      # insert into assembled color image
      a[:,i::n] = b

   # make a list of the width of each slice
   slice_widths = [slices[1]] * slices[0] + [slices[2]]
   assert sum(slice_widths) == width
   # next unslice image
   I = np.zeros((height, width), dtype=np.dtype('>H'))
   for i, sw in enumerate(slice_widths):
      col_s = sum(slice_widths[0:i])
      col_e = col_s + sw
      I[:,col_s:col_e] = a.flat[col_s*height:col_e*height].reshape(height,sw)

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
