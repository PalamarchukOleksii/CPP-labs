import math
import json
import pickle

from xvm.enums.op_code import OpCode
from xvm.op import Op
from xvm.parser import parse_string
from xvm.frame import Frame

__all__ = ['parse_string', 'VM']

ENTRYPOINT_KEY = "$entrypoint$"

class VM:
    def __init__(self, input_fn=input, print_fn=print):
        self.stack = []
        self.variables = {}
        self.input_fn = input_fn
        self.print_fn = print_fn
        self.pc = 0
        self.code = []
        self.labels = {}
        self.breakpoint_hit = False

        self.call_stack = []
        self.functions = {}
        self.current_function = ENTRYPOINT_KEY

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

        elif op.opcode == OpCode.MOD:
            assert len(op.args) == 0, f"MOD expects no arguments, got {len(op.args)}"
            arg1 = self.stack.pop()
            arg2 = self.stack.pop()
            self.stack.append(arg1 % arg2)

        elif op.opcode == OpCode.EQ:
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a == b else 0)
            
        elif op.opcode == OpCode.NEQ:
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a != b else 0)
            
        elif op.opcode == OpCode.GT:
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a > b else 0)
            
        elif op.opcode == OpCode.LT:
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a < b else 0)
            
        elif op.opcode == OpCode.GE:
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a >= b else 0)
            
        elif op.opcode == OpCode.LE:
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a <= b else 0)

        elif op.opcode == OpCode.LABEL:
            assert len(op.args) == 1, f"LABEL expects 1 argument, got {len(op.args)}"
            label_name = op.args[0]
            if label_name not in self.labels:
                self.labels[label_name] = self.pc

        elif op.opcode == OpCode.JMP:
            assert len(op.args) == 1, f"JMP expects 1 argument, got {len(op.args)}"
            label_name = op.args[0]
            if label_name not in self.labels:
                raise NameError(f"Label '{label_name}' is not defined")
            self.pc = self.labels[label_name]
            
        elif op.opcode == OpCode.CJMP:
            assert len(op.args) == 1, f"CJMP expects 1 argument, got {len(op.args)}"
            label_name = op.args[0]
            condition = self.stack.pop()
            if condition == 1:
                if label_name not in self.labels:
                    raise NameError(f"Label '{label_name}' is not defined")
                self.pc = self.labels[label_name]
                
        elif op.opcode == OpCode.BREAKPOINT:
            self.breakpoint_hit = True

        elif op.opcode == OpCode.CALL:
            assert len(op.args) == 0, f"CALL expects no arguments, got {len(op.args)}"
            function_name = self.stack.pop()
            
            if function_name not in self.functions:
                raise NameError(f"Function '{function_name}' is not defined")
            
            frame = Frame(self.current_function, self.pc, self.variables.copy(), self.labels.copy())
            self.call_stack.append(frame)

            self.current_function = function_name
            self.code = self.functions[function_name]
            self.variables = {}
            self._preprocess_labels()
            self.pc = -1
            
            if self.breakpoint_hit:
                self.pc += 1
            
        elif op.opcode == OpCode.RET:
            assert len(op.args) == 0, f"RET expects no arguments, got {len(op.args)}"
            
            if not self.call_stack:
                self.pc = len(self.code)
                return
            
            frame = self.call_stack.pop()
            self.current_function = frame.function_name
            self.code = self.functions[frame.function_name]
            self.variables = frame.variables
            self.labels = frame.labels
            self.pc = frame.return_pc

        else:
            raise NotImplementedError(f"Opcode {op.opcode} not implemented yet.")
        
    def _preprocess_labels(self):
        self.labels = {}
        for i, op in enumerate(self.code):
            if op.opcode == OpCode.LABEL:
                label_name = op.args[0]
                self.labels[label_name] = i

    def run_code(self, code, load_code=True):
        if isinstance(code, dict):
            self.functions = code.copy()
            
            if ENTRYPOINT_KEY not in self.functions:
                raise ValueError(f"Code dictionary must contain '{ENTRYPOINT_KEY}' key")
            
            if load_code:
                self.code = self.functions[ENTRYPOINT_KEY]
                self.current_function = ENTRYPOINT_KEY
                self._preprocess_labels()
                self.pc = 0
                self.call_stack = []
                
        elif isinstance(code, list):
            if not all(isinstance(op, Op) for op in code):
                raise TypeError("All elements of code must be Op instances")
            
            if load_code:
                self.functions = {ENTRYPOINT_KEY: code}
                self.code = code
                self.current_function = ENTRYPOINT_KEY
                self._preprocess_labels()
                self.pc = 0
                self.call_stack = []
        else:
            raise TypeError(f"Expected list[Op] or dict[str, list[Op]], got {type(code).__name__}")

        self.breakpoint_hit = False

        while True:
            if self.pc >= len(self.code):
                if self.call_stack:
                    frame = self.call_stack.pop()
                    self.current_function = frame.function_name
                    self.code = self.functions[self.current_function]
                    self.variables = frame.variables
                    self.labels = frame.labels
                    self.pc = frame.return_pc + 1
                    continue
                else:
                    break

            if self.breakpoint_hit:
                break

            operation = self.code[self.pc]
            self.run_op(operation)
            
            if not self.breakpoint_hit:
                self.pc += 1

        return self.stack, self.variables
    
    def run_loaded_code(self):
        if not self.code:
            raise RuntimeError("No code loaded. Use load_code_from_json() first.")
        
        return self.run_code(self.code, load_code=False)
    
    def parse_code_from_json(self, json_path: str) -> dict[str, list[Op]]:
        with open(json_path, 'r') as file:
            data = json.load(file)

        all_code = {}
        for func_name, data_ops in data.items():
            ops = []
            for op_dict in data_ops:
                opcode = OpCode(op_dict.get("op"))
                arg = op_dict.get("arg")
                if arg is not None:
                    ops.append(Op(opcode, arg))
                else:
                    ops.append(Op(opcode))
            all_code[func_name] = ops

        return all_code

    def load_code_from_json(self, json_path: str):
        code_dict = self.parse_code_from_json(json_path)
        if ENTRYPOINT_KEY not in code_dict:
            raise ValueError(f"JSON must contain '{ENTRYPOINT_KEY}' key")
        
        self.functions = code_dict
        self.code = self.functions[ENTRYPOINT_KEY]
        self.current_function = ENTRYPOINT_KEY
        self._preprocess_labels()
        self.pc = 0
        return code_dict

    def run_code_from_json(self, json_path: str):
        self.load_code_from_json(json_path)
        return self.run_loaded_code()

    def step(self):
        if not self.code:
            raise RuntimeError("No code loaded. Use load_code_from_json() first.")
        
        if self.pc >= len(self.code):
            raise RuntimeError("Program execution finished.")
        
        operation = self.code[self.pc]
        old_pc = self.pc
        
        self.run_op(operation)
        
        if self.pc == old_pc:
            self.pc += 1
            
        return operation
    
    def next(self):
        if not self.code:
            raise RuntimeError("No code loaded. Use load_code_from_json() first.")
        
        if self.pc >= len(self.code):
            raise RuntimeError("Program execution finished.")
        
        operation = self.code[self.pc]

        if operation.opcode == OpCode.CALL:
            call_depth = len(self.call_stack)
            self.step()
            
            while self.pc < len(self.code) and len(self.call_stack) > call_depth:
                self.step()
        else:
            self.step()
            
        return operation
    
    def clear_breakpoint(self):
        self.breakpoint_hit = False
    
    def is_breakpoint_hit(self):
        return self.breakpoint_hit

    def dump_stack(self, pkl_path: str):
        with open(pkl_path, 'wb') as file:
            pickle.dump(self.stack, file)

    def load_stack(self, pkl_path: str):
        with open(pkl_path, 'rb') as file:
            self.stack = pickle.load(file)

    def dump_memory(self, pkl_path: str):
        with open(pkl_path, 'wb') as file:
            pickle.dump(self.variables, file)

    def load_memory(self, pkl_path: str):
        with open(pkl_path, 'rb') as file:
            self.variables = pickle.load(file)