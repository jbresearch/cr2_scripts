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
import jbimage

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-r", "--raw", required=True,
                     help="input RAW file for image parameters")
   parser.add_argument("-i", "--input", required=True,
                     help="input sensor image file to decode (PGM)")
   parser.add_argument("-o", "--output", required=True,
                     help="output color image file (PPM)")
   parser.add_argument("-S", "--saturation", type=int,
                     help="saturation level (overriding camera default)")
   parser.add_argument("-b", "--bayer", default="RGGB",
                     help="Bayer pattern (first letter pair for odd rows, second pair for even rows)")
   parser.add_argument("-C", "--camera",
                     help="camera identifier string for color table lookup")
   parser.add_argument("-d", "--display", action="store_true", default=False,
                     help="display decoded image")
   args = parser.parse_args()

   # obtain required parameters from RAW file
   tiff = jbtiff.tiff_file(open(args.raw, 'rb'))
   width,height = tiff.get_sensor_size()
   border = tiff.get_border()
   if args.camera:
      model = args.camera
   else:
      model = tiff.get_model(0)

   # load sensor image
   I = jbimage.pnm_file.read(open(args.input,'rb'))
   assert len(I.shape) == 2 # must be a one-channel image
   assert I.shape == (height,width) # image size must be exact

   # get necessary transformation data
   t_black, t_maximum, cam_rgb = jbtiff.tiff_file.color_table[model]
   # extract references to color channels
   # c0 c1 / c2 c3 = R G / G B on most Canon cameras
   c = []
   for i in [0,1]:
      for j in [0,1]:
         c.append(I[i::2,j::2])
   # determine black levels for each channel from first four columns
   bl = [np.median(c[i][:,0:4]) for i in range(4)]
   # determine if we need to increase the saturation level
   t_maximum_actual = max([c[i].max() for i in range(4)])
   if t_maximum_actual > t_maximum:
      print "WARNING: actual levels (%d) exceed saturation (%d)" % (t_maximum_actual, t_maximum)
   # subtract black level and scale each channel to [0.0,1.0]
   if args.saturation:
      t_maximum = args.saturation
   print "Scaling with black levels (%s), saturation %d" % (','.join("%d" % x for x in bl),t_maximum)
   for i in range(4):
      c[i]  = (c[i]  - bl[i])/float(t_maximum - bl[i])
   # determine nearest neighbour for each colour channel
   assert len(args.bayer) == 4
   nn = []
   for ch,color in enumerate("RGB"):
      ch_nn = np.zeros((2,2),dtype=int)
      ch_nn[:] = -1 # initialize
      if args.bayer.count(color) == 1: # there is only one instance
         ch_nn[:] = args.bayer.find(color)
      elif args.bayer.count(color) == 2: # there are two instances
         ch_nn[0,:] = args.bayer.find(color,0,2)
         ch_nn[1,:] = args.bayer.find(color,2,4)
      assert(ch_nn.min() >= 0)
      nn.append(ch_nn)
   # copy color channels and interpolate missing data (nearest neighbour)
   I = np.zeros((height, width, 3))
   for ch in range(3):
      for i in [0,1]:
         for j in [0,1]:
            I[i::2,j::2,ch] = c[nn[ch][i,j]]
   # convert from camera color space to linear RGB D65 space
   rgb_cam = np.linalg.pinv(cam_rgb)
   I = np.dot(I, rgb_cam.transpose())
   # limit values
   np.clip(I, 0.0, 1.0, I)
   # apply sRGB gamma correction
   I = jbtiff.tiff_file.srgb_gamma(I)
   # cut border
   x1,y1,x2,y2 = border
   I = I[y1:y2+1,x1:x2+1]
   # show colour image, as needed
   if args.display:
      plt.figure()
      plt.imshow(I.astype('float'))
      plt.title('%s' % args.input)
   # scale to 16-bit
   I *= (1<<16)-1

   # save result
   jbimage.pnm_file.write(I.astype('>H'), open(args.output,'wb'))

   # show user what we've done, as needed
   if args.display:
      plt.show()
   return

# main entry point
if __name__ == '__main__':
   main()
