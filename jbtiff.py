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

import struct

class tiff_file():

   ## constants

   field_size = {
      1: 1, # BYTE 8-bit unsigned integer.
      2: 1, # ASCII 8-bit byte that contains a 7-bit ASCII code; the last byte must be NUL (binary zero).
      3: 2, # SHORT 16-bit (2-byte) unsigned integer.
      4: 4, # LONG 32-bit (4-byte) unsigned integer.
      5: 8, # RATIONAL Two LONGs: the first represents the numerator of a fraction; the second, the denominator.
      6: 1, # SBYTE An 8-bit signed (twos-complement) integer.
      7: 1, # UNDEFINED An 8-bit byte that may contain anything, depending on the definition of the field.
      8: 2, # SSHORT A 16-bit (2-byte) signed (twos-complement) integer.
      9: 4, # SLONG A 32-bit (4-byte) signed (twos-complement) integer.
      10: 8, # SRATIONAL Two SLONG’s: the first represents the numerator of a fraction, the second the denominator.
      11: 4, # FLOAT Single precision (4-byte) IEEE format.
      12: 8, # DOUBLE Double precision (8-byte) IEEE format.
      }

   ## class functions

   # read a word of given size (in bytes), endianness, and signed/unsigned state
   @staticmethod
   def read_word(fid, size, signed, little_endian):
      tmp = fid.read(size)
      # set up endianness
      if little_endian:
         fmt = '<'
      else:
         fmt = '>'
      # set up word size
      if size == 1:
         fmt += 'B'
      elif size == 2:
         fmt += 'H'
      elif size == 4:
         fmt += 'L'
      else:
         raise ValueError('Unsupported word size: %d' % size)
      # set up signed/unsigned nature
      if signed:
         fmt = fmt.lower()
      # convert and return
      return struct.unpack(fmt, tmp)[0]

   # read a real number of given size (in bytes) and endianness
   @staticmethod
   def read_float(fid, size, little_endian):
      tmp = fid.read(size)
      # set up endianness
      if little_endian:
         fmt = '<'
      else:
         fmt = '>'
      # set up word size
      if size == 4:
         fmt += 'f'
      elif size == 8:
         fmt += 'd'
      else:
         raise ValueError('Unsupported float size: %d' % size)
      # convert and return
      return struct.unpack(fmt, tmp)[0]

   # write a word of given size (in bytes), endianness, and signed/unsigned state
   @staticmethod
   def write_word(data, fid, size, signed, little_endian):
      # set up endianness
      if little_endian:
         fmt = '<'
      else:
         fmt = '>'
      # set up word size
      if size == 1:
         fmt += 'B'
      elif size == 2:
         fmt += 'H'
      elif size == 4:
         fmt += 'L'
      else:
         raise ValueError('Unsupported word size: %d' % size)
      # set up signed/unsigned nature
      if signed:
         fmt = fmt.lower()
      # convert and write
      buf = struct.pack(fmt, data)
      assert len(buf) == size
      fid.write(buf)
      return

   # write a real number of given size (in bytes) and endianness
   @staticmethod
   def write_float(data, fid, size, little_endian):
      # set up endianness
      if little_endian:
         fmt = '<'
      else:
         fmt = '>'
      # set up word size
      if size == 4:
         fmt += 'f'
      elif size == 8:
         fmt += 'd'
      else:
         raise ValueError('Unsupported float size: %d' % size)
      # convert and write
      buf = struct.pack(fmt, data)
      assert len(buf) == size
      fid.write(buf)
      return

   ## class methods

   # initialize class from stream
   def __init__(self, fid):
      # determine byte order
      tmp = fid.read(2)
      if tmp == 'II':
         self.little_endian = True
      elif tmp == 'MM':
         self.little_endian = False
      else:
         raise ValueError('Unexpected value for byte order: %s' % tmp)
      # determine TIFF identifier
      tmp = self.read_word(fid, 2, False, self.little_endian)
      assert tmp == 42
      # initialize IFD table
      self.IFDs = []
      # read all IFDs in file
      while True:
         # get offset to IFD
         ifd_offset = self.read_word(fid, 4, False, self.little_endian)
         # check if this was the last one
         if ifd_offset == 0:
            break
         # read number of IFD entries
         fid.seek(ifd_offset)
         entry_count = self.read_word(fid, 2, False, self.little_endian)
         # read IFD entries
         IFD = []
         for i in range(entry_count):
            # make sure we're in the correct position
            fid.seek(ifd_offset + 2 + i*12)
            # get IFD entry information
            tag = self.read_word(fid, 2, False, self.little_endian)
            field_type = self.read_word(fid, 2, False, self.little_endian)
            value_count = self.read_word(fid, 4, False, self.little_endian)
            # check if the value fits here or if we need offset
            if self.field_size[field_type] * value_count > 4:
               value_offset = self.read_word(fid, 4, False, self.little_endian)
               fid.seek(value_offset)
            # read value(s)
            if field_type == 1: # BYTE
               values = [self.read_word(fid, 1, False, self.little_endian) for j in range(value_count)]
            elif field_type == 2: # ASCII
               tmp = fid.read(value_count)
               if tmp[-1] == '\0':
                  tmp = tmp[:-1]
               values = tmp.split('\0')
            elif field_type == 3: # SHORT
               values = [self.read_word(fid, 2, False, self.little_endian) for j in range(value_count)]
            elif field_type == 4: # LONG
               values = [self.read_word(fid, 4, False, self.little_endian) for j in range(value_count)]
            elif field_type == 5: # RATIONAL
               values = [(self.read_word(fid, 4, False, self.little_endian), \
                          self.read_word(fid, 4, False, self.little_endian)) for j in range(value_count)]
            elif field_type == 6: # SBYTE
               values = [self.read_word(fid, 1, True, self.little_endian) for j in range(value_count)]
            elif field_type == 7: # UNDEFINED
               values = [self.read_word(fid, 1, False, self.little_endian) for j in range(value_count)]
            elif field_type == 8: # SSHORT
               values = [self.read_word(fid, 2, True, self.little_endian) for j in range(value_count)]
            elif field_type == 9: # SLONG
               values = [self.read_word(fid, 4, True, self.little_endian) for j in range(value_count)]
            elif field_type == 10: # SRATIONAL
               values = [(self.read_word(fid, 4, True, self.little_endian), \
                          self.read_word(fid, 4, True, self.little_endian)) for j in range(value_count)]
            elif field_type == 11: # FLOAT
               values = [self.read_float(fid, 4, self.little_endian) for j in range(value_count)]
            elif field_type == 12: # DOUBLE
               values = [self.read_float(fid, 8, self.little_endian) for j in range(value_count)]
            # store entry in IFD table
            IFD.append((tag, field_type, values))
         # store IFD in table
         self.IFDs.append(IFD)
         # make sure we're in the correct position to read next offset
         fid.seek(ifd_offset + 2 + entry_count*12)
      return

   # write data to stream
   def write(self, fid):
      # byte order
      if self.little_endian:
         fid.write('II')
      else:
         fid.write('MM')
      # TIFF identifier
      self.write_word(42, fid, 2, False, self.little_endian)
      # initialize pointers to offset and to next free space
      offset_ptr = 4
      free_ptr = 8
      # write all IFDs in file
      for IFD in self.IFDs:
         # write offset to this IFD
         ifd_offset = free_ptr
         fid.seek(offset_ptr)
         self.write_word(ifd_offset, fid, 4, False, self.little_endian)
         # write number of IFD entries
         fid.seek(ifd_offset)
         entry_count = len(IFD)
         self.write_word(entry_count, fid, 2, False, self.little_endian)
         # update pointer to offset and to next free space
         offset_ptr = ifd_offset + 2 + entry_count*12
         free_ptr =  offset_ptr + 4
         # write IFD entries
         for i, (tag, field_type, values) in enumerate(IFD):
            # make sure we're in the correct position
            fid.seek(ifd_offset + 2 + i*12)
            # write IFD entry information
            self.write_word(tag, fid, 2, False, self.little_endian)
            self.write_word(field_type, fid, 2, False, self.little_endian)
            # determine count
            if field_type == 2: # ASCII
               value_count = sum([len(x)+1 for x in values])
            else:
               value_count = len(values)
            self.write_word(value_count, fid, 4, False, self.little_endian)
            # check if the value fits here or if we need offset
            if self.field_size[field_type] * value_count > 4:
               value_offset = free_ptr
               self.write_word(value_offset, fid, 4, False, self.little_endian)
               fid.seek(value_offset)
               free_ptr += self.field_size[field_type] * value_count
            # write value(s)
            if field_type == 1: # BYTE
               for value in values:
                  self.write_word(value, fid, 1, False, self.little_endian)
            elif field_type == 2: # ASCII
               for value in values:
                  fid.write(value)
                  self.write_word(0, fid, 1, False, self.little_endian)
            elif field_type == 3: # SHORT
               for value in values:
                  self.write_word(value, fid, 2, False, self.little_endian)
            elif field_type == 4: # LONG
               for value in values:
                  self.write_word(value, fid, 4, False, self.little_endian)
            elif field_type == 5: # RATIONAL
               for value in values:
                  self.write_word(value[0], fid, 4, False, self.little_endian)
                  self.write_word(value[1], fid, 4, False, self.little_endian)
            elif field_type == 6: # SBYTE
               for value in values:
                  self.write_word(value, fid, 1, True, self.little_endian)
            elif field_type == 7: # UNDEFINED
               for value in values:
                  self.write_word(value, fid, 1, False, self.little_endian)
            elif field_type == 8: # SSHORT
               for value in values:
                  self.write_word(value, fid, 2, True, self.little_endian)
            elif field_type == 9: # SLONG
               for value in values:
                  self.write_word(value, fid, 4, True, self.little_endian)
            elif field_type == 10: # SRATIONAL
               for value in values:
                  self.write_word(value[0], fid, 4, True, self.little_endian)
                  self.write_word(value[1], fid, 4, True, self.little_endian)
            elif field_type == 11: # FLOAT
               for value in values:
                  self.write_float(value, fid, 4, self.little_endian)
            elif field_type == 12: # DOUBLE
               for value in values:
                  self.write_float(value, fid, 8, self.little_endian)
      # write null offset to IFD
      fid.seek(offset_ptr)
      self.write_word(0, fid, 4, False, self.little_endian)
      return
