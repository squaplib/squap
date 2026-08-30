class Variables:
    def __init__(self):
        super().__setattr__("_variables", {})
        super().__setattr__("_callbacks", [])   # For detecting any change to a variable
        # might need to become a dict for multiple _callbacks per variable.

    def __getattr__(self, name):
        if name in self._variables:
            return self._variables[name]
        else:
            raise AttributeError(f"'Namespace' object has no attribute '{name}'")

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setattr__(self, name, value):
        if name in ('_variables', '_callbacks'):
            raise ValueError(f"'{name}' is a reserved name and cannot be used")

        self._variables[name] = value

        if name in self._callbacks:
            for callback in self._callbacks[name]:
                callback()

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __delitem__(self, key):
        del self._variables[key]

    def on_change(self, var_name, func):
        """When the variable with name ``var_name`` is changed, the function ``func`` is called."""
        if var_name in self._callbacks:
            self._callbacks[var_name].append(func)
        else:
            self._callbacks[var_name] = [func]

    def __repr__(self):
        result = "Variables:\n"
        for index, key in enumerate(self._variables):
            if index == len(self._variables):
                result += f"    {key} = {self._variables[key]}"
            else:
                result += f"    {key} = {self._variables[key]}\n"
        return result
