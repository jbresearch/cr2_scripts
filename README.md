# CR2_Scripts

The CR2_Scripts project consists of a set of scripts for converting
[Canon RAW](http://lclevy.free.fr/cr2/) format files to and from
[Netpbm](http://netpbm.sourceforge.net/) format files.

Documentation is available as follows:
- Brief user documentation is available for each script by passing the
   conventional '-h' or '--help' parameter.
- An introduction to CR2_Scripts can be found in the following blog post:
   [Scripts for reading and writing Canon RAW files](https://jabriffa.wordpress.com/2016/01/21/scripts-for-reading-and-writing-canon-raw-files/)

To contact us:
- For bug reports, use the [issue tracker](https://github.com/jbresearch/cr2_scripts/issues)
- For public comments or questions, leave a comment on [Scripts for reading and writing Canon RAW files](https://jabriffa.wordpress.com/2016/01/21/scripts-for-reading-and-writing-canon-raw-files/)
- For private communication, use the [contact form on my blog](https://jabriffa.wordpress.com/about/).

# Prerequisites

The scripts are written in python, as far as possible in a platform-indepedent
way. However, they have only been tested on a 64-bit Ubuntu 14.04 LTS system.
To use this software you need the following installed on your system (Ubuntu
package names given in parentheses):

- Python v2.7.6 (`python`)
- Numpy v1.8.2 (`python-numpy`)
- Matplotlib v1.3.1 (`python-matplotlib`)
- PVRG JPEG v1.2.1 (`pvrg-jpeg`)

Later versions, with the notable exception of Python v3.x, should also work.
For PVRG JPEG, note that the scripts assume the name of the executable is
`pvrg-jpeg`; this is correct if you install the Ubuntu package.
However, the [upstream source](http://www.panix.com/~eli/jpeg/) names its
executable simply as `jpeg`.

# Copyright and license

Copyright © 2015-2017 Johann A. Briffa

This file is part of CR2_Scripts.

CR2_Scripts is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CR2_Scripts is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CR2_Scripts.  If not, see <http://www.gnu.org/licenses/>.
