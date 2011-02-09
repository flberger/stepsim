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
    """

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

        return

    def draw_from(self, container, units):
        """Add a new source container to this Converter.
        """

        self.source_tuples_list.append((container, units))

        print("{0}: adding source '{1}', drawing {2} {3} per step.".format(self.name,
                                                                           container.name,
                                                                           units,
                                                                           container.type))

        return

    def step(self):
        """Draw units from source Containers and feed units to target Container.
        """

        if self.countdown == -1:

            print("{0} ready to draw resources".format(self.name))

            # Hoping for the best this time!
            #
            self.last_step_successful = True

            # First check if enough resources are available
            #
            for tuple in self.source_tuples_list:

                if tuple[0].stock < tuple[1]:

                    print("{0}: cannot draw {1} {2} from {3}, only {4} left.".format(self.name,
                                                                                     tuple[1],
                                                                                     tuple[0].type,
                                                                                     tuple[0].name,
                                                                                     tuple[0].stock))

                    self.last_step_successful = False

            if self.last_step_successful:

                # Loop again, drawing from all source Containers
                #
                for tuple in self.source_tuples_list:

                    units_drawn = tuple[0].draw(tuple[1])

                    if units_drawn == tuple[1]:

                        msg = "{0} drawing {1} {2} from {3}. {3} has {4} {2} left now."

                        print(msg.format(self.name,
                                         tuple[1],
                                         tuple[0].type,
                                         tuple[0].name,
                                         tuple[0].stock))

                    else:
                        # Due to the test above, this should not happen
                        #
                        msg = "{0} could only draw {1} {2} instead of {3} {2} from {4}."

                        print(msg.format(self.name,
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

                print("{0} delivering {1} {2} to {3}. {3} stock is {4} {2} now.".format(self.name,
                                                         self.target_units_tuple[1],
                                                         self.target_units_tuple[0].type,
                                                         self.target_units_tuple[0].name,
                                                         self.target_units_tuple[0].stock))

                self.countdown = -1

        elif self.countdown > 0:

            print("{0} conversion in progress, {1} steps left.".format(self.name,
                                                                       self.countdown))

            self.countdown = self.countdown - 1

        return

    def __repr__(self):
        """Readable string representation.
        """

        return "<{0}: converting from {1} to {2}>".format(self.name,
                                                          str(list(map(lambda x: x[0].name, self.source_tuples_list))),
                                                          self.target_units_tuple[0].name)

class Simulation:
    """A Simulation wraps a graph of Containers and Converters and runs the simulation step-by-step.
    """

    def __init__(self):
        """Initialise.
        """

        # TODO: Liste von Converters gleich als Parameter uebergeben? Mit *(?)?

        self.converter_list = []
        self.container_list = []
        self.step_counter = 0

        return

    def add_converter(self, converter):
        """Add a Converter to the simulation.
        """

        self.converter_list.append(converter)

        print("Adding converter '{0}' to simulation.".format(converter.name))

        for container in map(lambda x: x[0], converter.source_tuples_list):

            if container not in self.container_list:

                self.container_list.append(container)

        if converter.target_units_tuple[0] not in self.container_list:

            self.container_list.append(converter.target_units_tuple[0])

        print("Current containers: {0}".format(list(map(lambda x: x.name, self.container_list))))

        return

    def step(self):
        """Advance one simulation step.
        """

        for converter in self.converter_list:

            converter.step()

        return

    def run(self, break_check, delay = 0):
        """Run the simulation until an Exception occurs.
           break_check must be a function. The simulation will be stopped when in returns True.
           delay is the time in seconds to pause between steps.
        """

        print("Starting simulation.")

        self.step_counter = 0

        while not break_check():

            self.step_counter = self.step_counter + 1

            print("Step {0}:".format(self.step_counter))

            self.step()

            time.sleep(delay)

        print("Break condition met, simulation finished.")
        print("Final state after {0} steps: {1}".format(self.step_counter,
                                                      self.container_list))

        return

    def save_dot(self, filename):
        """Export the simulation graph into the Graphviz DOT graph language.
           See http://www.graphviz.org/ for details.
        """

        dot_string_list = ["digraph {\n"]

        for converter in self.converter_list:

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

        print("Writing DOT file:\n{0}".format(dot_string))

        file = open(filename, "w")
        file.write(dot_string)
        file.close()

    def __repr__(self):
        """Readable string representation.
        """

        return "<Simulation consisting of {0}>".format(str(self.converter_list))
