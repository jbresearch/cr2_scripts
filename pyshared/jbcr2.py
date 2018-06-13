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
