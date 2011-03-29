"""StepSim Setup Script

   Copyright 2011 Florian Berger <fberger@florian-berger.de>
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

VERSION = "0.3.1"
LONG_DESCRIPTION = """About
-----

StepSim is a lightweight step-based simulation module written in Python.
It can do simple real-time simulations of discrete systems. StepSim
supports step-by-step simulation or can run until a break condition
occurs.

Simulations are made up of *containers* and *converters*. A *container*
stores a discrete amount of units of a certain type. A *converter* draws
units from one or more containers and delivers the result to another
container.

StepSim does not even attempt to do any parallel processing. It
processes converters round-robin in a fixed order.

Prerequisites
-------------

Python (tested on Python 3.1.2 and 2.6.5)
`http://www.python.org <http://www.python.org>`_

Installation
------------

Unzip the file, then at the command line run

::

    python setup.py install

Running Tests
-------------

Open a shell / DOS window, navigate to the stepsim directory, and run

::

    python -m doctest README

Documentation
-------------

To read the API documentation, open a shell / DOS window, navigate to
the stepsim directory, and run

::

    pydoc stepsim

You can create a HTML version using

::

    pydoc -w stepsim

Example
-------

First import the stepsim module:

::

    >>> import stepsim

To get verbose output, activate logging to console:

::

    >>> stepsim.log_to_stdout()

Now create some containers:

::

    >>> cashbox = stepsim.Container("cashbox", "EUR", 10)
    >>> storage = stepsim.Container("storage", "parts")

Then create a converter and set up the draw-deliver-ratio:

::

    >>> buyer = stepsim.Converter("buyer", 2, (cashbox, 3), (storage, 1))
    buyer: Adding source 'cashbox', drawing 3 EUR per step.

We are ready to create a simulation:

::

    >>> s = stepsim.Simulation(buyer)
    Adding converter 'buyer' to simulation.
    Current containers: ['cashbox', 'storage']
    >>> s
    <Simulation consisting of [<buyer: converting from ['cashbox'] to storage>]>

You can now step through the simulation or simply let it run until an
end condition is satisfied. In this case we let it run until the buyer
can not buy any more parts:

::

    >>> s.run(lambda : not buyer.last_step_successful)
    Starting simulation.
    --- Step 1: -----------------------------------------------
    buyer: Ready to draw resources
    buyer: Drawing 3 EUR from cashbox. cashbox has 7 EUR left now.
    Active Container of buyer: <cashbox: 7 EUR in stock>
    --- Step 2: -----------------------------------------------
    buyer: Conversion in progress, 2 steps left.
    Active Container of buyer: None
    --- Step 3: -----------------------------------------------
    buyer: Conversion in progress, 1 steps left.
    Active Container of buyer: None
    --- Step 4: -----------------------------------------------
    buyer: Delivering 1 parts to storage. storage stock is 1 parts now.
    Active Container of buyer: <storage: 1 parts in stock>
    --- Step 5: -----------------------------------------------
    buyer: Ready to draw resources
    buyer: Drawing 3 EUR from cashbox. cashbox has 4 EUR left now.
    Active Container of buyer: <cashbox: 4 EUR in stock>
    --- Step 6: -----------------------------------------------
    buyer: Conversion in progress, 2 steps left.
    Active Container of buyer: None
    --- Step 7: -----------------------------------------------
    buyer: Conversion in progress, 1 steps left.
    Active Container of buyer: None
    --- Step 8: -----------------------------------------------
    buyer: Delivering 1 parts to storage. storage stock is 2 parts now.
    Active Container of buyer: <storage: 2 parts in stock>
    --- Step 9: -----------------------------------------------
    buyer: Ready to draw resources
    buyer: Drawing 3 EUR from cashbox. cashbox has 1 EUR left now.
    Active Container of buyer: <cashbox: 1 EUR in stock>
    --- Step 10: -----------------------------------------------
    buyer: Conversion in progress, 2 steps left.
    Active Container of buyer: None
    --- Step 11: -----------------------------------------------
    buyer: Conversion in progress, 1 steps left.
    Active Container of buyer: None
    --- Step 12: -----------------------------------------------
    buyer: Delivering 1 parts to storage. storage stock is 3 parts now.
    Active Container of buyer: <storage: 3 parts in stock>
    --- Step 13: -----------------------------------------------
    buyer: Ready to draw resources
    buyer: Cannot draw 3 EUR from cashbox, only 1 left.
    Active Container of buyer: None
    --- Break condition met, simulation finished. ---------------
    Final state after 13 steps:
    <cashbox: 1 EUR in stock>
    <storage: 3 parts in stock>

You can export the simulation graph in the DOT graph language (see
`http://www.graphviz.org/ <http://www.graphviz.org/>`_):

::

    >>> s.save_dot("part_buyer.dot")
    Writing DOT file.
    digraph {
        graph [size=5] ;
        node [fontsize=10, fontname="Bitstream Vera Sans"] ;
        "cashbox" [shape=box];
        "cashbox" -> "buyer" ;
        "storage" [shape=box];
        "buyer" -> "storage" ;
    }
    <BLANKLINE>

Clean up:

::

    >>> import os
    >>> os.remove("part_buyer.dot")

The file 'making\_cakes.py' shows a more elaborate example. It is
included in the ZIP archive and will be installed in
'share/doc/stepsim/examples'.

License
-------

StepSim is licensed under the GPL. See the file COPYING for details.

Author
------

(c) Florian Berger
"""

distutils.core.setup(name = "stepsim",
                     version = VERSION,
                     author = "Florian Berger",
                     author_email = "fberger@florian-berger.de",
                     url = "http://florian-berger.de/software/stepsim/",
                     description = "StepSim - Python Step-based Simulation Package",
                     long_description = LONG_DESCRIPTION,
                     license = "GPL",
                     py_modules = ["stepsim"],
                     packages = [],
                     requires = [],
                     provides = ["stepsim"],
                     scripts = [],
                     data_files = [("share/doc/stepsim/examples", ['making_cakes.py']),
                                   ("share/doc/stepsim", ['COPYING', 'README', 'NEWS'])])
