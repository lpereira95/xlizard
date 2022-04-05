
from abc import ABCMeta


class _BaseProcessor(metaclass=ABCMeta):

    def __init__(self, reader):

        # ensure global function contains all attributes
        self.reader = reader
        self.context = reader.context

        # ensure context will be ready
        self._init_context_vars()
        self._init_func_attrs(self.context.current_function)

        self.context.try_new_function_fncs.append(self.on_try_new_function)

        if hasattr(self, 'on_pop_nesting'):
            self.context.pop_nesting_fncs.append(self.on_pop_nesting)

        if hasattr(self, 'on_before_return'):
            self.context.before_return_fncs.append(self.on_before_return)

    def _init_context_vars(self):
        pass

    def _init_func_attrs(self, current_function):
        pass

    def _check_reader(self, reader):
        if reader is not self.reader:
            raise Exception('Reader must be the same as at initialization')

    def on_try_new_function(self):
        self._init_func_attrs(self.context.current_function)


def regexp_converter(tokens, reader):
    reader.context._token_span = None

    for token in tokens:
        reader.context._token_span = token.span()
        yield token.group()


def token_len_counter(tokens, reader):
    reader.context._token_len = 0

    for token in tokens:
        yield token
        reader.context._token_len += len(token)


def position_setter(tokens, reader):
    context = reader.context
    for token in tokens:
        yield token

        context.current_position += context._token_len
        context._token_len = 0  # reset length

        if token != '\n':
            context.current_function.end = context.current_position + (len(token) - 1)
        else:
            context._line_start_span = context.current_position + 1


class PositionSetter(_BaseProcessor):
    """Processes span position.

    Requires the following processors:
        * token_len_counter
    """

    def _init_context_vars(self):
        self.context._line_start_span = 0
        self.context.current_position = 0

    def _init_func_attrs(self, current_function):
        current_function.children_spans = []
        current_function.start = current_function.end = self.context._line_start_span

    def on_pop_nesting(self, previous_function):
        if self.context.current_function is not previous_function:
            self.context.current_function.end = previous_function.end

    def on_before_return(self):
        self.context.current_function.end = self.context.current_position + self.context._token_len

        # to assign children spans
        self._assign_children_spans()

    def _assign_children_spans(self):
        previous_child = self.context.global_pseudo_function

        stack = [previous_child]
        functions = self.context.fileinfo.function_list
        for i, child in enumerate(reversed(functions)):
            child.children_spans = []

            while True:
                if child.top_nesting_level <= stack[-1].top_nesting_level:
                    stack.pop()
                else:
                    break

            stack[-1].children_spans.append((child.start, child.end))
            stack.append(child)

        # reverse spans
        for child in [self.context.global_pseudo_function] + functions:
            child.children_spans.reverse()

    def __call__(self, tokens, reader):
        self._check_reader(reader)

        for token in tokens:
            yield token

            self.context.current_position += self.context._token_len
            self.context._token_len = 0  # reset length

            if token != '\n':
                self.context.current_function.end = self.context.current_position + (len(token) - 1)
            else:
                self.context._line_start_span = self.context.current_position + 1


class CommentProcessor(_BaseProcessor):
    """Processes comments and stores comment spans info.

    Requires the following processors:
        * regexp_converter
        * position_setter
    """

    def _init_context_vars(self):
        self.context._comments_spans = []

    def _init_func_attrs(self, current_function):
        current_function.comments_spans = []

    def on_pop_nesting(self, previous_function):
        if self.context.current_function is not previous_function:
            self._assign_comments_spans(previous_function)

    def on_before_return(self):
        self._assign_comments_spans(self.context.current_function)

    def _assign_comments_spans(self, function):
        fstart, fend = function.start, function.end

        # append comment spans
        i = len(self.context._comments_spans) - 1
        while True:
            try:
                start, end = self.context._comments_spans[i]
            except IndexError:
                break

            if end < fstart:  # no need to verify all up
                break

            if start >= fstart and end <= fend:
                function.comments_spans.append((start, end))
                self.context._comments_spans.pop(i)

            i -= 1

        function.comments_spans.reverse()

    def __call__(self, tokens, reader):
        self._check_reader(reader)

        for token in tokens:
            comment = reader.get_comment_from_token(token)
            if comment is not None:
                self.context._comments_spans.append(self.context._token_span)
                for _ in comment.splitlines()[1:]:
                    yield '\n'
            else:
                yield token


class _LocalVarsStateProcessor(_BaseProcessor):

    def _init_func_attrs(self, current_function):
        current_function.local_vars = []

    def on_pop_nesting(self, previous_function):
        if self.context.current_function is not previous_function:
            previous_function.local_vars = list(set(previous_function.local_vars))


def line_counter(tokens, reader, always_yield=False):
    context = reader.context
    context.current_line = 1
    newline = 1
    for token in tokens:
        if token != "\n":
            count = token.count('\n')
            context.current_line += count
            context.add_nloc(count + newline)
            newline = 0
            yield token
        else:
            context.current_line += 1
            newline = 1
            if always_yield is True:
                yield token
