"""Factories to simplify object creation.
"""

import lizard

from flinter.parser.flizard.readers import (
    FortranReader,
    PythonReader,
)
from flinter.parser.flizard.fortran_states import FortranVariablesState
from flinter.parser.flizard.python_states import PythonVariablesState
from flinter.parser.flizard import processors as pflizard


def add_state_to_reader(reader, state):
    reader.parallel_states.append(state)


def set_processors(reader, parsing_type='errors'):
    # TODO: add basic to be the same as lizard
    # TODO: add complexity
    map_parsing = {
        'errors': _set_for_errors,
    }
    return map_parsing[parsing_type](reader)


def add_vars_state_to_reader(reader):

    if isinstance(reader, FortranReader):
        state = FortranVariablesState(reader.context, reader)
    elif isinstance(reader, PythonReader):
        state = PythonVariablesState(reader.context, reader)
    else:
        return

    add_state_to_reader(reader, state)


def _set_for_errors(reader):
    # to collect local vars if available
    add_vars_state_to_reader(reader)

    return _get_error_processors(reader)


def _get_error_processors(reader):
    # these parsers needs access to '\n' tokens
    # in python only for local variables
    always_yield = isinstance(reader, FortranReader) or isinstance(reader, PythonReader)

    processors = [
        pflizard.regexp_converter,
        pflizard.token_len_counter,
        lizard.preprocessing,
        pflizard.CommentProcessor(reader),
        pflizard.PositionSetter(reader),
        lambda tokens, reader: pflizard.line_counter(
            tokens, reader, always_yield=always_yield),
        # lizard.token_counter,
        # lizard.condition_counter,
    ]

    return processors
