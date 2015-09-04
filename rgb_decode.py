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
                     help="input sensor image file to decode (PGM)")
   parser.add_argument("-o", "--output", required=True,
                     help="output color image file (PPM)")
   parser.add_argument("-d", "--display", action="store_true", default=False,
                     help="display decoded image")
   args = parser.parse_args()

   # obtain required parameters from RAW file
   tiff = jbtiff.tiff_file(open(args.raw, 'r'))
   width,height = tiff.get_image_size(3)
   border = tiff.get_border()
   model = tiff.get_model(0)

   # load sensor image
   I = jbtiff.pnm_file.read(open(args.input,'r'))
   assert len(I.shape) == 2 # must be a one-channel image
   assert I.shape == (height,width) # image size must be exact

   # get necessary transformation data
   t_black, t_maximum, rgb_cam = jbtiff.tiff_file.color_table[model]
   # extract references to color channels)
   R  = I[0::2,0::2] # Red
   G1 = I[0::2,1::2] # Green 1
   G2 = I[1::2,0::2] # Green 2
   B  = I[1::2,1::2] # Blue
   # determine black levels for each channel
   Rb = np.median(R[:,0:4])
   G1b = np.median(G1[:,0:4])
   G2b = np.median(G2[:,0:4])
   Bb = np.median(B[:,0:4])
   # subtract black level and scale each channel to [0.0,1.0]
   print "Scaling with black levels (%d,%d,%d,%d), saturation %d" % (Rb,G1b,G2b,Bb,t_maximum)
   R  = (R  - Rb)/float(t_maximum - Rb)
   G1 = (G1 - G1b)/float(t_maximum - G1b)
   G2 = (G2 - G2b)/float(t_maximum - G2b)
   B  = (B  - Bb)/float(t_maximum - Bb)
   # copy color channels and interpolate missing data (nearest neighbour)
   I = np.zeros((height, width, 3))
   for i in [0,1]:
      for j in [0,1]:
         I[i::2,j::2,0] = R # Red
   for i in [0,1]:
      I[i::2,1::2,1] = G1 # Green 1
      I[i::2,0::2,1] = G2 # Green 2
   for i in [0,1]:
      for j in [0,1]:
         I[i::2,j::2,2] = B # Blue
   # convert from camera color space to linear RGB D65 space
   I = np.dot(I, rgb_cam.transpose())
   # limit values
   np.clip(I, 0.0, 1.0, I)
   # apply sRGB gamma correction
   I = jbtiff.tiff_file.srgb_gamma(I)
   # cut border
   x1,y1,x2,y2 = border
   I = I[y1:y2+1,x1:x2+1]
   # scale to 16-bit
   I *= (1<<16)-1

   # save result
   jbtiff.pnm_file.write(I.astype('>H'), open(args.output,'w'))

   # show user what we've done, as needed
   if args.display:
      # linear display
      plt.figure()
      plt.imshow(I)
      plt.title('%s' % args.input)
      # show everything
      plt.show()
   return

# main entry point
if __name__ == '__main__':
   main()
