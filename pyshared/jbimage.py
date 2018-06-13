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
