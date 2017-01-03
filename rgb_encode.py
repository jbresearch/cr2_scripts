#!/usr/bin/python
# coding=utf8
#
# Copyright © 2015-2017 Johann A. Briffa
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

## main program

def main():
   # interpret user options
   parser = argparse.ArgumentParser()
   parser.add_argument("-r", "--raw", required=True,
                     help="input RAW file for image parameters")
   parser.add_argument("-i", "--input", required=True,
                     help="input color image file to encode (PPM)")
   parser.add_argument("-o", "--output", required=True,
                     help="output sensor image file (PGM)")
   parser.add_argument("-s", "--small", required=True,
                     help="output small RGB image file (DAT)")
   parser.add_argument("-B", "--black", required=True, type=int,
                     help="black level (same for all channels)")
   parser.add_argument("-S", "--saturation", type=int,
                     help="saturation level (overriding camera default)")
   parser.add_argument("-b", "--bayer", default="RGGB",
                     help="Bayer pattern (first letter paid for odd rows, second pair for even rows)")
   parser.add_argument("-C", "--camera",
                     help="camera identifier string for color table lookup")
   parser.add_argument("-d", "--display", action="store_true", default=False,
                     help="display encoded image")
   args = parser.parse_args()

   # obtain required parameters from RAW file
   tiff = jbtiff.tiff_file(open(args.raw, 'rb'))
   swidth,sheight = tiff.get_image_size(2)
   sdepth = tiff.get_image_depth(2)
   width,height = tiff.get_sensor_size()
   border = tiff.get_border()
   if args.camera:
      model = args.camera
   else:
      model = tiff.get_model(0)
   # determine image size without border
   x1,y1,x2,y2 = border
   iwidth = x2-x1+1
   iheight = y2-y1+1

   # load colour image
   I = jbtiff.pnm_file.read(open(args.input,'r'))
   assert len(I.shape) == 3 and I.shape[2] == 3 # must be a three-channel image
   assert I.shape == (iheight,iwidth,3) # image size must be exact

   # scale each channel to [0.0,1.0]
   if I.dtype == np.dtype('uint8'):
      depth = 8
   elif I.dtype == np.dtype('>H'):
      depth = 16
   else:
      raise ValueError("Cannot handle input arrays of type %s" % I.dtype)
   I = I / float((1<<depth)-1)
   # invert sRGB gamma correction
   I = jbtiff.tiff_file.srgb_gamma_inverse(I)
   # get necessary transformation data
   t_black, t_maximum, cam_rgb = jbtiff.tiff_file.color_table[model]
   # convert from linear RGB D65 space to camera color space
   I = np.dot(I, cam_rgb.transpose())
   # limit values
   np.clip(I, 0.0, 1.0, I)
   # add black level and scale each channel to saturation limit
   if args.saturation:
      t_maximum = args.saturation
   print "Scaling with black level %d, saturation %d" % (args.black,t_maximum)
   I = I * (t_maximum - args.black) + args.black

   # determine subsampling rate
   step = int(round(height / float(sheight)))
   assert step == 2 ** int(np.log2(step))
   # determine precision to use
   if sdepth == 16:
      dtype = np.dtype('<H')
   elif sdepth == 8:
      dtype = np.dtype('uint8')
   else:
      raise ValueError("Cannot handle raw images of depth %d" % sdepth)
   # create small RGB image and copy color channels
   a = np.zeros((iheight//step, iwidth//step, 3), dtype=dtype)
   a[:] = I[0::step,0::step,:]
   # add border
   dy1 = (sheight - a.shape[0])//2
   dy2 = sheight - a.shape[0] - dy1
   dx1 = (swidth - a.shape[1])//2
   dx2 = swidth - a.shape[1] - dx1
   a = np.pad(a, ((dy1,dy2),(dx1,dx2),(0,0)), mode='constant', constant_values=args.black).astype(dtype)
   assert a.shape == (sheight, swidth, 3)
   # save result
   a.tofile(open(args.small,'w'))

   # add border
   dy1 = y1
   dy2 = height-y2-1
   dx1 = x1
   dx2 = width-x2-1
   I = np.pad(I, ((dy1,dy2),(dx1,dx2),(0,0)), mode='constant', constant_values=args.black).astype('>H')
   assert I.shape == (height, width, 3)
   # determine mapping for each colour channel
   assert len(args.bayer) == 4
   cmap = {v: k for k, v in enumerate("RGB")}
   # create full sensor image and copy color channels
   a = np.zeros((height,width), dtype=np.dtype('>H'))
   a[0::2,0::2] = I[0::2,0::2,cmap[args.bayer[0]]]
   a[0::2,1::2] = I[0::2,1::2,cmap[args.bayer[1]]]
   a[1::2,0::2] = I[1::2,0::2,cmap[args.bayer[2]]]
   a[1::2,1::2] = I[1::2,1::2,cmap[args.bayer[3]]]
   # save result
   jbtiff.pnm_file.write(a, open(args.output,'w'))

   # show user what we've done, as needed
   if args.display:
      # linear display
      plt.figure()
      plt.imshow(a, cmap=plt.cm.gray)
      plt.title('%s' % args.input)
      # show everything
      plt.show()
   return

# main entry point
if __name__ == '__main__':
   main()
