import math

from xvm.enums.op_code import OpCode
from xvm.op import Op
from xvm.parser import parse_string

__all__ = ['parse_string', 'VM']

class VM:
    def __init__(self, input_fn=input, print_fn=print):
        self.stack = []
        self.variables = {}

        self.input_fn = input_fn
        self.print_fn = print_fn

    def run_op(self, op: Op):
        if op.opcode == OpCode.LOAD_CONST:
            assert len(op.args) == 1, f"LOAD_CONST expects exactly one argument, got {len(op.args)}"
            self.stack.append(op.args[0])
            
        elif op.opcode == OpCode.STORE_VAR:
            assert len(op.args) == 1, f"STORE_VAR expects exactly one argument, got {len(op.args)}"
            var_name = op.args[0]
            value = self.stack.pop()
            self.variables[var_name] = value
            
        elif op.opcode == OpCode.LOAD_VAR:
            assert len(op.args) == 1, f"LOAD_VAR expects exactly one argument, got {len(op.args)}"
            var_name = op.args[0]
            assert var_name in self.variables, f"Variable '{var_name}' not found."
            self.stack.append(self.variables[var_name])

        elif op.opcode == OpCode.INPUT_STRING:
            assert len(op.args) == 0, f"INPUT_STRING expects no arguments, got {len(op.args)}"
            value = self.input_fn()
            assert isinstance(value, str), f"INPUT_STRING expected a string, got {type(value)}"
            self.stack.append(value)

        elif op.opcode == OpCode.INPUT_NUMBER:
            assert len(op.args) == 0, f"INPUT_NUMBER expects no arguments, got {len(op.args)}"
            value = self.input_fn()
            assert isinstance(value, (int, float)), f"INPUT_NUMBER expected a number, got {type(value)}"
            self.stack.append(value)

        elif op.opcode == OpCode.PRINT:
            assert len(op.args) == 0, f"PRINT expects no arguments, got {len(op.args)}"
            value = self.stack.pop()
            self.print_fn(value)
            
        elif op.opcode == OpCode.ADD:
            assert len(op.args) == 0, f"ADD expects no arguments, got {len(op.args)}"
            arg1 = self.stack.pop()
            arg2 = self.stack.pop()
            self.stack.append(arg1 + arg2)
            
        elif op.opcode == OpCode.SUB:
            assert len(op.args) == 0, f"SUB expects no arguments, got {len(op.args)}"
            arg1 = self.stack.pop()
            arg2 = self.stack.pop()
            self.stack.append(arg1 - arg2)
            
        elif op.opcode == OpCode.MUL:
            assert len(op.args) == 0, f"MUL expects no arguments, got {len(op.args)}"
            arg1 = self.stack.pop()
            arg2 = self.stack.pop()
            self.stack.append(arg1 * arg2)
            
        elif op.opcode == OpCode.DIV:
            assert len(op.args) == 0, f"DIV expects no arguments, got {len(op.args)}"
            arg1 = self.stack.pop()
            arg2 = self.stack.pop()
            self.stack.append(arg1 / arg2)
            
        elif op.opcode == OpCode.EXP:
            assert len(op.args) == 0, f"EXP expects no arguments, got {len(op.args)}"
            arg1 = self.stack.pop()
            self.stack.append(math.exp(arg1))
            
        elif op.opcode == OpCode.SQRT:
            assert len(op.args) == 0, f"SQRT expects no arguments, got {len(op.args)}"
            arg1 = self.stack.pop()
            self.stack.append(math.sqrt(arg1))
            
        elif op.opcode == OpCode.NEG:
            assert len(op.args) == 0, f"NEG expects no arguments, got {len(op.args)}"
            arg1 = self.stack.pop()
            self.stack.append(-arg1)

        else:
            raise NotImplementedError(f"Opcode {op.opcode} not implemented yet.")


    def run_code(self, code: list[Op]):
        for op in code:
            self.run_op(op)
        return self.stack, self.variables


    def run_code_from_json(self, json_path: str):
        pass


    def dump_stack(self, pkl_path: str):
        pass

    def load_stack(self, pkl_path: str):
        pass


    def dump_memory(self, pkl_path: str):
        pass

    def load_memory(self, pkl_path: str):
        pass