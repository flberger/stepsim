"""StepSim Setup Script

   Copyright 2010 Florian Berger <fberger@florian-berger.de>
"""

# This file is part of stepsim.
#
# stepsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# stepsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with stepsim.  If not, see <http://www.gnu.org/licenses/>.

# work started on 8 Februar 2010

import distutils.core

VERSION = "0.1.0"

distutils.core.setup(name = "stepsim",
                     version = VERSION,
                     author = "Florian Berger",
                     author_email = "fberger@florian-berger.de",
                     url = "http://florian-berger.de/software/stepsim/",
                     description = "StepSim - Python Step-based Simulation Package",
                     license = "GPL",
                     py_modules = ["stepsim"],
                     packages = [],
                     requires = [],
                     provides = ["stepsim"],
                     scripts = [],
                     data_files = [("share/doc/stepsim/examples", ['making_cakes.py'])])
