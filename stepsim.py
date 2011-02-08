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

   >>> buyer = stepsim.Converter("buyer", storage, 1)
   >>> buyer.draw_from(cashbox, 3)
   Adding source 'cashbox', drawing 3 EUR per step.

   Now we are ready to create a simulation:

   >>> s = stepsim.Simulation()
   >>> s.add_converter(buyer)
   Adding converter 'buyer' to simulation.

   You can step through simulations or simply let it run until an Exception
   occurs:

   >>> s.run()
   Starting simulation.
   Next step.
   buyer drawing 3 EUR from cashbox. cashbox has 7 EUR left now.
   buyer delivering 1 parts to storage. storage stock is 1 parts now.
   Next step.
   buyer drawing 3 EUR from cashbox. cashbox has 4 EUR left now.
   buyer delivering 1 parts to storage. storage stock is 2 parts now.
   Next step.
   buyer drawing 3 EUR from cashbox. cashbox has 1 EUR left now.
   buyer delivering 1 parts to storage. storage stock is 3 parts now.
   Next step.
   Exception while executing step in <buyer: converting from ['cashbox'] to storage>
   Simulation finished.
   >>>
"""

class Container:
    """A Container stores a discrete number of units of a single ressource.

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
    """

    # TODO: extra speed parameter? To be able to speed up / slow down

    def __init__(self, name, target, units):
        """Initialise.
           target must be an instance of Container.
           units must be an integer.
        """

        self.name = name
        self.target_units_tuple = (target, units)
        self.source_tuples_list = []

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

        # TODO: test whether the step can be completed at all
        # TODO: noop until step can be completed

        # First draw from all source Containers
        #
        for tuple in self.source_tuples_list:

            units_drawn = tuple[0].draw(tuple[1])

            if units_drawn == tuple[1]:

                print("{0} drawing {1} {2} from {3}. {3} has {4} {2} left now.".format(self.name,
                                                        tuple[1],
                                                        tuple[0].type,
                                                        tuple[0].name,
                                                        tuple[0].stock))

            else:
                raise Exception("Not enough units from {}".format(tuple[0].name))

        # Then deliver to target Container
        #
        self.target_units_tuple[0].deliver(self.target_units_tuple[1])

        print("{0} delivering {1} {2} to {3}. {3} stock is {4} {2} now.".format(self.name,
                                                 self.target_units_tuple[1],
                                                 self.target_units_tuple[0].type,
                                                 self.target_units_tuple[0].name,
                                                 self.target_units_tuple[0].stock))

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

        self.converter_list = []

        return

    def add_converter(self, converter):
        """Add a Converter to the simulation.
        """

        self.converter_list.append(converter)

        print("Adding converter '{}' to simulation.".format(converter.name))

        return

    def step(self):
        """Advance one simulation step.
           Will return True upon a successful step, False otherwise.
        """

        print("Next step.")

        for converter in self.converter_list:

            try:

                converter.step()

            except:
                print("Exception while executing step in {}".format(str(converter)))

                return False

        return True

    def run(self):
        """Run the simulation until an Exception occurs.
        """

        print("Starting simulation.")

        while self.step():
            pass

        print("Simulation finished.")

        return
