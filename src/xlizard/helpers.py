"""Factories to simplify object creation.
"""

import lizard

from xlizard.readers import (
    FortranReader,
    PythonReader,
    FortranVariablesState,
    PythonVariablesState,
)
from xlizard import processors as pxlizard


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
        pxlizard.regexp_converter,
        pxlizard.token_len_counter,
        lizard.preprocessing,
        pxlizard.CommentProcessor(reader),
        pxlizard.PositionSetter(reader),
        lambda tokens, reader: pxlizard.line_counter(
            tokens, reader, always_yield=always_yield),
        # lizard.token_counter,
        # lizard.condition_counter,
    ]

    return processors
