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

"""StepSim - Python Step-based Simulation Package

   Copyright 2011 Florian Berger <fberger@florian-berger.de>

   StepSim computes step-by-step simulations of a graph of containers and
   converterts.

   First create the containers:

   >>> import stepsim
   >>> cashbox = stepsim.Container("cashbox", "EUR", 10)
   >>> storage = stepsim.Container("storage", "parts")

   Then create a converter and set up the draw-deliver-ratio:

   >>> buyer = stepsim.Converter("buyer", 2, (cashbox, 3), (storage, 1))
   Adding source 'cashbox', drawing 3 EUR per step.

   Now we are ready to create a simulation:

   >>> s = stepsim.Simulation()
   >>> s.add_converter(buyer)
   Adding converter 'buyer' to simulation.
   Adding containers ['cashbox', 'storage'] to simulation.
   >>> s
   <Simulation consisting of [<buyer: converting from ['cashbox'] to storage>]>

   You can now step through the simulation or simply let it run until an end
   condition is satisfied:

   >>> s.run(lambda : not buyer.last_step_successful)
   Starting simulation.
   Next step.
   buyer ready to draw resources
   buyer drawing 3 EUR from cashbox. cashbox has 7 EUR left now.
   Next step.
   buyer conversion in progress, 2 steps left.
   Next step.
   buyer conversion in progress, 1 steps left.
   Next step.
   buyer delivering 1 parts to storage. storage stock is 1 parts now.
   Next step.
   buyer ready to draw resources
   buyer drawing 3 EUR from cashbox. cashbox has 4 EUR left now.
   Next step.
   buyer conversion in progress, 2 steps left.
   Next step.
   buyer conversion in progress, 1 steps left.
   Next step.
   buyer delivering 1 parts to storage. storage stock is 2 parts now.
   Next step.
   buyer ready to draw resources
   buyer drawing 3 EUR from cashbox. cashbox has 1 EUR left now.
   Next step.
   buyer conversion in progress, 2 steps left.
   Next step.
   buyer conversion in progress, 1 steps left.
   Next step.
   buyer delivering 1 parts to storage. storage stock is 3 parts now.
   Next step.
   buyer ready to draw resources
   buyer: cannot draw 3 EUR from cashbox, only 1 left.
   Simulation finished.
   Final state: [<cashbox: 1 EUR in stock>, <storage: 3 parts in stock>]
   >>>
"""

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
           type must be a string describing the type of units (kg, €, etc.).
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

        return "<{}: {} {} in stock>".format(self.name, self.stock, self.type)

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

        print("Adding source '{}', drawing {} {} per step.".format(container.name,
                                                                   units,
                                                                   container.type))

        return

    def step(self):
        """Draw units from source Containers and feed units to target Container.
        """

        if self.countdown == -1:

            print("{} ready to draw resources".format(self.name))

            # Hoping for the best this time!
            #
            self.last_step_successful = True

            # First check if enough resources are available
            #
            for tuple in self.source_tuples_list:

                if tuple[0].stock < tuple[1]:

                    print("{}: cannot draw {} {} from {}, only {} left.".format(self.name,
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

            print("{} conversion in progress, {} steps left.".format(self.name,
                                                                     self.countdown))

            self.countdown = self.countdown - 1

        return

    def __repr__(self):
        """Readable string representation.
        """

        return "<{}: converting from {} to {}>".format(self.name,
                                                       str(list(map(lambda x: x[0].name, self.source_tuples_list))),
                                                       self.target_units_tuple[0].name)

class Simulation:
    """A Simulation wraps a graph of Containers and Converters and runs the simulation step-by-step.
    """

    def __init__(self):
        """Initialise.
        """

        # TODO: Liste von Converters gleich als Parameter übergeben? Mit *(?)?
        # TODO: graph export, e.g. graphviz DOT

        self.converter_list = []
        self.container_list = []

        return

    def add_converter(self, converter):
        """Add a Converter to the simulation.
        """

        self.converter_list.append(converter)

        print("Adding converter '{}' to simulation.".format(converter.name))

        for container in map(lambda x: x[0], converter.source_tuples_list):

            if container not in self.container_list:

                self.container_list.append(container)

        if converter.target_units_tuple[0] not in self.container_list:

            self.container_list.append(converter.target_units_tuple[0])

        print("Adding containers {} to simulation.".format(list(map(lambda x: x.name, self.container_list))))

        return

    def step(self):
        """Advance one simulation step.
        """

        print("Next step.")

        for converter in self.converter_list:

            converter.step()

        return

    def run(self, break_check, delay = 0):
        """Run the simulation until an Exception occurs.
           break_check must be a function. The simulation will be stopped when in returns True.
           delay is the time in seconds to pause between steps.
        """

        print("Starting simulation.")

        while not break_check():

            self.step()

            time.sleep(delay)

        print("Simulation finished.")
        print("Final state: {}".format(self.container_list))

        return

    def __repr__(self):
        """Readable string representation.
        """

        return "<Simulation consisting of {}>".format(str(self.converter_list))
