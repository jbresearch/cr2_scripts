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
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'pyshared'))
import jbtiff
import jbcr2

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-r", "--raw", required=True,
                     help="input RAW file for image parameters")
   parser.add_argument("-i", "--input", required=True,
                     help="input JPEG lossless raw data file to decode")
   parser.add_argument("-o", "--output", required=True,
                     help="output sensor image file (PGM)")
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

   # read input raw file
   tiff = jbtiff.tiff_file(open(args.raw, 'rb'))

   # convert lossless JPEG encoded input file to raw data
   a, components = jbcr2.decode_lossless_jpeg(args.input)
   # obtain required parameters from RAW file
   width,height = tiff.get_sensor_size()
   slices = tiff.get_slices()
   # next unslice image
   I = jbcr2.unslice(a, width, height, slices)

   # save result
   jbtiff.pnm_file.write(I.astype('>H'), open(args.output,'wb'))

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
