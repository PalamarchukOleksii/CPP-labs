import copy
from pathlib import Path
import pytest
from xvm.vm import VM

class MyIO:
    def __init__(self, in_buffer):
        self.in_buffer = copy.deepcopy(in_buffer)
        self.out_buffer = []

    def print_fn(self, obj):
        self.out_buffer.append(obj)

    def input_fn(self):
        a = self.in_buffer.pop(0)
        if isinstance(a, str):
            try:
                return int(a)
            except ValueError:
                return float(a)
        return a

def run_vm_test(base, exponent):
    DIR = Path(__file__).parent.resolve() 
    JSON_PATH = DIR / "test_part8_code.json"
    io = MyIO([base, exponent])
    vm = VM(input_fn=io.input_fn, print_fn=io.print_fn)
    stack, variables = vm.run_code_from_json(JSON_PATH)
    return variables, io

@pytest.mark.parametrize(
    "base, exponent, expected",
    [
        (2, 10, 1024),
        (2, 3, 8),
        (-2, 4, 16),
        (-2, 3, -8),
        (5, 0, 1),
        (1, 10000, 1),
        (2, 100, 1267650600228229401496703205376),
    ]
)

def test_fast_exponentiation(base, exponent, expected):
    variables, io = run_vm_test(base, exponent)
    assert variables["base"] == base
    assert variables["exponent"] == exponent
    assert variables["result"] == expected
    assert io.out_buffer[-1] == expected
