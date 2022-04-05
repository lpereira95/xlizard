"""Additional states defined for fortran parser.
"""

from lizard_languages.code_reader import CodeStateMachine

from flinter.parser.flizard.processors import _LocalVarsStateProcessor


class FortranVariablesState(CodeStateMachine, _LocalVarsStateProcessor):

    def __init__(self, context, reader):
        CodeStateMachine.__init__(self, context)
        _LocalVarsStateProcessor.__init__(self, reader)

    def __call__(self, token, reader=None):
        self._state(token)

    def _add_local_var(self, var_name):
        self.context.current_function.local_vars.append(var_name)

    def _state_global(self, token):
        if token.upper() in ('INTEGER', 'REAL', 'COMPLEX', 'LOGICAL', 'CHARACTER'):
            self._state = self._wait_double_colon

    def reset_state(self, token=None):
        self._state = self._state_global
        if token is not None:
            self._state_global(token)

    def _wait_double_colon(self, token):
        if token == '::':
            self._state = self._add_var

    def _wait_var_after_comma(self, token):
        if token == '\n':
            self.reset_state()
        elif token == '(':
            self._state = self._wait_close_paren
        elif token == ',':
            self._state = self._add_var

    def _wait_close_paren(self, token):
        if token == ')':
            self._state = self._wait_var_after_comma

    def _add_var(self, token):
        self._add_local_var(token)
        self._state = self._wait_var_after_comma
