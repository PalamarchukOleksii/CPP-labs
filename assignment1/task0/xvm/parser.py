from typing import List, Union

from .enums.op_code import OpCode
from .op import Op


def parse_argument(arg: str) -> Union[str, int, float]:
    if arg.startswith('"') and arg.endswith('"'):
        return arg[1:-1]
    try:
        if '.' in arg:
            return float(arg)
        else:
            return int(arg)
    except ValueError:
        return arg


def parse_opcode(opcode_str: str) -> OpCode:
    try:
        return OpCode(opcode_str)
    except ValueError:
        raise ValueError(f"Unknown opcode: '{opcode_str}'")


def parse_string(text: str) -> List[Op]:
    operations = []

    for line in text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        try:
            parts = line.split()
            if not parts:
                continue
                
            opcode = parse_opcode(parts[0])
            args = tuple(parse_argument(arg) for arg in parts[1:])
            
            operations.append(Op(opcode, *args))
            
        except ValueError:
            raise ValueError(f"Error parsing line: '{line}'")

    return operations