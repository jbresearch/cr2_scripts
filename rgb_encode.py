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
                     help="input color image file to encode (PPM)")
   parser.add_argument("-o", "--output", required=True,
                     help="output sensor image file (PGM)")
   parser.add_argument("-s", "--small", required=True,
                     help="output small RGB image file (DAT)")
   parser.add_argument("-B", "--black", required=True, type=int,
                     help="black level (same for all channels)")
   parser.add_argument("-C", "--camera",
                     help="camera identifier string for color table lookup")
   parser.add_argument("-d", "--display", action="store_true", default=False,
                     help="display encoded image")
   args = parser.parse_args()

   # obtain required parameters from RAW file
   tiff = jbtiff.tiff_file(open(args.raw, 'r'))
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
   a[:,:,0] = I[0::step,0::step,0] # Red
   a[:,:,1] = I[0::step,1::step,1] # Green 1
   #a[:,:,1] = I[1::step,0::step,1] # Green 2
   a[:,:,2] = I[1::step,1::step,2] # Blue
   # add border
   dy1 = (sheight - a.shape[0])//2
   dy2 = sheight - a.shape[0] - dy1
   dx1 = (swidth - a.shape[1])//2
   dx2 = swidth - a.shape[1] - dx1
   a = np.pad(a, ((dy1,dy2),(dx1,dx2),(0,0)), mode='constant', constant_values=args.black).astype(dtype)
   assert a.shape == (sheight, swidth, 3)
   # save result
   a.tofile(open(args.small,'w'))

   # create full sensor image and copy color channels
   a = np.zeros((iheight,iwidth), dtype=np.dtype('>H'))
   a[0::2,0::2] = I[0::2,0::2,0] # Red
   a[0::2,1::2] = I[0::2,1::2,1] # Green 1
   a[1::2,0::2] = I[1::2,0::2,1] # Green 2
   a[1::2,1::2] = I[1::2,1::2,2] # Blue
   # add border
   a = np.pad(a, ((y1,height-y2-1),(x1,width-x2-1)), mode='constant', constant_values=args.black).astype('>H')
   assert a.shape == (height, width)
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
