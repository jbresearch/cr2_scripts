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

import os
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

   # add ranges of numbers from another set
   def add_ranges(self, x):
      assert isinstance(x, value_range)
      for k in x.data:
         self.add_range(k[0], k[1])
      return

   # subtract range of numbers, both inclusive
   def sub_range(self, lo, hi):
      assert lo <= hi
      tmp = []
      # copy over existing spans, editing as needed
      for a,b in self.data:
         # unaffected span
         if b < lo or a > hi:
            tmp.append((a,b))
            continue
         # completely subtracted span
         if a >= lo and b <= hi:
            continue
         # interior part erased
         if a < lo and b > hi:
            tmp.append((a, lo-1))
            tmp.append((hi+1, b))
            continue
         # initial part erased
         if a < lo:
            tmp.append((a, lo-1))
            continue
         # final part erased
         if b > hi:
            tmp.append((hi+1, b))
            continue
         # catch-all
         raise AssertionError("Unhandled situation: remove %s from %s" % ((lo,hi), (a,b)))
      # replace table with new version
      self.data = tmp
      return

   # subtract ranges of numbers from another set
   def sub_ranges(self, x):
      assert isinstance(x, value_range)
      for k in x.data:
         self.sub_range(k[0], k[1])
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
      return ', '.join(['%d-%d' % (a,b) if b>a else '%d' % a for a,b in self.data])

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

   tag_name = {}
   # load tag names from text file
   dirname = os.path.dirname(os.path.abspath(__file__))
   for line in open(os.path.join(dirname,'tiff-tags.txt'),'r'):
      record = line.split('\t')
      tag_name[int(record[0])] = record[2]

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

   # read TIFF header
   def read_tiff_header(self, fid, spans):
      # determine byte order
      fid.seek(0)
      tmp = fid.read(2)
      if tmp == 'II':
         self.little_endian = True
      elif tmp == 'MM':
         self.little_endian = False
      else:
         raise ValueError('Unexpected value for byte order: %s' % tmp)
      # determine TIFF identifier
      tmp = tiff_file.read_word(fid, 2, False, self.little_endian)
      assert tmp == 42
      # add header bytes
      spans.add_range(0, 8-1)
      return

   # read CR2 header if present
   def read_cr2_header(self, fid, spans):
      self.cr2 = False
      # read first TIFF offset
      fid.seek(4)
      tmp = tiff_file.read_word(fid, 4, False, self.little_endian)
      if tmp != 16:
         return
      # read CR2 magic word
      tmp = fid.read(2)
      if tmp != 'CR':
         return
      # read CR2 header data
      self.cr2 = True
      self.cr2_major = tiff_file.read_word(fid, 1, False, self.little_endian)
      self.cr2_minor = tiff_file.read_word(fid, 1, False, self.little_endian)
      self.cr2_ifd_offset = tiff_file.read_word(fid, 4, False, self.little_endian)
      # add header bytes
      spans.add_range(8, 16-1)
      return

   # read TIFF directory, starting at given offset
   def read_directory(self, fid, ifd_offset, spans):
      # read number of IFD entries
      fid.seek(ifd_offset)
      entry_count = tiff_file.read_word(fid, 2, False, self.little_endian)
      # add IFD bytes
      spans.add_range(ifd_offset, ifd_offset + 2 + entry_count*12 + 4 - 1)
      # read IFD entries
      IFD = {}
      for i in range(entry_count):
         # make sure we're in the correct position
         fid.seek(ifd_offset + 2 + i*12)
         # get IFD entry information
         tag = tiff_file.read_word(fid, 2, False, self.little_endian)
         field_type = tiff_file.read_word(fid, 2, False, self.little_endian)
         value_count = tiff_file.read_word(fid, 4, False, self.little_endian)
         # check if the value fits here or if we need offset
         value_offset = None
         if self.field_size[field_type] * value_count > 4:
            value_offset = tiff_file.read_word(fid, 4, False, self.little_endian)
            fid.seek(value_offset)
            # add value bytes
            spans.add_range(value_offset, value_offset + self.field_size[field_type] * value_count - 1)
         # read value(s)
         if field_type == 1: # BYTE
            values = [tiff_file.read_word(fid, 1, False, self.little_endian) for j in range(value_count)]
         elif field_type == 2: # ASCII
            tmp = fid.read(value_count)
            if tmp[-1] == '\0':
               tmp = tmp[:-1]
            values = tmp.split('\0')
         elif field_type == 3: # SHORT
            values = [tiff_file.read_word(fid, 2, False, self.little_endian) for j in range(value_count)]
         elif field_type == 4: # LONG
            values = [tiff_file.read_word(fid, 4, False, self.little_endian) for j in range(value_count)]
         elif field_type == 5: # RATIONAL
            values = [(tiff_file.read_word(fid, 4, False, self.little_endian), \
                       tiff_file.read_word(fid, 4, False, self.little_endian)) for j in range(value_count)]
         elif field_type == 6: # SBYTE
            values = [tiff_file.read_word(fid, 1, True, self.little_endian) for j in range(value_count)]
         elif field_type == 7: # UNDEFINED
            values = [tiff_file.read_word(fid, 1, False, self.little_endian) for j in range(value_count)]
         elif field_type == 8: # SSHORT
            values = [tiff_file.read_word(fid, 2, True, self.little_endian) for j in range(value_count)]
         elif field_type == 9: # SLONG
            values = [tiff_file.read_word(fid, 4, True, self.little_endian) for j in range(value_count)]
         elif field_type == 10: # SRATIONAL
            values = [(tiff_file.read_word(fid, 4, True, self.little_endian), \
                       tiff_file.read_word(fid, 4, True, self.little_endian)) for j in range(value_count)]
         elif field_type == 11: # FLOAT
            values = [tiff_file.read_float(fid, 4, self.little_endian) for j in range(value_count)]
         elif field_type == 12: # DOUBLE
            values = [tiff_file.read_float(fid, 8, self.little_endian) for j in range(value_count)]
         # store entry in IFD table with original offset if present
         IFD[tag] = (field_type, values, value_offset)
      # recursively read sub directories as needed
      for tag in [34665, 34853, 40965]: # EXIF, GPS, Interoperability
         if tag in IFD:
            # read original entry details
            field_type, values, value_offset = IFD[tag]
            assert len(values) == 1
            assert value_offset == None
            # decode
            value_offset = values[0]
            values = self.read_directory(fid, value_offset, spans)
            # replace values with subdirectory and original offset
            IFD[tag] = (field_type, values, value_offset)
      # return directory
      return IFD

   # initialize class from stream
   def __init__(self, fid):
      # keep track of range of bytes read
      spans = value_range()
      # check if this is a TIFF file
      self.read_tiff_header(fid, spans)
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
         ifd_offset = tiff_file.read_word(fid, 4, False, self.little_endian)
         # check if this was the last one
         if ifd_offset == 0:
            break
         # read TIFF directory
         IFD = self.read_directory(fid, ifd_offset, spans)
         # update pointer to next IFD offset
         offset_ptr = ifd_offset + 2 + len(IFD)*12
         # read data strips or embedded JPEG if present
         strips = []
         strip_offsets = []
         strip_lengths = []
         if 273 in IFD:
            assert 279 in IFD
            assert 513 not in IFD and 514 not in IFD
            strip_offsets = IFD[273][1]
            strip_lengths = IFD[279][1]
         if 513 in IFD:
            assert 514 in IFD
            assert 273 not in IFD and 279 not in IFD
            strip_offsets = IFD[513][1]
            strip_lengths = IFD[514][1]
         assert len(strip_offsets) == len(strip_lengths)
         for strip_offset, strip_length in zip(strip_offsets, strip_lengths):
            fid.seek(strip_offset)
            strips.append(fid.read(strip_length))
            spans.add_range(strip_offset, strip_offset + strip_length - 1)
         # store IFD, original offset, and data strips in table
         self.data.append((IFD, ifd_offset, strips))
         # display image size of this IFD
         if 256 in IFD and 257 in IFD:
            w = IFD[256][1][0]
            h = IFD[257][1][0]
            print "IFD#%d: image size %dx%d" % (len(self.data)-1, w, h)
         # display slice information from this IFD if present
         if self.cr2 and 50752 in IFD:
            slices = IFD[50752][1]
            print "IFD#%d: slices are %dx%d + %d" % (len(self.data)-1,slices[0],slices[1],slices[2])
      # display range of bytes used
      print "Bytes read:", spans.display()
      # determine file size
      fid.seek(0, 2)
      fsize = fid.tell()
      # determine range of bytes unused
      unused = value_range()
      unused.add_range(0, fsize-1)
      unused.sub_ranges(spans)
      # display range of bytes unused
      print "Bytes not read:", unused.display()
      # check content of unused ranges
      for i, (a,b) in enumerate(unused.data):
         # read data segment
         fid.seek(a)
         n = b-a+1
         data = fid.read(n)
         # check if it's all-zero
         if not all([x=='\0' for x in data]):
            print "Non-zero data at %d, length %d" % (a,n)
      return

   # determine written length of TIFF directory, including end alignment
   def get_directory_length(self, IFD, isleaf=False):
      # length for count and sequence of entries
      length = 2 + len(IFD)*12
      # length for offset at end
      if not isleaf:
         length += 4
      # length of any subdirectories present
      for tag in [34665, 34853, 40965]: # EXIF, GPS, Interoperability
         if tag in IFD:
            field_type, values, value_offset = IFD[tag]
            length += self.get_directory_length(values, True)
      # length of data for IFD entries
      for i, (tag, (field_type, values, value_offset)) in enumerate(sorted(IFD.iteritems())):
         # determine count
         if field_type == 2: # ASCII
            value_count = sum([len(x)+1 for x in values])
         else:
            value_count = len(values)
         # check if the value fits here or if we need data segment
         if self.field_size[field_type] * value_count > 4:
            length += tiff_file.align(self.field_size[field_type] * value_count)
      # done
      return tiff_file.align(length)

   # write TIFF header
   def write_tiff_header(self, fid):
      fid.seek(0)
      # byte order
      if self.little_endian:
         fid.write('II')
      else:
         fid.write('MM')
      # TIFF identifier
      tiff_file.write_word(42, fid, 2, False, self.little_endian)
      # return pointers to IFD space and to offset
      return 8, 4

   # write CR2 header if necessary
   def write_cr2_header(self, fid, free_ptr):
      # make sure this is a CR2 file
      if not self.cr2:
         return free_ptr, None
      # go to start of CR2 header
      assert free_ptr == 8
      fid.seek(free_ptr)
      # write CR2 magic word and version
      fid.write('CR')
      tiff_file.write_word(self.cr2_major, fid, 1, False, self.little_endian)
      tiff_file.write_word(self.cr2_minor, fid, 1, False, self.little_endian)
      tiff_file.write_word(0, fid, 4, False, self.little_endian) # space for CR2 IFD offset
      return free_ptr+8, free_ptr+4

   # write TIFF directory, starting at given offset
   def write_directory(self, IFD, fid, ifd_offset, isleaf=False):
      # write number of IFD entries
      fid.seek(ifd_offset)
      entry_count = len(IFD)
      tiff_file.write_word(entry_count, fid, 2, False, self.little_endian)
      # update pointer to offset and to next free space
      if isleaf:
         free_ptr = tiff_file.align(ifd_offset + 2 + entry_count*12)
      else:
         offset_ptr = ifd_offset + 2 + entry_count*12
         free_ptr = tiff_file.align(offset_ptr + 4)
      # write any subdirectories present
      for tag in [34665, 34853, 40965]: # EXIF, GPS, Interoperability
         if tag in IFD:
            field_type, values, value_offset = IFD[tag]
            value_offset = free_ptr
            free_ptr = self.write_directory(values, fid, value_offset, True)
            # replace value with offset for this subdirectory
            IFD[tag] = (field_type, [value_offset], None)
      # write IFD entries
      for i, (tag, (field_type, values, value_offset)) in enumerate(sorted(IFD.iteritems())):
         # make sure we're in the correct position
         fid.seek(ifd_offset + 2 + i*12)
         # write IFD entry information
         tiff_file.write_word(tag, fid, 2, False, self.little_endian)
         tiff_file.write_word(field_type, fid, 2, False, self.little_endian)
         # determine count
         if field_type == 2: # ASCII
            value_count = sum([len(x)+1 for x in values])
         else:
            value_count = len(values)
         tiff_file.write_word(value_count, fid, 4, False, self.little_endian)
         # check if the value fits here or if we need offset
         value_offset = None
         if self.field_size[field_type] * value_count > 4:
            value_offset = free_ptr
            tiff_file.write_word(value_offset, fid, 4, False, self.little_endian)
            fid.seek(value_offset)
            free_ptr = tiff_file.align(free_ptr + self.field_size[field_type] * value_count)
            # TODO: Update record with new value_offset
         # write value(s)
         if field_type == 1: # BYTE
            for value in values:
               tiff_file.write_word(value, fid, 1, False, self.little_endian)
         elif field_type == 2: # ASCII
            for value in values:
               fid.write(value)
               tiff_file.write_word(0, fid, 1, False, self.little_endian)
         elif field_type == 3: # SHORT
            for value in values:
               tiff_file.write_word(value, fid, 2, False, self.little_endian)
         elif field_type == 4: # LONG
            for value in values:
               tiff_file.write_word(value, fid, 4, False, self.little_endian)
         elif field_type == 5: # RATIONAL
            for value in values:
               tiff_file.write_word(value[0], fid, 4, False, self.little_endian)
               tiff_file.write_word(value[1], fid, 4, False, self.little_endian)
         elif field_type == 6: # SBYTE
            for value in values:
               tiff_file.write_word(value, fid, 1, True, self.little_endian)
         elif field_type == 7: # UNDEFINED
            for value in values:
               tiff_file.write_word(value, fid, 1, False, self.little_endian)
         elif field_type == 8: # SSHORT
            for value in values:
               tiff_file.write_word(value, fid, 2, True, self.little_endian)
         elif field_type == 9: # SLONG
            for value in values:
               tiff_file.write_word(value, fid, 4, True, self.little_endian)
         elif field_type == 10: # SRATIONAL
            for value in values:
               tiff_file.write_word(value[0], fid, 4, True, self.little_endian)
               tiff_file.write_word(value[1], fid, 4, True, self.little_endian)
         elif field_type == 11: # FLOAT
            for value in values:
               tiff_file.write_float(value, fid, 4, self.little_endian)
         elif field_type == 12: # DOUBLE
            for value in values:
               tiff_file.write_float(value, fid, 8, self.little_endian)
      # return updated pointers
      if isleaf:
         return free_ptr
      else:
         return offset_ptr, free_ptr

   # write data to stream
   def write(self, fid):
      # write TIFF header
      ifd_ptr, offset_ptr = self.write_tiff_header(fid)
      # write CR2 header if necessary
      ifd_ptr, cr2_offset_ptr = self.write_cr2_header(fid, ifd_ptr)
      # determine start of data space
      data_ptr = ifd_ptr
      for k, (IFD, ifd_offset, strips) in enumerate(self.data):
         data_ptr += self.get_directory_length(IFD)
      # keep track of start of data space to check for overlaps later
      start_data_ptr = data_ptr
      # write all IFDs and associated strips in file
      for k, (IFD, ifd_offset, strips) in enumerate(self.data):
         # write data strips if present
         if strips:
            tag_offset = None
            tag_length = None
            if 273 in IFD:
               assert 279 in IFD
               assert 513 not in IFD and 514 not in IFD
               tag_offset = 273
               tag_length = 279
            if 513 in IFD:
               assert 514 in IFD
               assert 273 not in IFD and 279 not in IFD
               tag_offset = 513
               tag_length = 514
            assert tag_offset and tag_length
            assert len(IFD[tag_offset][1]) == len(strips)
            assert len(IFD[tag_length][1]) == len(strips)
            for i, strip in enumerate(strips):
               # check and update IFD data
               assert IFD[tag_length][1][i] == len(strip)
               IFD[tag_offset][1][i] = data_ptr
               # write data to file
               fid.seek(data_ptr)
               fid.write(strip)
               # update free pointer
               data_ptr = tiff_file.align(data_ptr + len(strip))
         # if this was the CR2 IFD, write its offset in header
         if self.cr2 and ifd_offset == self.cr2_ifd_offset:
            print "Writing offset to IFD#%d = %d (0x%08x) as CR2" % (k, ifd_ptr, ifd_ptr)
            self.cr2_ifd_offset = ifd_ptr
            assert cr2_offset_ptr == 12
            fid.seek(cr2_offset_ptr)
            tiff_file.write_word(self.cr2_ifd_offset, fid, 4, False, self.little_endian)
         # write offset to this IFD
         fid.seek(offset_ptr)
         tiff_file.write_word(ifd_ptr, fid, 4, False, self.little_endian)
         # write TIFF directory
         offset_ptr, ifd_ptr = self.write_directory(IFD, fid, ifd_ptr)
      # write null offset to IFD
      fid.seek(offset_ptr)
      tiff_file.write_word(0, fid, 4, False, self.little_endian)
      # check for overlap of IFD into data space
      assert ifd_ptr <= start_data_ptr
      return

   # print formatted data to stream
   @staticmethod
   def display_directory(fid, IFD, shift=1):
      for i, (tag, (field_type, values, value_offset)) in enumerate(sorted(IFD.iteritems())):
         print >> fid, " "*3*shift + "Entry %d:" % i
         # display IFD entry information
         if tag in tiff_file.tag_name:
            print >> fid, " "*3*(shift+1) + "Tag: %d (%s)" % (tag, tiff_file.tag_name[tag])
         else:
            print >> fid, " "*3*(shift+1) + "Tag: %d" % tag
         print >> fid, " "*3*(shift+1) + "Type: %d (%s)" % (field_type, tiff_file.field_name[field_type])
         # display value offset if present
         if value_offset:
            print >> fid, " "*3*(shift+1) + "Pointer: %d (0x%08x)" % (value_offset, value_offset)
         # display value(s)
         if isinstance(values, list):
            print >> fid, " "*3*(shift+1) + "Values:", values
         elif isinstance(values, dict):
            print >> fid, " "*3*(shift+1) + "Subdirectory:"
            # display subdirectory entries
            tiff_file.display_directory(fid, values, shift+1)
         else:
            raise AssertionError("Unknown value type")
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
         print >> fid, "CR2: IFD at %d (0x%08x)" % (self.cr2_ifd_offset, self.cr2_ifd_offset)
      # display all IFDs in file
      for k, (IFD, ifd_offset, strips) in enumerate(self.data):
         print >> fid, "IFD#%d: at %d (0x%08x)" % (k, ifd_offset, ifd_offset)
         # display IFD entries
         tiff_file.display_directory(fid, IFD)
      return

   # print formatted data to stream
   def save_data(self, basename):
      # go through all IFDs in file
      for k, (IFD, ifd_offset, strips) in enumerate(self.data):
         # save strips
         if strips:
            fid = open('%s-%d.dat' % (basename, k), 'w')
            for strip in strips:
               fid.write(strip)
            fid.close()
      return
