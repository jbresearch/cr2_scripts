#!/bin/bash
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

../cr2_extract.py -i 2908.cr2 -o Components/2908 -d > 2908.txt
../raw_decode.py -r 2908.cr2 -i Components/2908-3.dat -o Sensor/2908.pgm
../rgb_decode.py -r 2908.cr2 -i Sensor/2908.pgm -o Sensor/2908.ppm -C "Canon EOS 450D"
