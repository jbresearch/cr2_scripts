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
import Image
import jbtiff

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-i", "--input", required=True,
                     help="input JPEG lossless raw data file to decode")
   parser.add_argument("-o", "--output", required=True,
                     help="output decoded image file (use PNG extension)")
   parser.add_argument("-W", "--width", required=True, type=int,
                     help="sensor image width (from RAW IFD)")
   parser.add_argument("-H", "--height", required=True, type=int,
                     help="sensor image height (from RAW IFD)")
   parser.add_argument("-S", "--slice", required=True, type=int,
                     help="first sensor image slice width")
   parser.add_argument("-C", "--camera",
                     help="camera identifier string, for color conversion")
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
   assert all([h == args.height for f,w,h in components])
   assert sum([w for f,w,h in components]) == args.width
   a = np.zeros((args.height, args.width), dtype=np.dtype('>H'))
   for i, (f,w,h) in enumerate(components):
      # read raw data for this color component
      b = np.fromfile(f, dtype=np.dtype('>H'))
      b.shape = (h,w)
      # insert into assembled color image
      a[:,i::n] = b

   # determine the number of slices and the width of each slice
   slices = (args.width + args.slice - 1) // args.slice
   slice_widths = [args.slice] * (slices-1) + [args.width - args.slice*(slices-1)]
   # next unslice image
   I = np.zeros((args.height, args.width), dtype=np.dtype('>H'))
   for i, sw in enumerate(slice_widths):
      col_s = sum(slice_widths[0:i])
      col_e = col_s + sw
      I[:,col_s:col_e] = a.flat[col_s*args.height:col_e*args.height].reshape(args.height,sw)

   # convert to XYZ color space if necessary
   if args.camera:
      # get necessary transformation data
      #t_black, t_maximum, pre_mul, rgb_cam = jbtiff.tiff_file.color_table[args.camera]
      t_black, t_maximum, rgb_cam = jbtiff.tiff_file.color_table[args.camera]
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
      # apply pre-multipliers
      #print "Scaling with multipliers (%0.3f,%0.3f,%0.3f)" % (pre_mul[0], pre_mul[1], pre_mul[2])
      #R *= pre_mul[0]
      #G1 *= pre_mul[1]
      #G2 *= pre_mul[1]
      #B *= pre_mul[2]
      # copy color channels and interpolate missing data (nearest neighbour)
      I = np.zeros((args.height, args.width, 3))
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
      #rgb_cam /= rgb_cam.sum(axis=1, keepdims=True)
      I = np.dot(I, rgb_cam.transpose())
      # limit values
      np.clip(I, 0.0, 1.0, I)
      # apply sRGB gamma correction
      I = jbtiff.tiff_file.srgb_gamma(I)
      # scale to 16-bit
      I *= (1<<16)-1

   # save result
   #im = Image.fromarray(I.astype('int32'))
   #im.save(args.output, optimize=True)
   jbtiff.pnm_file.write(I.astype('>H'), open(args.output,'w'))

   # show user what we've done, as needed
   if args.display:
      # linear display
      plt.figure()
      plt.imshow(I, cmap=plt.cm.gray)
      plt.title('%s (linear)' % args.input)
      # gamma-corrected
      gamma = 2.2
      I = np.power(I/float(I.max()), 1/gamma)
      plt.figure()
      plt.imshow(I, cmap=plt.cm.gray)
      plt.title('%s (gamma %g)' % (args.input, gamma))
      # show everything
      plt.show()
   return

# main entry point
if __name__ == '__main__':
   main()
