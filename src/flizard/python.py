"""Language parser for Python.

Hopefully, this file can soon be merged in lizard.

What needs to be done before merge:
* eof may be a problem
"""

from lizard_languages.code_reader import CodeReader, CodeStateMachine
from lizard_languages.script_language import ScriptLanguageMixIn


def count_spaces(token):
    return len(token.replace('\t', ' ' * 8))


class PythonIndents:  # pylint: disable=R0902
    def __init__(self, context):
        self.indents = [0]
        self.context = context

    def set_nesting(self, spaces, token=""):
        while self.indents[-1] > spaces and (not token.startswith(")")):
            self.indents.pop()
            self.context.pop_nesting()
        if self.indents[-1] < spaces:
            self.indents.append(spaces)
            self.context.add_bare_nesting()

    def reset(self):
        self.set_nesting(0)


class PythonReader(CodeReader, ScriptLanguageMixIn):

    ext = ['py']
    language_names = ['python']
    _conditions = set(['if', 'for', 'while', 'and', 'or',
                       'elif', 'except', 'finally'])

    protected_names = _conditions.union(
        {'with', 'def', 'class', 'from', 'import', 'try', 'return',
         'else', 'print'})

    def __init__(self, context):
        super(PythonReader, self).__init__(context)
        self.parallel_states = [PythonStates(context, self)]

    @staticmethod
    def generate_tokens(source_code, addition='', token_class=None):
        return ScriptLanguageMixIn.generate_common_tokens(
            source_code,
            r"|\'\'\'.*?\'\'\'" + r'|\"\"\".*?\"\"\"', token_class)

    @staticmethod
    def get_comment_from_token(token):
        if token.startswith('#'):
            return token[1:]
        elif token.startswith('"""') or token.startswith("'''"):
            return token[3:]

    def preprocess(self, tokens):
        indents = PythonIndents(self.context)
        current_leading_spaces = 0
        reading_leading_space = True
        for token in tokens:
            if token != '\n':
                if reading_leading_space:
                    if token.isspace():
                        current_leading_spaces += count_spaces(token)
                    else:
                        if not token.startswith('#'):
                            indents.set_nesting(current_leading_spaces, token)
                        reading_leading_space = False
            else:
                reading_leading_space = True
                current_leading_spaces = 0
            if not token.isspace() or token == '\n':
                yield token
        indents.reset()

    def eof(self):
        self.context.before_return()


class PythonStates(CodeStateMachine):  # pylint: disable=R0903

    def __init__(self, context, reader):
        super(PythonStates, self).__init__(context)
        self.reader = reader

    def _state_global(self, token):
        # TODO: check how decorators are handled

        if token == 'def':
            self._state = self._function
        elif token == 'class':
            self._state = self._class

    def reset_state(self, token=None):
        self._state = self._state_global
        if token is not None:
            self._state_global(token)

    def _function(self, token):
        if token != '(':
            last_type = self.context.current_function.type
            self.context.restart_new_function(token)
            self.context.add_to_long_function_name("(")

            if last_type == 'class':
                self.context.current_function.type = 'class_method'
            else:
                self.context.current_function.type = 'function'
        else:
            self._state = self._dec

    def _dec(self, token):
        if token == ')':
            self._state = self._state_global
        else:
            self.context.parameter(token)
            return
        self.context.add_to_long_function_name(" " + token)

    def _class(self, token):
        if token == '(':
            self._state = self._class_dec
        elif token == ':':
            self.reset_state()
        else:
            self.context.restart_new_function(token)
            self.context.current_function.type = 'class'
            # maybe too implicit
            self.context.current_function.base_classes = []

    def _class_dec(self, token):
        if token == ')':
            self.reset_state()
        elif token == '=':
            self.context.current_function.base_classes.pop()
        elif token.isidentifier():
            self.context.current_function.base_classes.append(token)
