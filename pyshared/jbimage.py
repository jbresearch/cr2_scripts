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

import numpy as np
from PIL import Image

class pnm_file():

   @staticmethod
   def read(fid):
      # read header (assume separate lines for id, size, and depth)
      tmp = fid.readline().strip()
      if tmp == "P5":
         ch = 1
      elif tmp == "P6":
         ch = 3
      else:
         raise ValueError("Cannot handle files of type %s" % tmp)
      tmp = fid.readline().strip().split()
      if len(tmp) == 2: # width,height in same line
         w = int(tmp[0])
         h = int(tmp[1])
      else: # width, height in separate lines
         assert len(tmp) == 1
         w = int(tmp[0])
         tmp = fid.readline().strip().split()
         assert len(tmp) == 1
         h = int(tmp[0])
      tmp = fid.readline().strip()
      if tmp == "255":
         dtype = np.dtype('uint8')
      elif tmp == "65535":
         dtype = np.dtype('>H')
      else:
         raise ValueError("Cannot handle files with %s colors" % tmp)
      # read pixels
      I = np.fromfile(fid, count=h*w*ch, dtype=dtype)
      I = I.reshape((h,w,ch)).squeeze()
      return I

   @staticmethod
   def write(image, fid):
      # determine dimensions, channels, and bit depth
      if len(image.shape) == 2:
         h,w = image.shape
         ch = 1
      elif len(image.shape) == 3:
         h,w,ch = image.shape
      else:
         raise ValueError("Cannot handle input arrays of size %s" % image.shape)
      if image.dtype == np.dtype('uint8'):
         depth = 8
      elif image.dtype == np.dtype('>H'):
         depth = 16
      else:
         raise ValueError("Cannot handle input arrays of type %s" % image.dtype)
      # write header
      if ch == 1:
         print >> fid, "P5"
      else:
         print >> fid, "P6"
      print >> fid, w, h
      print >> fid, (1<<depth)-1
      # write pixels
      image.tofile(fid)
      return

## class to read and write general image files (using PIL)

class image_file():

   @staticmethod
   def read(infile):
      im = Image.open(infile)
      ch = len(im.mode)
      (x,y) = im.size
      # Works with PIL 1.1.6 upwards
      # return array is read-only!
      assert list(map(int, Image.VERSION.split('.'))) >= [1,1,6]
      I = np.asarray(im).reshape(y,x,ch)
      return I

   @staticmethod
   def write(I,outfile):
      # Works with PIL 1.1.6 upwards
      assert list(map(int, Image.VERSION.split('.'))) >= [1,1,6]
      # convert to image of the correct type based on shape and dtype
      im = Image.fromarray(I.squeeze())
      # save to file
      im.save(outfile, optimize=True)
      return
