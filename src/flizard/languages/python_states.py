"""Additional states defined for python parser.
"""

from lizard_languages.code_reader import CodeStateMachine

from flizard.processors import _LocalVarsStateProcessor


# TODO: make it work without '\n'


class PythonVariablesState(CodeStateMachine, _LocalVarsStateProcessor):

    def __init__(self, context, reader):
        CodeStateMachine.__init__(self, context)
        _LocalVarsStateProcessor.__init__(self, reader)

        self._potential_local_vars = []

    def _state_global(self, token):
        if self.last_token == '\n' and token.isidentifier() \
                and token not in self.reader.protected_names:
            self.next(self._potential_local_var, token)

    def reset_state(self, token=None):
        self._state = self._state_global
        if token is not None:
            self._state_global(token)

    def _potential_local_var(self, token):
        # TODO: == case
        # TODO: a = b = 2. case
        if token == '=':
            self.context.current_function.local_vars.extend(self._potential_local_vars)
            self._potential_local_vars = []
            self.reset_state()
        elif token.isidentifier():
            if self.last_token == '.':  # for class variables
                self._potential_local_vars[-1] += f'.{token}'
            else:
                self._potential_local_vars.append(token)
        elif token == '\n' or token == '(' or token == '[':
            self._potential_local_vars = []
            self.reset_state()
