class Frame:
    def __init__(self, function_name, return_pc, variables=None, labels=None):
        self.function_name = function_name
        self.return_pc = return_pc
        self.variables = variables if variables is not None else {}
        self.labels =  labels if labels is not None else {}