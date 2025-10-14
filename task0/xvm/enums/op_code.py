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
    MOD = 'MOD'

    PRINT = 'PRINT'
    INPUT_STRING = 'INPUT_STRING'
    INPUT_NUMBER = 'INPUT_NUMBER'

    BREAKPOINT = 'BREAKPOINT'

    EQ = 'EQ'
    NEQ = 'NEQ'
    GT = 'GT'
    LT = 'LT'
    GE = 'GE'
    LE = 'LE'

    LABEL = 'LABEL'
    JMP = 'JMP'
    CJMP = 'CJMP'

    CALL = 'CALL'
    RET = 'RET'
