
import lizard


class FunctionInfo(lizard.FunctionInfo):
    # TODO: to be removed when lizard is released

    @property
    def length(self):
        return self.end_line - self.start_line + 1

    @length.setter
    def length(self, *args):
        pass


class FileInfoBuilder(lizard.FileInfoBuilder):

    def __init__(self, filename):
        super().__init__(filename)

        self.try_new_function_fncs = []
        self.pop_nesting_fncs = []
        self.before_return_fncs = []

        self.global_pseudo_function = FunctionInfo('*global*',
                                                   self.fileinfo.filename, 0)
        self.current_function = self.global_pseudo_function
        self.global_pseudo_function.type = 'file'

    def try_new_function(self, name):
        # TODO: replace by super().try_new_function(name) when lizard is released
        self.current_function = FunctionInfo(
            self.with_namespace(name),
            self.fileinfo.filename,
            self.current_line)
        self.current_function.top_nesting_level = self.current_nesting_level

        # TODO: fine detailed type
        # TODO: probably remove from here
        self.current_function.type = 'function'

        for fnc in self.try_new_function_fncs:
            fnc()

    def pop_nesting(self):
        previous_function = self.current_function

        super().pop_nesting()

        for fnc in self.pop_nesting_fncs:
            fnc(previous_function)

    def before_return(self):
        # for debug (0 or 1 expected, but neither mean success)
        # if fortran with modules, normally 1 is expected
        self._len_stack_return = len(self._nesting_stack.nesting_stack)

        while len(self._nesting_stack.nesting_stack) > 0:
            self.pop_nesting()

        for fnc in self.before_return_fncs:
            fnc()

    def with_namespace(self, name):
        if len(self._nesting_stack.nesting_stack):
            return self._nesting_stack.nesting_stack[-1].name_in_space + name

        return name
