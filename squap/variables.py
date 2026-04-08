class Variables:
    def __init__(self):
        super().__setattr__("_variables", {})
        self.hidden_variables = {}

    def __getattr__(self, name):
        if name in self._variables:
            return self._variables[name]
        else:
            raise AttributeError(f"'Namespace' object has no attribute '{name}'")

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setattr__(self, name, value):
        if name != '_variables':
            self._variables[name] = value
        else:
            raise ValueError(f"'_variables' is a reserved name and cannot be used")

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __delitem__(self, key):
        del self._variables[key]

    def __repr__(self):
        result = "Variables:\n"
        for index, key in enumerate(self._variables):
            if index == len(self._variables):
                result += f"    {key} = {self._variables[key]}"
            else:
                result += f"    {key} = {self._variables[key]}\n"

        return result

