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

class value_range():

   # initialize as blank sequence
   def __init__(self):
      self.data = []
      return

   # add range of numbers, both inclusive
   def add_range(self, lo, hi):
      assert lo <= hi
      # find insertion point
      index = len(self.data)
      for i, (a,b) in enumerate(self.data):
         if lo <= b:
            index = i
            break
      # insert as new range
      self.data.insert(index, (lo,hi))
      # now flatten the existing range
      self.flatten()
      return

   # flatten sequence of ranges into shortest expression
   def flatten(self):
      tmp = []
      span = None
      for a,b in self.data:
         # nothing there yet
         if not span:
            span = (a,b)
            continue
         # mergeable spans
         if a <= span[1]+1 and b >= span[0]-1:
            span = (min(a,span[0]), max(b,span[1]))
            continue
         # un-mergeable spans
         tmp.append(span)
         span = (a,b)
      # write last entry
      tmp.append(span)
      # replace table with flattened version
      self.data = tmp
      return

   # display overall range used
   def display(self):
      return ', '.join(['%d-%d' % (a,b) for a,b in self.data])

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

   field_name = {
      1: 'BYTE',
      2: 'ASCII',
      3: 'SHORT',
      4: 'LONG',
      5: 'RATIONAL',
      6: 'SBYTE',
      7: 'UNDEFINED',
      8: 'SSHORT',
      9: 'SLONG',
      10: 'SRATIONAL',
      11: 'FLOAT',
      12: 'DOUBLE',
      }

   ## class functions

   # return value aligned to word boundary (increasing as necessary)
   @staticmethod
   def align(value, word_size=2):
      return ((value + word_size - 1) // word_size) * word_size

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

   # read CR2 header if present
   def read_cr2_header(self, fid, spans):
      self.cr2 = False
      # read first TIFF offset
      fid.seek(4)
      tmp = self.read_word(fid, 4, False, self.little_endian)
      if tmp != 16:
         return
      # read CR2 magic word
      tmp = fid.read(2)
      if tmp != 'CR':
         return
      # read CR2 header data
      self.cr2 = True
      self.cr2_major = self.read_word(fid, 1, False, self.little_endian)
      self.cr2_minor = self.read_word(fid, 1, False, self.little_endian)
      self.cr2_ifd_offset = self.read_word(fid, 4, False, self.little_endian)
      # add header bytes
      spans.add_range(8, 16-1)
      return

   # read TIFF directory, starting at given offset
   def read_directory(self, fid, ifd_offset, spans):
      # read number of IFD entries
      fid.seek(ifd_offset)
      entry_count = self.read_word(fid, 2, False, self.little_endian)
      # add IFD bytes
      spans.add_range(ifd_offset, ifd_offset + 2 + entry_count*12 + 4 - 1)
      # read IFD entries
      IFD = {}
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
            # add value bytes
            spans.add_range(value_offset, value_offset + self.field_size[field_type] * value_count - 1)
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
         IFD[tag] = (field_type, values)
      # recursively read sub directories as needed
      for tag in [34665, 34853]: # EXIF, GPS
         if tag in IFD:
            field_type, values = IFD[tag]
            assert len(values) == 1
            tmp = self.read_directory(fid, values[0], spans)
            # replace values with subdirectory
            IFD[tag] = (field_type, tmp)
      return IFD

   # initialize class from stream
   def __init__(self, fid):
      # keep track of range of bytes read
      spans = value_range()
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
      # add header bytes
      spans.add_range(0, 8-1)
      # initialize pointer to next IFD offset
      offset_ptr = 4
      # check if this is a CR2 file
      self.read_cr2_header(fid, spans)
      # initialize IFD table
      self.data = []
      # read all IFDs and associated strips in file
      while True:
         # get offset to IFD
         fid.seek(offset_ptr)
         ifd_offset = self.read_word(fid, 4, False, self.little_endian)
         # check if this was the last one
         if ifd_offset == 0:
            break
         # read TIFF directory
         IFD = self.read_directory(fid, ifd_offset, spans)
         # update pointer to next IFD offset
         offset_ptr = ifd_offset + 2 + len(IFD)*12
         # read data strips if present
         strips = []
         if 273 in IFD:
            assert 279 in IFD
            assert len(IFD[273][1]) == len(IFD[279][1])
            for strip_offset, strip_length in zip(IFD[273][1], IFD[279][1]):
               fid.seek(strip_offset)
               strips.append(fid.read(strip_length))
               spans.add_range(strip_offset, strip_offset + strip_length - 1)
         # store IFD and data strips in table
         self.data.append((IFD, strips))
      # display range of bytes used
      print "Bytes read:", spans.display()
      return

   # write TIFF directory, starting at given offset
   def write_directory(self, IFD, fid, ifd_offset, isleaf=False):
      # write number of IFD entries
      fid.seek(ifd_offset)
      entry_count = len(IFD)
      self.write_word(entry_count, fid, 2, False, self.little_endian)
      # update pointer to offset and to next free space
      if isleaf:
         free_ptr = self.align(ifd_offset + 2 + entry_count*12)
      else:
         offset_ptr = ifd_offset + 2 + entry_count*12
         free_ptr = self.align(offset_ptr + 4)
      # write any subdirectories present
      for tag in [34665, 34853]: # EXIF, GPS
         if tag in IFD:
            field_type, values = IFD[tag]
            sub_offset = free_ptr
            free_ptr = self.write_directory(values, fid, sub_offset, True)
            # replace value with offset for this subdirectory
            IFD[tag] = (field_type, [sub_offset])
      # write IFD entries
      for i, (tag, (field_type, values)) in enumerate(sorted(IFD.iteritems())):
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
            free_ptr = self.align(free_ptr + self.field_size[field_type] * value_count)
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
      # return updated pointers
      if isleaf:
         return free_ptr
      else:
         return offset_ptr, free_ptr

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
      # write all IFDs and associated strips in file
      for IFD, strips in self.data:
         # write data strips if present
         if strips:
            assert 273 in IFD
            assert 279 in IFD
            assert len(IFD[273][1]) == len(strips)
            assert len(IFD[279][1]) == len(strips)
            for i, strip in enumerate(strips):
               # determine strip details
               strip_offset = free_ptr
               strip_length = len(strip)
               # check and update IFD data
               assert IFD[279][1][i] == strip_length
               IFD[273][1][i] = strip_offset
               # write data to file
               fid.seek(strip_offset)
               fid.write(strip)
               # update free pointer
               free_ptr = self.align(free_ptr + strip_length)
         # write offset to this IFD
         ifd_offset = free_ptr
         fid.seek(offset_ptr)
         self.write_word(ifd_offset, fid, 4, False, self.little_endian)
         # write TIFF directory
         offset_ptr, free_ptr = self.write_directory(IFD, fid, ifd_offset)
      # write null offset to IFD
      fid.seek(offset_ptr)
      self.write_word(0, fid, 4, False, self.little_endian)
      return

   # print formatted data to stream
   def display(self, fid):
      # byte order
      if self.little_endian:
         print >> fid, "Byte order: little-endian"
      else:
         print >> fid, "Byte order: big-endian"
      # CR2 header if present
      if self.cr2:
         print >> fid, "CR2: v%d.%d" % (self.cr2_major, self.cr2_minor)
         print >> fid, "CR2: IFD at 0x%08x" % (self.cr2_ifd_offset)
      # display all IFDs in file
      for k, (IFD, strips) in enumerate(self.data):
         print >> fid, "IFD#%d:" % k
         # display IFD entries
         for i, (tag, (field_type, values)) in enumerate(sorted(IFD.iteritems())):
            print >> fid, "   Entry %d:" % i
            # display IFD entry information
            print >> fid, "      Tag: %s" % tag
            print >> fid, "      Type: %d (%s)" % (field_type, self.field_name[field_type])
            # display value(s)
            print >> fid, "      Value: %s" % values
      return
