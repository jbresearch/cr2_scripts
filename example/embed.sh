#!/bin/bash
#
# Copyright (c) 2015-2016 Johann A. Briffa
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

../rgb_encode.py -r 2908.cr2 -i Sensor/2908r.ppm -o Sensor/2908r.pgm -s Components/2908r-2.dat -B 1025 -C "Canon EOS 450D"
../raw_encode.py -r 2908.cr2 -i Sensor/2908r.pgm -o Components/2908r-3.dat -C 2 -P 14
convert Manual/2908r.jpg -strip -rotate "90<" -resize "2256x1504" -define jpeg:optimize-coding=false -quality 50 -define jpeg:q-table=canon-q-table.xml jpeg:Components/2908r-0.dat
convert Manual/2908r.jpg -strip -rotate "90<" -resize "160x120" -gravity center -background black -extent "160x120" -define jpeg:optimize-coding=false -quality 50 -define jpeg:q-table=canon-q-table.xml jpeg:Components/2908r-1.dat
../cr2_embed.py -i 2908.cr2 -b Components/2908r -o 2908r.cr2
