from dataclasses import dataclass, field

from xvm.enums.op_code import OpCode

@dataclass
class Op:
    opcode: OpCode
    args: tuple = field(default_factory=tuple)
    
    def __init__(self, opcode: OpCode, *args):
        self.opcode = opcode
        self.args = args