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
import commands
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
                     help="input sensor image file to encode")
   parser.add_argument("-o", "--output", required=True,
                     help="output JPEG lossless raw data file")
   parser.add_argument("-C", "--components", required=True, type=int,
                     help="number of color components to create")
   parser.add_argument("-P", "--precision", required=True, type=int,
                     help="number of bits per sensor pixel")
   parser.add_argument("-d", "--display", action="store_true", default=False,
                     help="display encoded images")
   args = parser.parse_args()

   # See raw_decode.py for color components & slicing example

   # read input raw file
   tiff = jbtiff.tiff_file(open(args.raw, 'rb'))
   # load sensor image
   I = jbtiff.pnm_file.read(open(args.input,'rb'))

   # obtain required parameters from RAW file
   width,height = tiff.get_sensor_size()
   slices = tiff.get_slices()
   # check input image parameters
   assert len(sensor.shape) == 2 # must be a one-channel image
   assert sensor.shape == (height,width) # image size must be exact

   # slice image
   a = jbcr2.slice_image(sensor, width, height, slices)
   # encode to lossless JPEG output file
   parts = jbcr2.encode_lossless_jpeg(a, args.components, args.precision, args.output)

   # show user what we've done, as needed
   if args.display:
      for i, b in enumerate(parts):
         plt.figure()
         plt.imshow(b, cmap=plt.cm.gray)
         plt.title('Part %d' % i)
      plt.show()
   return

# main entry point
if __name__ == '__main__':
   main()
