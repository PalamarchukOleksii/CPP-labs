from enum import Enum

class OpCode(Enum):
    LOAD_CONST = 'LOAD_CONST'
    LOAD_VAR = 'LOAD_VAR'
    STORE_VAR = 'STORE_VAR'

    ADD = 'ADD'
    SUB = 'SUB'
    MUL = 'MUL'
    DIV = 'DIV'
    EXP = 'EXP'
    SQRT = 'SQRT'
    NEG = 'NEG'
