
import os

from flizard.readers import (
    PythonReader as fPythonReader,
    FortranReader as fFortranReader,
)

# TODO: move to flinter?
from flizard.helpers import set_processors
from flizard._lizard import FileInfoBuilder

__version__ = '0.1.0'


# TODO: rename to xlizard?
# TODO: some things should be moved back to flinter


def _flanguages():
    return [
        fFortranReader,
        fPythonReader,
    ]


def get_available_exts():
    exts = []
    for language in _flanguages():
        exts.extend(language.ext)

    return set(exts)


def get_reader_for(filename):
    for lan in _flanguages():
        if lan.match_filename(filename):
            return lan


def _update_function_names(context, path):
    # update functions names
    filename = os.path.basename(path).split('.')[0]
    context.global_pseudo_function.name = filename
    for function in context.fileinfo.function_list:
        function.name = f'{filename}.{function.name}'


def _get_comment_spans(context):
    comments_spans = context.global_pseudo_function.comments_spans.copy()

    for function in context.fileinfo.function_list:
        comments_spans.extend(function.comments_spans)

    comments_spans.sort(key=lambda x: x[0])

    return comments_spans


def _from_function_to_dict(function, path):
    path_ = f"{path}/{'.'.join(function.name.split('.')[1:])}"
    if path_[-1] == '/':
        path_ = path_[:-1]

    function_info = {
        'type': function.type,
        'name': function.name,
        'path': path_,
        'size': function.length,
        'depth': function.top_nesting_level,
        'start_line': function.start_line,
        'end_line': function.end_line,
    }

    if hasattr(function, 'start'):
        function_info['start'] = function.start
        function_info['end'] = function.end

    function_info['children'] = []

    return function_info


def _nest_file(data):
    if len(data) == 1:
        return data[0]

    child = data[0]
    last_depth = child['depth']
    children_stack = [[child]]
    for child in data[1:]:
        if child['depth'] == last_depth:
            children_stack[-1].append(child)

        elif child['depth'] < last_depth:
            child['children'] = children_stack.pop()
            if len(children_stack) == 0:
                children_stack.append([])
            children_stack[-1].append(child)

        else:
            for _ in range(child['depth'] - last_depth):
                children_stack.append([])

            children_stack[-1].append(child)

        last_depth = child['depth']

    return child


def parse_content(path, content, parsing_type='errors'):
    # TODO: make sense of parsing_type
    Reader = get_reader_for(path)
    context = FileInfoBuilder(path)

    reader = Reader(context)

    # sets processors and append states
    processors = set_processors(reader)

    tokens = reader.generate_tokens(content, "", lambda match: match)

    for processor in processors:
        tokens = processor(tokens, reader)

    for _ in reader(tokens, reader):
        pass

    _update_function_names(context, path)

    return context
