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
import os.path

VERSION = "0.5.1"
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
    >>> stepsim.loglevel("debug")

Now create some containers:

::

    >>> cashbox = stepsim.Container("cashbox", "EUR", 10)
    >>> storage = stepsim.Container("storage", "parts")

Then create a converter and set up the draw-deliver-ratio:

::

    >>> buyer = stepsim.Converter("buyer", 2, (cashbox, 3), (storage, 1))
    buyer: Adding source 'cashbox', drawing 3 EUR per step.

From any list of converters, we can get a list of simulation milestones
that lead to an end condition (without actually running a simulation):

::

    >>> stepsim.loglevel("info")
    >>> stepsim.milestones("storage == 3", [buyer])
    ------------------------------
    Milestones to achieve storage == 3:
    <BLANKLINE>
    Milestone:
    9 EUR in cashbox (10 in stock, 111.11%)
    total: 111.11%
    <BLANKLINE>
    Milestone:
    3.0 parts in storage (0 in stock, 0.0%)
    total: 0.0%
    ------------------------------
    [<Milestone (cashbox: 9) 111.11%>, <Milestone (storage: 3.0) 0.0%>]

Let's create a simulation:

::

    >>> stepsim.loglevel("debug")
    >>> s = stepsim.Simulation(buyer)
    Adding converter 'buyer' to simulation.
    Current containers: ['cashbox', 'storage']
    >>> s
    <Simulation consisting of [<buyer: converting from ['cashbox'] to storage>]>

The step() method is used to advance the simulation by one step:

::

    >>> stepsim.loglevel("info")
    >>> s.step()
    buyer: Drawing 3 EUR from cashbox.

It is also possible to check conditions inbetween. The simulation
instance offers a convenience method to do this using a string
describing the condition:

::

    >>> s.check("cashbox == 10")
    False
    >>> s.check("cashbox != 10")
    True
    >>> s.check("storage >= 0")
    True

It is possible to evaluate how many steps it will take until a certain
condition is met:

::

    >>> stepsim.be_quiet()
    >>> s.estimate_finish("storage == 2", 100)
    8

Behind the scenes, this will run a copy of the simulation. A maximum
step value will prevent hanging on impossible conditions:

::

    >>> s.estimate_finish("cashbox < 1", 100)
    100

Whe you remove a converter, its last step will be reverted. Note that
this does not rewind the simulation step counter.

::

    >>> stepsim.log_to_stdout()
    >>> stepsim.loglevel("debug")
    >>> s.step()
    buyer: Conversion in progress, 2 steps left.
    Active Container of buyer: None
    >>> s.remove_converter("buyer")
    reverting last draw from 'buyer'
    buyer: returning 3 EUR to cashbox.
    Removing converter 'buyer' from simulation.
    Current containers: []

You can now step on through the simulation or simply let it run from the
current state until an end condition is satisfied. In this case we let
it run until the buyer can not buy any more parts:

::

    >>> s.add_converter(buyer)
    Adding converter 'buyer' to simulation.
    Current containers: ['cashbox', 'storage']
    >>> s.run(lambda : not buyer.last_step_successful)
    Starting simulation.
    --- Step 3: -----------------------------------------------
    buyer: Ready to draw resources
    buyer: Drawing 3 EUR from cashbox.
    cashbox has 7 EUR left now.
    Active Container of buyer: <cashbox: 7 EUR in stock>
    --- Step 4: -----------------------------------------------
    buyer: Conversion in progress, 2 steps left.
    Active Container of buyer: None
    --- Step 5: -----------------------------------------------
    buyer: Conversion in progress, 1 steps left.
    Active Container of buyer: None
    --- Step 6: -----------------------------------------------
    buyer: Delivering 1 parts to storage.
    storage stock is 1 parts now.
    Active Container of buyer: <storage: 1 parts in stock>
    --- Step 7: -----------------------------------------------
    buyer: Ready to draw resources
    buyer: Drawing 3 EUR from cashbox.
    cashbox has 4 EUR left now.
    Active Container of buyer: <cashbox: 4 EUR in stock>
    --- Step 8: -----------------------------------------------
    buyer: Conversion in progress, 2 steps left.
    Active Container of buyer: None
    --- Step 9: -----------------------------------------------
    buyer: Conversion in progress, 1 steps left.
    Active Container of buyer: None
    --- Step 10: -----------------------------------------------
    buyer: Delivering 1 parts to storage.
    storage stock is 2 parts now.
    Active Container of buyer: <storage: 2 parts in stock>
    --- Step 11: -----------------------------------------------
    buyer: Ready to draw resources
    buyer: Drawing 3 EUR from cashbox.
    cashbox has 1 EUR left now.
    Active Container of buyer: <cashbox: 1 EUR in stock>
    --- Step 12: -----------------------------------------------
    buyer: Conversion in progress, 2 steps left.
    Active Container of buyer: None
    --- Step 13: -----------------------------------------------
    buyer: Conversion in progress, 1 steps left.
    Active Container of buyer: None
    --- Step 14: -----------------------------------------------
    buyer: Delivering 1 parts to storage.
    storage stock is 3 parts now.
    Active Container of buyer: <storage: 3 parts in stock>
    --- Step 15: -----------------------------------------------
    buyer: Ready to draw resources
    buyer: Cannot draw 3 EUR from cashbox, only 1 left.
    Active Container of buyer: None
    --- Break condition met, simulation finished. ---------------
    Final state after 15 steps:
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

Florian Berger
"""

distutils.core.setup(name = "stepsim",
                     version = VERSION,
                     author = "Florian Berger",
                     author_email = "fberger@florian-berger.de",
                     url = "http://florian-berger.de/en/software/stepsim",
                     description = "StepSim - Python Step-based Simulation Package",
                     long_description = LONG_DESCRIPTION,
                     license = "GPL",
                     py_modules = ["stepsim"],
                     packages = [],
                     requires = [],
                     provides = ["stepsim"],
                     scripts = [],
                     data_files = [(os.path.join("share", "doc", "stepsim", "examples"),
                                    ['making_cakes.py']),
                                   (os.path.join("share", "doc", "stepsim"),
                                    ['COPYING', 'README', 'NEWS'])])
