"""Making Cakes - A StepSim Example

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

# Work started on 09 Feb 2011.

import stepsim
import logging

# TODO: realistic times (steps = minutes)

def main():

    # Set up logger output
    #
    logger = logging.getLogger("stepsim")
    logger.addHandler(logging.StreamHandler())

    # For more verbose output use logging.DEBUG
    #
    logger.setLevel(logging.INFO)

    # Let's try a more complicated example and make a cake.

    cashbox = stepsim.Container("Cashbox", "EUR", 100.0)
    butter = stepsim.Container("Butter", "gram")
    sugar = stepsim.Container("Sugar", "gram")
    eggs = stepsim.Container("Eggs", "eggs")
    flour = stepsim.Container("Flour", "gram")
    milk = stepsim.Container("Milk", "ml")
    dough = stepsim.Container("Dough", "gram")
    cakes = stepsim.Container("Cakes", "cakes")

    # Prices in Germany as of Feb 2011. :-)
    #
    butter_buyer = stepsim.Converter("Butter Buyer", 1, (cashbox, 1.35), (butter, 250))
    sugar_buyer = stepsim.Converter("Sugar Buyer", 1, (cashbox, 1.19), (sugar, 1000))
    eggs_buyer = stepsim.Converter("Eggs Buyer", 1, (cashbox, 2.14), (eggs, 6))
    flour_buyer = stepsim.Converter("Flour Buyer", 1, (cashbox, 0.69), (flour, 1000))
    milk_buyer = stepsim.Converter("Milk Buyer", 1, (cashbox, 0.95), (milk, 1000))

    dough_maker_slow = stepsim.Converter("Dough Maker Slow", 5, (butter, 250), (dough, 1000))
    dough_maker_slow.draw_from(sugar, 50)
    dough_maker_slow.draw_from(eggs, 6)
    dough_maker_slow.draw_from(flour, 500)
    dough_maker_slow.draw_from(milk, 125)

    dough_maker_fast = stepsim.Converter("Dough Maker Fast", 2, (butter, 250), (dough, 1000))
    dough_maker_fast.draw_from(sugar, 50)
    dough_maker_fast.draw_from(eggs, 6)
    dough_maker_fast.draw_from(flour, 500)
    dough_maker_fast.draw_from(milk, 125)

    oven_1 = stepsim.Converter("Oven 1", 9, (dough, 1000), (cakes, 1))
    #oven_2 = stepsim.Converter("Oven 2", 9, (dough, 1000), (cakes, 1))

    making_cakes = stepsim.Simulation(butter_buyer,
                                      sugar_buyer,
                                      eggs_buyer,
                                      flour_buyer,
                                      milk_buyer)

    making_cakes.add_converter(dough_maker_slow)
    making_cakes.add_converter(dough_maker_fast)

    making_cakes.add_converter(oven_1)
    #making_cakes.add_converter(oven_2)

    # Run simulation
    #
    making_cakes.run(lambda : cakes.stock == 10, delay = 0.5)

    # Or try:
    #
    #making_cakes.run(lambda : making_cakes.step_counter == 1000)

    making_cakes.save_dot("making_cakes.dot")

if __name__ == "__main__":

        main()
