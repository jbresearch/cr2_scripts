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
import tempfile
import argparse

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'pyshared'))
import jbtiff
import jbcr2
import jbimage

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

   # extract existing sensor image
   IFD, ifd_offset, strips = tiff.data[3]
   # save into a temporary file
   fid, tmpfile = tempfile.mkstemp()
   for strip in strips:
      os.write(fid, strip)
   os.close(fid)
   # decode lossless JPEG encoded file to determine parameters
   a, components, precision = jbcr2.decode_lossless_jpeg(tmpfile)
   # delete temporary file
   os.remove(tmpfile)

   # read sensor image file
   sensor = jbimage.image_file.read(args.sensor).squeeze()

   # obtain required parameters from RAW file
   width,height = tiff.get_sensor_size()
   slices = tiff.get_slices()
   # check input image parameters
   assert len(sensor.shape) == 2 # must be a one-channel image
   assert sensor.shape == (height,width) # image size must be exact
   # slice image
   a = jbcr2.slice_image(sensor, width, height, slices)
   # encode to a temporary lossless JPEG output file
   fid, tmpfile = tempfile.mkstemp()
   os.close(fid)
   parts = jbcr2.encode_lossless_jpeg(a, components, precision, tmpfile)
   # read and delete temporary file
   with open(tmpfile, 'rb') as fid:
      data = fid.read()
   os.remove(tmpfile)

   # replace data strips for main sensor image (IFD#3)
   jbcr2.replace_ifd(tiff, 3, data)

   # save updated CR2 file
   tiff.write(open(args.output,'wb'))
   return

# main entry point
if __name__ == '__main__':
   main()
