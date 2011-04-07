"""StepSim - Python Step-based Simulation Package

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

# Work started on 05 Feb 2011.

# NOTE: in string formatting operations, I use "{1}" instead of "{}" to be
# compatible with Python < 3.1

import time
import logging
import re

LOGGER = logging.getLogger("stepsim")

try:
    LOGGER.addHandler(logging.NullHandler())

except AttributeError:

    # Fallback for Python < 3.1
    #
    class NullHandler(logging.Handler):

        def emit(self, record):
            pass

    LOGGER.addHandler(NullHandler())

def log_to_stderr():
    """Convenience function. Call this to activate logging to stderr.
    """

    LOGGER.addHandler(logging.StreamHandler())

    # For less verbose output use logging.INFO
    #
    LOGGER.setLevel(logging.DEBUG)

    return

def log_to_stdout():
    """Convenience function. Call this to activate logging to stdout.
    """

    from sys import stdout

    LOGGER.addHandler(logging.StreamHandler(stdout))

    # For less verbose output use logging.INFO
    #
    LOGGER.setLevel(logging.DEBUG)

    return

class Container:
    """A Container stores a discrete number of units of a single resource.

       Attributes:

       Container.name
           A string.

       Container.stock
           An integer value representing the number of units in stock.

       Container.type
           A string value representing the type of storage.
    """

    def __init__(self, name, type, stock = 0):
        """Initalise.
           type must be a string describing the type of units (kg, EUR, etc.).
           stock is the initial stock and must be an integer.
        """

        self.name = name
        self.type = type
        self.stock = stock

        return

    def draw(self, units):
        """Draw a number of units from the Container.
           Returns the number of units actually drawn.
        """

        if self.stock >= units:

            self.stock = self.stock - units

            return units

        else:
            units_left = self.stock

            self.stock = 0

            return units_left

    def deliver(self, units):
        """Deliver a number of units to this container.
        """

        self.stock = self.stock + units

        return

    def __repr__(self):
        """Readable string representation.
        """

        return "<{0}: {1} {2} in stock>".format(self.name, self.stock, self.type)

class Converter:
    """A Converter drains units from one or more Containers and stores the result in another Container.

       Attributes:

       Converter.name
           A string holding the name of this Converter.

       Converter.steps
           Interger holding the number of steps needed to manufacture the output.

       Converter.last_step_successful
           Boolean flag denoting whether the last step (draw / deliver) worked out.

       Converter.countdown
           A counter to implement a three-state state machine:
           -1 : ready to draw resources
           >0 : resources drawn, conversion in progress
            0 : conversion ready, delivering

       Converter.active_container
           The last Container that this Converter has just drawn from or
           delivered to. None if no Container has been accessed in the current
           step.
    """

    # TODO: implement adaptive flexible converters that draw as much as they can (or as much as they can get, given less resources) while keeping the ratio
    # TODO: count (active) steps for accounting

    def __init__(self, name, steps, source_units_tuple, target_units_tuple):
        """Initialise.
           source_units_tuple, target_units_tuple are tuples of (Container,
           integer) giving a source and a target container and the number of
           units to draw / deliver.
        """

        self.name = name

        self.steps = steps

        self.target_units_tuple = target_units_tuple

        self.source_tuples_list = []
        self.draw_from(source_units_tuple[0], source_units_tuple[1])

        self.last_step_successful = True

        # countdown is used as a three-state state machine:
        # -1 : ready to draw resources
        # >0 : resources drawn, conversion in progress
        #  0 : conversion ready, delivering
        #
        self.countdown = -1

        self.active_container = None

        return

    def draw_from(self, container, units):
        """Add a new source container to this Converter.
        """

        self.source_tuples_list.append((container, units))

        msg = "{0}: Adding source '{1}', drawing {2} {3} per step."
        LOGGER.debug(msg.format(self.name, container.name, units, container.type))

        return

    def step(self):
        """Draw units from source Containers and feed units to target Container.
        """

        if self.countdown == -1:

            LOGGER.debug("{0}: Ready to draw resources".format(self.name))

            # Hoping for the best this time!
            #
            self.last_step_successful = True

            # First check if enough resources are available
            #
            for tuple in self.source_tuples_list:

                if tuple[0].stock < tuple[1]:

                    LOGGER.debug("{0}: Cannot draw {1} {2} from {3}, only {4} left.".format(self.name,
                                                                                     tuple[1],
                                                                                     tuple[0].type,
                                                                                     tuple[0].name,
                                                                                     tuple[0].stock))

                    self.last_step_successful = False

                    # No active Container
                    #
                    self.active_container = None

            if self.last_step_successful:

                # Loop again, drawing from all source Containers
                #
                for tuple in self.source_tuples_list:

                    units_drawn = tuple[0].draw(tuple[1])

                    # Only the very last container will persist in
                    # self.active_container
                    #
                    self.active_container = tuple[0]

                    if units_drawn == tuple[1]:

                        msg = "{0}: Drawing {1} {2} from {3}. {3} has {4} {2} left now."
                        LOGGER.info(msg.format(self.name,
                                    tuple[1],
                                    tuple[0].type,
                                    tuple[0].name,
                                    tuple[0].stock))

                    else:
                        # Due to the test above, this should not happen
                        #
                        msg = "{0}: Could only draw {1} {2} instead of {3} {2} from {4}."
                        LOGGER.debug(msg.format(self.name,
                                         units_drawn,
                                         tuple[0].type,
                                         tuple[1],
                                         tuple[0].name))

                        self.last_step_successful = False

                # All good?
                #
                if self.last_step_successful:

                    self.countdown = self.steps

        elif self.countdown == 0:

            # Still going?
            #
            if self.last_step_successful:

                # Then deliver to target Container
                #
                self.target_units_tuple[0].deliver(self.target_units_tuple[1])

                # Overwriting possible Container just drawn from
                #
                self.active_container = self.target_units_tuple[0]

                msg = "{0}: Delivering {1} {2} to {3}. {3} stock is {4} {2} now."
                LOGGER.info(msg.format(self.name,
                                       self.target_units_tuple[1],
                                       self.target_units_tuple[0].type,
                                       self.target_units_tuple[0].name,
                                       self.target_units_tuple[0].stock))

                self.countdown = -1

        elif self.countdown > 0:

            LOGGER.info("{0}: Conversion in progress, {1} steps left.".format(self.name,
                                                                              self.countdown))

            self.countdown = self.countdown - 1

            # No active Container
            #
            self.active_container = None

        LOGGER.debug("Active Container of {0}: {1}".format(self.name,
                                                           self.active_container))

        return

    def __repr__(self):
        """Readable string representation.
        """

        return "<{0}: converting from {1} to {2}>".format(self.name,
                                                          str(list(map(lambda x: x[0].name, self.source_tuples_list))),
                                                          self.target_units_tuple[0].name)

class Simulation:
    """A Simulation wraps a graph of Containers and Converters and runs the simulation step-by-step.

       Attributes:

       Simulation.converter_dict
           A dict of Converters whose step() function will be called in
           Simulation.step(), indexed by their names.

       Simulation.container_dict
           A convenience dict of Containers connected to the Converters, indexed
           by their names.

       Simulation.step_counter
           An integer counting the steps that have been taken.
    """

    def __init__(self, *converters):
        """Initialise.
        """

        self.converter_dict = {}
        self.container_dict = {}
        self.step_counter = 0

        # Use the default procedure for each converter
        #
        for converter in converters:
            self.add_converter(converter)

        return

    def add_converter(self, converter):
        """Add a Converter to the simulation.
        """

        self.converter_dict[converter.name] = converter

        LOGGER.debug("Adding converter '{0}' to simulation.".format(converter.name))

        self.rebuild_container_dict()

        return

    def remove_converter(self, name):
        """Remove a Converter from the simulation by its name.
           If name is not found in Simulation.converter_dict, no action will be
           taken.
        """

        if name in self.converter_dict.keys():

            LOGGER.debug("Deleting converter '{0}' from simulation.".format(name))

            del self.converter_dict[name]

            self.rebuild_container_dict()

        else:
            LOGGER.debug("'{0}' not found.".format(name))

        return

    def rebuild_container_dict(self):
        """Rebuild Simulation.container_dict from registered converters.
        """

        self.container_dict = {}

        for converter in self.converter_dict.values():

            for container in [x[0] for x in converter.source_tuples_list]:

                if container not in self.container_dict.values():

                    self.container_dict[container.name] = container

            if converter.target_units_tuple[0] not in self.container_dict.values():

                container = converter.target_units_tuple[0]

                self.container_dict[container.name] = container

        LOGGER.debug("Current containers: {0}".format(list(self.container_dict.keys())))

        return


    def check(self, condition_string):
        """Convenience function to check if a condition is True right now.

           condition_string must be a string "NAME OPERATOR VALUE" where

           - NAME is a valid key to Simulation.container_dict
           - OPERATOR is one of ("<", ">", ">=", "<=", "==", "!=")
           - VALUE is a number

           Returns True if the condition is true, False otherwise.
        """

        # Taken from my Projektmanager game on 7 April 2011

        match = re.match(r"^([^<>=!]+?)\s*([<>=!]{1,2})\s*(\w+)\s*$",
                         condition_string)

        if match is not None and len(match.groups()) == 3:

            container, operator, value = match.groups()

            if container not in self.container_dict.keys():

                raise KeyError("break condition container '{0}' not in Simulation.container_dict".format(container))

            # The regex above will let an invalid "<<" etc. pass, so check again
            #
            if operator not in ("<", ">", ">=", "<=", "==", "!="):

                raise SyntaxError("break condition operator '{0}' is invalid".format(operator))

            if not value.isnumeric():

                raise TypeError("break condition value '{0}' is not a number".format(value))

            # Still here? Then everything should be fine.
            #
            return eval('self.container_dict["{0}"].stock {1} {2}'.format(container,
                                                                          operator,
                                                                          value))

        else:
            raise SyntaxError("invalid condition string: '{0}'".format(condition_string))


    def step(self):
        """Advance one simulation step.
        """

        for converter in self.converter_dict.values():

            converter.step()

        self.step_counter = self.step_counter + 1

        return

    def run(self, break_check, delay = 0):
        """Repeatedly run Simulation.step() until an Exception occurs.
           break_check must be a function. The simulation will be stopped when in returns True.
           delay is the time in seconds to pause between steps.
        """

        LOGGER.info("Starting simulation.")

        while not break_check():

            LOGGER.info("--- Step {0}: -----------------------------------------------".format(self.step_counter + 1))

            self.step()

            time.sleep(delay)

        LOGGER.info("--- Break condition met, simulation finished. ---------------")
        LOGGER.info("Final state after {0} steps:\n{1}".format(self.step_counter,
                                                               "\n".join([str(x) for x in self.container_dict.values()])))

        return

    def save_dot(self, filename, size = 5, fontsize = 10, fontname = "Bitstream Vera Sans"):
        """Export the simulation graph into the Graphviz DOT graph language.
           size, fontsize and fontname are DOT graph parameters.
           Use for example dot -Tpng graph.dot > graph.png to render.
           See http://www.graphviz.org/ for details.
        """

        dot_string_list = ["""digraph {{
    graph [size={0}] ;
    node [fontsize={1}, fontname="{2}"] ;
""".format(size, fontsize, fontname)]

        for converter in self.converter_dict.values():

            # First the source containers
            #
            for tuple in converter.source_tuples_list:

                shape_string = '    "{0}" [shape=box];\n'.format(tuple[0].name)

                if not shape_string in dot_string_list:

                    dot_string_list.append(shape_string)

                dot_string_list.append('    "{0}" -> "{1}" ;\n'.format(tuple[0].name,
                                                                       converter.name))

            # Then the target container
            #
            shape_string = '    "{0}" [shape=box];\n'.format(converter.target_units_tuple[0].name)

            if not shape_string in dot_string_list:

                dot_string_list.append(shape_string)

            dot_string_list.append('    "{0}" -> "{1}" ;\n'.format(converter.name,
                                                                   converter.target_units_tuple[0].name))

        dot_string_list.append("}\n")

        dot_string = "".join(dot_string_list)

        LOGGER.info("Writing DOT file.")
        LOGGER.debug(dot_string)

        file = open(filename, "w")
        file.write(dot_string)
        file.close()

    def __repr__(self):
        """Readable string representation.
        """

        return "<Simulation consisting of {0}>".format(list(self.converter_dict.values()))
