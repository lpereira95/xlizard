
import os


from flinter.error_processing import (
    fmt_analysis,
    get_statements_errors,
    get_vars_errors,
    get_nesting_errors,
    get_args_errors,
)
from flinter.parser.flizard.readers import (
    PythonReader as fPythonReader,
    FortranReader as fFortranReader,
)
from flinter.parser.flizard.helpers import set_processors
import flinter.parser.flizard._lizard as flizard


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


def _get_function_struct_errors(function, struct_rules):
    errors = {}

    get_statements_errors(
        function.length,
        max_lines=struct_rules["max-statements-in-context"],
        errors=errors)

    get_vars_errors(
        function.local_vars,
        max_declared_locals=struct_rules["max-declared-locals"],
        min_var_len=struct_rules["min-varlen"],
        max_var_len=struct_rules["max-varlen"],
        errors=errors)

    get_args_errors(
        function.parameters,
        max_arguments=struct_rules["max-arguments"],
        min_arg_len=struct_rules["min-arglen"],
        max_arg_len=struct_rules["max-arglen"],
        errors=errors)

    get_nesting_errors(
        function.top_nesting_level,
        max_depth=struct_rules["max-nesting-levels"],
        errors=errors)

    return errors


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


def _process_errors(context, path, content, rules):

    function_list = context.fileinfo.function_list + [context.global_pseudo_function]

    # struct errors
    struct_errors = {}
    for function in function_list:
        struct_errors[function.name] = _get_function_struct_errors(
            function, rules['struct-rules'])

    # regexp
    comments_spans = _get_comment_spans(context)
    functions_info = [(function.name, (function.start_line, function.end_line))
                      for function in function_list]
    regexp_errors = fmt_analysis(content, rules['regexp-rules'], comments_spans,
                                 functions_info)

    # concatenate data
    data = []
    for function in function_list:
        func_dict = _from_function_to_dict(function, path)
        func_dict['struct_rules'] = struct_errors[function.name]
        func_dict['regexp_rules'] = regexp_errors[function.name]

        data.append(func_dict)

    return _nest_file(data)


def parse_content(path, content, parsing_type='errors'):
    # TODO: make sense of parsing_type
    Reader = get_reader_for(path)
    context = flizard.FileInfoBuilder(path)

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


def parse_errors(path, content, rules):
    context = parse_content(path, content, parsing_type='errors')

    return _process_errors(context, path, content, rules)
