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

# TODO: name simulations, and when logging, put the name of the simulations in front of the message
# TODO: GUI with Cairo-graph (http://cairographics.org/pycairo/) and Tkinter dialogs
# TODO: kompakterer Graph-Export: Converter mit gleicher Funktion zu einem Knoten zusammenfassen

# NOTE: in string formatting operations, I use "{1}" instead of "{}" to be compatible with Python < 3.1

import time
import logging
import re
import copy
from sys import stdout

VERSION = "0.5.7a"

LOGGER = logging.getLogger("stepsim")

LOGGER.setLevel(logging.WARNING)

try:
    LOGGER.addHandler(logging.NullHandler())

except AttributeError:

    class NullHandler(logging.Handler):
        """Fallback Handler for Python < 3.1
        """

        def emit(self, record):
            pass

    LOGGER.addHandler(NullHandler())

STDERR_FORMATTER = logging.Formatter("stepsim [%(levelname)s] %(funcName)s(): %(message)s (l.%(lineno)d)")

STDERR_HANDLER = logging.StreamHandler()
STDERR_HANDLER.setFormatter(STDERR_FORMATTER)

# No special formatter for STDOUT, less noise
#
STDOUT_HANLDER = logging.StreamHandler(stdout)

def log_to_stderr():
    """Convenience function. Call this to activate logging to stderr.
    """

    LOGGER.addHandler(STDERR_HANDLER)

    return

def log_to_stdout():
    """Convenience function. Call this to activate logging to stdout.
    """

    LOGGER.addHandler(STDOUT_HANLDER)

    return

def loglevel(level):
    """Convenienve function. Level must be one of ("critical", "error", "warning", "info", "debug").
    """

    # TODO: accept logging.CRITICAL etc. arguments

    level_dict = {"critical": logging.CRITICAL,
                  "error": logging.ERROR,
                  "warning": logging.WARNING,
                  "info": logging.INFO,
                  "debug": logging.DEBUG}

    if level not in level_dict.keys():

        raise Exception("invalid log level: {0}".format(level))

    else:
        LOGGER.setLevel(level_dict[level])

    return

def be_quiet():
    """Convenienve function. Call this to deactivate logging.
    """

    LOGGER.removeHandler(STDERR_HANDLER)
    LOGGER.removeHandler(STDOUT_HANLDER)

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

       Container.units_delivered
           The total number of units that have been delivered to this Container,
           including the default stock given in __init__().
           Warning: Container.units_delivered will not be updated if you change
           Container.stock directly.
    """

    def __init__(self, name, type, stock = 0):
        """Initalise.
           type must be a string describing the type of units ("kg", "EUR", etc.).
           stock is the initial stock and must be an integer.
        """

        self.name = name
        self.type = type
        self.stock = self.units_delivered = stock

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
           Use this method instead of changing Containter.stock directly if you
           want Container.units_delivered to be up to date.
        """

        self.stock = self.stock + units

        self.units_delivered = self.units_delivered + units

        return

    def __repr__(self):
        """Readable string representation.
        """

        return "<{0}: {1} {2} in stock>".format(self.name, self.stock, self.type)

class Converter:
    """A Converter drains units from one or more Containers and stores the result in another Container.

       Attributes:

       Converter.source_tuples_list
           A list of tuples (Container, integer) giving the source containers
           and the number of units to draw.

       Converter.target_units_tuple
           A tuple (Container, integer) giving the target container and the
           number of units to deliver.

       Converter.name
           A string holding the name of this Converter.

       Converter.steps
           Integer holding the number of steps needed to manufacture the output.

       Converter.last_step_successful
           Boolean flag denoting whether the last step (draw / deliver) worked out.

       Converter.countdown
           A counter to implement a three-state state machine:
           -1 : ready to draw resources
           > 0 : resources drawn, conversion in progress
            0 : conversion ready, delivering

       Converter.active_container
           The last Container that this Converter has just drawn from or
           delivered to. None if no Container has been accessed in the current
           step.

       Converter.max_units
           Integer giving the maximum number of units that this Converter will
           deliver. If max_units < 0, the Converter will deliver an unlimited
           number of units. Initially -1.

       Converter.units_delivered
           Integer, giving the number of units delivered so far. Initially zero.

       Converter.steps_cached
           Will cache the previous steps value when a temporary steps value
           is active. None if no temporary steps are active.
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

        self.max_units = -1

        self.units_delivered = 0

        # Cache for old steps value. See Converter.set_temporary_steps()
        #
        self.steps_cached = None

        # Countdown for temporary steps. See Converter.set_temporary_steps()
        #
        self._temp_countdown = -1

        return

    def draw_from(self, container, units):
        """Add a new source container to this Converter.
        """

        self.source_tuples_list.append((container, units))

        msg = "{0}: Adding source '{1}', drawing {2} {3} per step."
        LOGGER.debug(msg.format(self.name, container.name, units, container.type))

        return

    def draw(self):
        """Draw units from source Containers. To be called by Simulation.step().
           Return True if Converter.countdown == -1, False otherwise.
        """

        if (self.max_units >= 0
            and self.units_delivered >= self.max_units):

            msg = "{0}: delivered {1} units, max units is {2}, no action."

            LOGGER.info(msg.format(self.name,
                                   self.units_delivered,
                                   self.max_units))

            self.last_step_successful = False

            return False

        if self.countdown == -1:

            LOGGER.debug("{0}: Ready to draw resources".format(self.name))

            # Hoping for the best this time!
            #
            self.last_step_successful = True

            # First check if enough resources are available
            #
            for tuple in self.source_tuples_list:

                if tuple[0].stock < tuple[1]:

                    msg = "{0}: Cannot draw {1} {2} from {3}, only {4} left."

                    LOGGER.debug(msg.format(self.name,
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

                        LOGGER.info("{0}: Drawing {1} {2} from {3}.".format(self.name,
                                                                            tuple[1],
                                                                            tuple[0].type,
                                                                            tuple[0].name))

                        LOGGER.debug("{0} has {1} {2} left now.".format(tuple[0].name,
                                                                        tuple[0].stock,
                                                                        tuple[0].type))

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

                    # Python: this creates a copy
                    #
                    self.countdown = self.steps

                    LOGGER.debug("{0}: Setting processing countdown to {1} steps".format(self.name, self.countdown))

            LOGGER.debug("Active Container of {0}: {1}".format(self.name,
                                                               self.active_container))

            return True

        else:

            # self.countdown != -1
            #
            return False

    def process(self):
        """Process units by counting down Converter.countdown. To be called by Simulation.step().
           Return True if Converter.countdown > 0, False otherwise.
        """

        # Not checking max_units here since this method does not affect
        # containers.

        if self.countdown > 0:

            LOGGER.info("{0}: Conversion in progress, {1} steps left.".format(self.name,
                                                                              self.countdown))

            self.countdown = self.countdown - 1

            if self._temp_countdown > 0:

                self._temp_countdown -= 1

            elif self._temp_countdown == 0:

                self.end_temporary_steps()

            # No active Container
            #
            self.active_container = None

            LOGGER.debug("Active Container of {0}: {1}".format(self.name,
                                                               self.active_container))

            return True

        else:

            return False

    def deliver(self):
        """Feed units to target Container when processing is done. To be called by Simulation.step().
           Return True if Converter.countdown == 0, False otherwise.
        """

        # Not checking max_units here since the check in draw() will effectively
        # disable delivery.

        if self.countdown == 0:

            # Still going?
            # TODO: obsolete check? Remove?
            #
            if self.last_step_successful:

                # Then deliver to target Container
                #
                self.target_units_tuple[0].deliver(self.target_units_tuple[1])

                # Overwriting possible Container just drawn from
                #
                self.active_container = self.target_units_tuple[0]

                LOGGER.info("{0}: Delivering {1} {2} to {3}.".format(self.name,
                                                                     self.target_units_tuple[1],
                                                                     self.target_units_tuple[0].type,
                                                                     self.target_units_tuple[0].name))

                LOGGER.debug("{0} stock is {1} {2} now.".format(self.target_units_tuple[0].name,
                                                                self.target_units_tuple[0].stock,
                                                                self.target_units_tuple[0].type))

                self.countdown = -1

                # Check for finished temporary step change
                #
                if self._temp_countdown > 0:

                    self._temp_countdown -= 1

                if self._temp_countdown == 0:

                    LOGGER.info("restoring {0}.steps to {1}".format(self.name,
                                                                    self.steps_cached))

                    self.steps = self.steps_cached

                    self.steps_cached = None

                    self._temp_countdown = -1

                self.units_delivered += self.target_units_tuple[1]

                msg = "{0} has delivered {1} units since last reset."

                LOGGER.debug(msg.format(self.name, self.units_delivered))

            LOGGER.debug("Active Container of {0}: {1}".format(self.name,
                                                               self.active_container))

            return True

        else:

            return False

    def revert(self):
        """Undo the last draw action taken by this Converter.
           Usually called from Simulation.remove_converter().
        """

        LOGGER.info("reverting last draw from '{0}'".format(self.name))

        if self.countdown >= 0:

            # This time, deliver to source Containers
            #
            for tuple in self.source_tuples_list:

                LOGGER.info("{0}: returning {1} {2} to {3}.".format(self.name,
                                                                    tuple[1],
                                                                    tuple[0].type,
                                                                    tuple[0].name))

                units_drawn = tuple[0].deliver(tuple[1])

        self.countdown = -1

        return

    def set_max_units(self, units):
        """Set the maximum number of units that this Converter will deliver.
           This will reset Converter.units_delivered.
        """

        self.max_units = units

        self.units_delivered = 0

        # Let's give it a fresh start
        #
        self.last_step_successful = True

        LOGGER.debug("{0}: setting max_units to {1}".format(self.name, units))

        return

    def set_temporary_steps(self, value, duration):
        """Set Converter.steps to `value` for `duration` steps.

           Will return True if the steps could be set successfully, False when
           a temporary value is already active.
        """

        # The actual work will be done in Converter.process()

        if self.steps_cached is not None:

            msg = "{0}: {1} steps of temporary value {2} pending, not setting steps"

            LOGGER.warning(msg.format(self.name,
                                      self._temp_countdown,
                                      self.steps))

            return False

        LOGGER.info("{0}: setting steps = {1} for {2} steps".format(self.name,
                                                                    value,
                                                                    duration))

        # Python: this creates a copy
        #
        self.steps_cached = self.steps

        self.steps = value

        # Countdown for temporary steps.
        #
        self._temp_countdown = duration

        # As step countdowns may take a while, make it effect the current
        # countdown at once.
        #
        if self.countdown > -1:

            self.countdown = self.steps - (self.steps_cached - self.countdown)

            if self.countdown < -1:

                self.countdown = -1

        LOGGER.info("{0}: setting remaining countdown to {1}".format(self.name,
                                                                     self.countdown))

        return True

    def end_temporary_steps(self):
        """Reset any temporary step setting and restore the previous step value.
        """

        if self.steps_cached is not None:

            LOGGER.info("restoring {0}.steps to {1}".format(self.name,
                                                            self.steps_cached))

            self.steps = self.steps_cached

            self.steps_cached = None

            # We do not log how much time has passed, so we restore to the
            # full old step value.
            # TODO: This actually prolongs the conversion. Replace with logging of steps.
            #
            self.countdown = self.steps

            LOGGER.info("{0}: setting remaining countdown to {1}".format(self.name,
                                                                         self.countdown))

            self._temp_countdown = -1

        return

    def __repr__(self):
        """Readable string representation.
        """

        return "<{0}: converting from {1} to {2}>".format(self.name,
                                                          str(list(map(lambda x: x[0].name, self.source_tuples_list))),
                                                          self.target_units_tuple[0].name)

    def __eq__(self, other):
        """Converters compare equal if the draw from the same Containers and deliver to the same Container.
        """

        if not isinstance(other, Converter):

            return NotImplemented

        self_containers = [tup[0] for tup in self.source_tuples_list]
        other_containers = [tup[0] for tup in other.source_tuples_list]

        # Containers are not hashable, so use their name
        #
        if set([container.name for container in self_containers]) != set([container.name for container in other_containers]):

            return False

        if self.target_units_tuple[0].name != other.target_units_tuple[0].name:

            return False

        return True

    def __ne__(self, other):

        if not isinstance(other, Converter):

            return NotImplemented

        return not self.__eq__(other)

class Milestone:
    """A Milestone incorporates information to be returned by milestones().

       Attributes:

       Milestone.container_value_dict
           A dict mapping container instances to the required number of units.

       Milestone.containers
           A list of containers in order of their addition.

       Milestone.converters
           A list of converters that contribute to this milestone.
           This must be populated from outside the Milestone.
           milestones() will do this.
    """

    def __init__(self):
        """Initialise.
        """

        self.container_value_dict = {}
        self.containers = []
        self.converters = []

        return

    def add(self, container, value):
        """Add or increase required number of units for the container.
        """

        if container in self.container_value_dict.keys():

            self.container_value_dict[container] = self.container_value_dict[container] + value

        else:

            self.container_value_dict[container] = value

            self.containers.append(container)

        return

    def units(self, container):
        """Convenience method, equivalent to Milestone.container_value_dict[container].
        """

        return self.container_value_dict[container]

    def percent(self, container):
        """Return the percentage of completeness of the container.
           This uses Container.units_delivered for computation, so the
           percentage relates to the lifetime of the Container, not to
           the current stock.
        """

        if container in self.containers:

            # Explicit float conversion for Python 2.6
            #
            return float(container.units_delivered) / float(self.units(container)) * 100.0

        else:
            raise KeyError("Container {0} not in Milestone.container_value_dict".format(container))

    def total_percent(self):
        """Return the percentage of completeness of this milestone.

           Should a self.percent(container) call return more than 100 percent,
           100 will be used instead, so this method will always return a value
           between 0 and 100.
        """

        if not self.containers:

            return 0

        else:

            percent_sum = 0

            for container in self.containers:

                percent_value = self.percent(container)

                if percent_value > 100:

                    percent_sum = percent_sum + 100

                else:

                    percent_sum = percent_sum + percent_value

            # Explicit float conversion for Python 2.6
            #
            return float(percent_sum) / float(len(self.containers))

    def __len__(self):
        """Implemented for truth value testing.
           Returns len(self.container_value_dict).
        """
        # In Python 2.6 there is object.__nonzero__(), in Python 3.x there
        # is object.__bool__(). Both fall back to object.__len__(), so we
        # implement this.

        return len(self.container_value_dict)

    def __repr__(self):
        """Readable, but not official string representation.
        """

        container_value_list = ["{0}: {1}".format(container.name, self.units(container)) for container in self.containers]

        return "<Milestone ({0}) {1}%>".format(", ".join(container_value_list),
                                               round(self.total_percent(), 2))

    def __str__(self):
        """Elaborate, inofficial string representation.
        """

        return_str = "\nMilestone:\n"

        msg = "{0} {1} in {2} ({3} delivered, {4}%)\n"

        for container in self.containers:

            return_str = return_str + msg.format(self.units(container),
                                                 container.type,
                                                 container.name,
                                                 container.units_delivered,
                                                 round(self.percent(container), 2))

        return_str = return_str + "total: {0}%".format(round(self.total_percent(), 2))

        return return_str

class Simulation:
    """A Simulation wraps a graph of Containers and Converters and runs the simulation step-by-step.

       Attributes:

       Simulation.converter_dict
           A dict mapping Converter names to instances of Converters whose
           draw(), process() and deliver() methods will be called in
           Simulation.step().

       Simulation.converter_list
           A list of Converters names, in order of their addition to the
           Simulation.

       Simulation.container_dict
           A convenience dict mapping Container names to instances of Containers
           connected to the Converters.

       Simulation.step_counter
           An integer counting the steps that have been taken.
    """

    def __init__(self, *converters):
        """Initialise.
        """

        self.converter_dict = {}
        self.converter_list = []
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

        self.converter_list.append(converter.name)

        LOGGER.debug("Adding converter '{0}' to simulation.".format(converter.name))

        self.rebuild_container_dict()

        return

    def remove_converter(self, name):
        """Remove a Converter from the simulation by its name.
           If name is not found in Simulation.converter_dict, no action will be
           taken.
        """

        if name in self.converter_dict.keys():

            # Undo last draw
            #
            self.converter_dict[name].revert()

            LOGGER.debug("Removing converter '{0}' from simulation.".format(name))

            del self.converter_dict[name]

            del self.converter_list[self.converter_list.index(name)]

            self.rebuild_container_dict()

        else:
            LOGGER.error("Cannot remove '{0}', Converter not found.".format(name))

        return

    def rebuild_container_dict(self):
        """Rebuild Simulation.container_dict from registered converters.
        """

        self.container_dict = {}

        # Use self.converter_list in all iterations to be deterministic
        #
        for name in self.converter_list:

            converter = self.converter_dict[name]

            for container in [x[0] for x in converter.source_tuples_list]:

                if container not in self.container_dict.values():

                    self.container_dict[container.name] = container

            if converter.target_units_tuple[0] not in self.container_dict.values():

                container = converter.target_units_tuple[0]

                self.container_dict[container.name] = container

        LOGGER.debug("Current containers: {0}".format(list(self.container_dict.keys())))

        return

    def parse_condition_string(self, condition_string):
        """Check condition_string for validity and return the components.

           condition_string must be a string "NAME OPERATOR VALUE" where

           - NAME is a valid key to Simulation.container_dict
           - OPERATOR is one of ("<", ">", ">=", "<=", "==", "!=")
           - VALUE is a number

           Returns a three-string tuple (container, operator, value).
        """

        # Taken from my "Projektmanager" game on 7 April 2011

        match = re.match(r"^([^<>=!]+?)\s*([<>=!]{1,2})\s*(\w+)\s*$",
                         condition_string)

        if match is not None and len(match.groups()) == 3:

            container, operator, value = match.groups()

            if container not in self.container_dict.keys():

                msg = "container '{0}' not in Simulation.container_dict: {1}"

                raise KeyError(msg.format(container,
                                          list(self.container_dict.keys())))

            # The regex above will let an invalid "<<" etc. pass, so check again
            #
            if operator not in ("<", ">", ">=", "<=", "==", "!="):

                raise SyntaxError("break condition operator '{0}' is invalid".format(operator))

            if not value.isdigit():

                raise TypeError("break condition value '{0}' is not a number".format(value))

            # Still here? Then everything should be fine.
            #
            return (container, operator, value)

        else:
            raise SyntaxError("invalid condition string: '{0}'".format(condition_string))

    def check(self, condition_string):
        """Convenience function to check if a condition is True right now.

           condition_string must be a string suitable for submission to
           Simulation.parse_condition_string().

           Returns True if the condition is true, False otherwise.
        """

        container, operator, value = self.parse_condition_string(condition_string)

        return eval('self.container_dict["{0}"].stock {1} {2}'.format(container,
                                                                      operator,
                                                                      value))

    def step(self):
        """Advance one simulation step.
           This will not return an error if the simulation is empty.
        """

        # To be able to evaluate the Container state between steps, we do not
        # want Converters to pick up units that have just been delivered during
        # the same step. So we first call Converter.process(), then
        # Converter.draw(), then Converter.deliver(). Still, the three have to
        # be mutually exclusive, i.e. only one of the three is carried out in
        # one step.
        #
        # TODO: can this be done more elegantly using Python's generators?

        converters_no_process = []

        # Use self.converter_list in all iterations to be deterministic
        #
        for name in self.converter_list:

            if not self.converter_dict[name].process():

                converters_no_process.append(name)

        converters_no_draw = []

        for name in converters_no_process:

            if not self.converter_dict[name].draw():

                converters_no_draw.append(name)

        for name in converters_no_draw:

            self.converter_dict[name].deliver()

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

    def estimate_finish(self, condition_string, max_steps):
        """Return the total number of steps after which this Simulation instace will meet condition_string.

           condition_string must be a string suitable for submission to
           Simulation.parse_condition_string().

           max_steps must be an integer giving the number of steps after which
           the simulation should be canceled.

           This method will create a copy of the Simulation instance and not
           alter the original instance in any way.
        """

        # Taken from my "Projektmanager" game on 7 April 2011

        # First check if the condition has already been met.
        #
        if self.check(condition_string):

            # TODO: this is actually not true since the counter can be advanced although the condition has already been met before
            #
            return self.step_counter

        else:

            sim_copy = copy.deepcopy(self)

            # Build a new break condition test.
            #
            container, operator, value = self.parse_condition_string(condition_string)

            finish_test = 'lambda: sim_copy.container_dict["{0}"].stock {1} {2} or sim_copy.step_counter >= {3}'

            finish_test = finish_test.format(container,
                                             operator,
                                             value,
                                             max_steps)

            # Make sure sim_copy is found in eval()
            #
            finish_test = eval(finish_test, {"sim_copy": sim_copy})

            sim_copy.run(finish_test)

            return sim_copy.step_counter

    def save_dot(self, filename, size = 5, fontsize = 10, fontname = "Bitstream Vera Sans"):
        """Export the simulation graph into the Graphviz DOT graph language.

           size, fontsize and fontname are DOT graph parameters.

           Use for example

               $ dot -Tpng graph.dot > graph.png

           to render.

           See http://www.graphviz.org/ for details.
        """

        dot_string_list = ["""digraph {{
    graph [size={0}] ;
    node [fontsize={1}, fontname="{2}"] ;
""".format(size, fontsize, fontname)]

        # For brevity, we only want a single node in the graph for all
        # Converters that compare equal.
        # So we build a list of lists of equal Converters.
        #
        converter_lists = []

        # Use self.converter_list in all iterations to be deterministic
        #
        for name in self.converter_list:

            converter = self.converter_dict[name]

            for sublist in converter_lists:

                # Equivalent converters compare as equal, check for the
                # first only
                #
                if converter == sublist[0]:

                    sublist.append(converter)

                    converter = None

                    break

            if converter is not None:

                converter_lists.append([converter])

        # Now export the graph
        #
        for sublist in converter_lists:

            converter = sublist[0]
            converters_name = "\\n".join([converter.name for converter in sublist])

            # First the source containers
            #
            for tuple in converter.source_tuples_list:

                shape_string = '    "{0}" [shape=box];\n'.format(tuple[0].name)

                if not shape_string in dot_string_list:

                    dot_string_list.append(shape_string)

                dot_string_list.append('    "{0}" -> "{1}" ;\n'.format(tuple[0].name,
                                                                       converters_name))

            # Then the target container
            #
            shape_string = '    "{0}" [shape=box];\n'.format(converter.target_units_tuple[0].name)

            if not shape_string in dot_string_list:

                dot_string_list.append(shape_string)

            dot_string_list.append('    "{0}" -> "{1}" ;\n'.format(converters_name,
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

        repr = "<Simulation, converters: {0}, containers: {1}>"

        # Use self.converter_list in all iterations to be deterministic
        #
        return repr.format([self.converter_dict[name] for name in self.converter_list],
                           list(self.container_dict.values()))

def milestones(condition_string, converter_list, graph_export = None):
    """Return an ordered list of Milestone instances that represents milestones to meet the condition.

       condition_string must be a string suitable for submission to
       Simulation.parse_condition_string().

       The operator in the string must be "==".

       converter_list must be a list of Converters that should be searched for
       contributions to Milestones.

       If graph_export is given, it must be a file name to call
       Simulation.save_dot() with.

       If no Milestones can be computed for this condition, an empty list is
       returned.
    """

    # This is not an Simulation instance method to be able to compute Milestones
    # for Converters that are not part of the Simulation.

    milestones = []

    # Build a new Simulation, which will extract containers etc.
    #
    simulation = Simulation()

    # Sort the converter list by converter name before adding, to be
    # deterministic
    #
    name_converter_dict = {}

    for converter in converter_list:

        name_converter_dict[converter.name] = converter

    name_list = list(name_converter_dict.keys())

    name_list.sort()

    for name in name_list:

        simulation.add_converter(name_converter_dict[name])

    if graph_export is not None:

        LOGGER.debug("saving graph file to '{}'".format(graph_export))

        # Estimate size by rule of thumb from number of converters
        #
        simulation.save_dot(graph_export, size = len(converter_list))

    # Will abort on malformed condition_string
    #
    try:

        container_name, operator, value = simulation.parse_condition_string(condition_string)

    except KeyError:

        return []

    if operator not in ("==", ">="):

        raise Exception("operator '{0}' not supported by this method".format(operator))

    # Final milestone is the break condition
    #
    current_milestone = Milestone()

    # TODO: using float(). stepsim should clarify whether it is discrete or not.
    #
    current_milestone.add(simulation.container_dict[container_name], float(value))

    while current_milestone:

        LOGGER.debug("adding current milestone {0}".format(repr(current_milestone)))

        milestones = [current_milestone] + milestones

        new_milestone = Milestone()

        for milestone_container in current_milestone.containers:

            LOGGER.debug("resetting converters in '{0}'".format(repr(current_milestone)))

            # Use a temporary local variable instead of
            # current_milestone.converters as it may store leftover converters
            #
            current_converters = []

            LOGGER.debug("looking for contributors to '{0}'".format(milestone_container.name))

            # Using self.converter_list in all iterations to be deterministic
            #
            for name in simulation.converter_list:

                converter = simulation.converter_dict[name]

                if converter.target_units_tuple[0] == milestone_container:

                    LOGGER.debug("found contributor '{0}'".format(converter.name))

                    current_converters.append(converter)

            # Any contributors?
            #
            if not current_converters:

                LOGGER.debug("no contributors, aborting")

                # Do not break. There might be items left.
                #
                continue

            # Now we know who contributes to achieving this part of the
            # milestone.
            #
            LOGGER.debug("contributors to '{0}': {1}".format(repr(current_milestone),
                                                             [converter.name for converter in current_converters]))

            # Accumulate used Converters in Milestone for bookkeeping.
            #
            current_milestone.converters.extend(current_converters)

            # We use them round robin until the demanded value is fulfilled.
            #
            units_produced = 0

            while units_produced < current_milestone.units(milestone_container):

                msg = "processing converters, {0} of {1} units produced so far"

                LOGGER.debug(msg.format(units_produced,
                                        current_milestone.units(milestone_container)))

                for converter in current_converters:

                    LOGGER.debug("converter '{0}'".format(converter.name))

                    # Save source container units
                    #
                    for source_unit_tuple in converter.source_tuples_list:

                        new_milestone.add(source_unit_tuple[0], source_unit_tuple[1])

                        LOGGER.debug("'{0}' needs {1} more of '{2}'".format(converter.name,
                                                                            source_unit_tuple[1],
                                                                            source_unit_tuple[0].name))

                        LOGGER.debug("new milestone is currently {0}".format(repr(new_milestone)))

                    # Deliver target units
                    #
                    units_produced = units_produced + converter.target_units_tuple[1]

                    # Already satisfied?
                    #
                    if units_produced >= current_milestone.units(milestone_container):

                        msg = "{0} of {1} units produced, aborting"

                        LOGGER.debug(msg.format(units_produced,
                                                current_milestone.units(milestone_container)))

                        break

            # Enough target units of milestone_container produced.

        # Processed all of current_milestone.keys()

        current_milestone = new_milestone

        LOGGER.debug("setting current milestone to new milestone {0}".format(repr(current_milestone)))

    # current_milestone evaluates to False, all possible milestones collected

    LOGGER.info("------------------------------")
    LOGGER.info("Milestones to achieve {0}:".format(condition_string))

    for milestone in milestones:

        LOGGER.info(str(milestone))

    LOGGER.info("------------------------------")

    return milestones
