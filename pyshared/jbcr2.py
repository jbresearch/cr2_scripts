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

import os
import tempfile
import commands
import numpy as np

## replace data strips for specified IFD

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

## convert lossless JPEG encoded input file to raw data

def decode_lossless_jpeg(filename):
   # create folder for temporary files
   tmpfolder = tempfile.mkdtemp()

   # decode input file with Stanford PVRG software
   cmd = 'pvrg-jpeg -d -s "%s" -o "%s"' % (filename, os.path.join(tmpfolder, "parts"))
   st, out = commands.getstatusoutput(cmd)
   if st != 0:
      raise AssertionError('Error decoding JPEG file: %s' % out)

   # Laurent Clévy's example:
   # Image (w x h): 5184 x 3456
   # 4 color components (w x h): 0x538 x 0xdbc = 1336 x 3516 each
   #    interleaved components: 5344 x 3516
   #    border: 160 x 60 on declared image size
   # 3 slices (w): 2x 0x6c0 + 0x760 = 2x 1728 + 1888 = 5344
   #    each slice takes: 432 pixels from each of 4 colors (first two)
   #                      472 pixels from each of 4 colors (last one)

   # interpret output to determine the number of color components and precision
   components = []
   for line in out.split('\n'):
      if line.startswith('>> '):
         record = line.split()
         f = record[4]
         w = int(record[6])
         h = int(record[8])
         components.append((f,w,h))
      elif line.startswith('Caution: precision type:'):
         record = line.split()
         print "RAW data precision: %d" % int(record[3])
   # number of color components
   n = len(components)
   # first assemble color components
   width = sum([w for f,w,h in components])
   height = components[0][2]
   assert all([h == height for f,w,h in components])
   a = np.zeros((height, width), dtype=np.dtype('>H'))
   for i, (f,w,h) in enumerate(components):
      # read raw data for this component
      b = np.fromfile(f, dtype=np.dtype('>H'))
      b.shape = (h,w)
      # insert into assembled color image
      a[:,i::n] = b
      # remove temporary file
      os.remove(f)

   # remove (empty) temporary folder
   os.rmdir(tmpfolder)

   return a, len(components)

## unslice sensor image

def unslice_image(a, width, height, slices):
   # make a list of the width of each slice
   slice_widths = [slices[1]] * slices[0] + [slices[2]]
   assert sum(slice_widths) == width
   # unslice image
   I = np.zeros((height, width), dtype=np.dtype('>H'))
   for i, sw in enumerate(slice_widths):
      col_s = sum(slice_widths[0:i])
      col_e = col_s + sw
      I[:,col_s:col_e] = a.flat[col_s*height:col_e*height].reshape(height,sw)
   return I

## slice sensor image

def slice_image(I, width, height, slices):
   # make a list of the width of each slice
   slice_widths = [slices[1]] * slices[0] + [slices[2]]
   assert sum(slice_widths) == width
   # slice image
   a = np.zeros((height, width), dtype=np.dtype('>H'))
   for i, sw in enumerate(slice_widths):
      col_s = sum(slice_widths[0:i])
      col_e = col_s + sw
      a.flat[col_s*height:col_e*height] = I[:,col_s:col_e].flat
   return a
