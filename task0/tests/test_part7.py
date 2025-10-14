import io
import os
import sys
import pytest
from xvm.debugger import Debugger


def run_debugger_commands(commands):
    """Run debugger with simulated stdin/stdout and return full output as string."""
    old_stdin, old_stdout = sys.stdin, sys.stdout
    sys.stdin = io.StringIO("\n".join(commands) + "\n")
    sys.stdout = io.StringIO()
    try:
        dbg = Debugger()
        dbg.cmdloop()
        return sys.stdout.getvalue()
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout


@pytest.fixture
def code_file_path():
    """Return absolute path to test JSON file in same directory."""
    return os.path.join(os.path.dirname(__file__), "test_part4_code.json")


def assert_output_in_order(output: str, expected_lines: list[str]):
    """
    Assert that all expected_lines appear in the given order within the output.
    Allows arbitrary text between expected lines.
    """
    current_index = 0
    for expected in expected_lines:
        next_index = output.find(expected, current_index)
        if next_index == -1:
            raise AssertionError(
                f"Expected line not found or out of order: '{expected}'\n\n"
                f"Output (truncated):\n{output[current_index:current_index+800]}"
            )
        current_index = next_index + len(expected)


def test_load_command(code_file_path):
    output = run_debugger_commands([f"load {code_file_path}", "exit"])
    assert_output_in_order(output, [
        f"Loaded code from {code_file_path}",
        "Program counter reset to 0, 12 instructions loaded.",
        "Exiting..."
    ])


def test_memory_empty(code_file_path):
    output = run_debugger_commands([f"load {code_file_path}", "memory", "exit"])
    assert_output_in_order(output, [
        f"Loaded code from {code_file_path}",
        "Program counter reset to 0, 12 instructions loaded.",
        "No variables stored.",
        "Exiting..."
    ])


def test_stack_empty(code_file_path):
    output = run_debugger_commands([f"load {code_file_path}", "stack", "exit"])
    assert_output_in_order(output, [
        f"Loaded code from {code_file_path}",
        "Program counter reset to 0, 12 instructions loaded.",
        "[]",
        "Exiting..."
    ])


def test_step_load_const(code_file_path):
    output = run_debugger_commands([f"load {code_file_path}", "step", "exit"])
    assert_output_in_order(output, [
        f"Loaded code from {code_file_path}",
        "Program counter reset to 0, 12 instructions loaded.",
        "Executed: LOAD_CONST (10,)",
        "PC: 1",
        "Exiting..."
    ])


def test_step_breakpoint(code_file_path):
    output = run_debugger_commands([f"load {code_file_path}", "step", "step", "exit"])
    assert_output_in_order(output, [
        f"Loaded code from {code_file_path}",
        "Program counter reset to 0, 12 instructions loaded.",
        "Executed: LOAD_CONST (10,)",
        "PC: 1",
        "Executed: BREAKPOINT",
        "PC: 2",
        "Exiting..."
    ])


def test_stack_after_load_const(code_file_path):
    output = run_debugger_commands([f"load {code_file_path}", "step", "stack 1", "exit"])
    assert_output_in_order(output, [
        f"Loaded code from {code_file_path}",
        "Program counter reset to 0, 12 instructions loaded.",
        "Executed: LOAD_CONST (10,)",
        "PC: 1",
        "[10]",
        "Exiting..."
    ])


def test_next_store_var_and_add(code_file_path):
    output = run_debugger_commands([f"load {code_file_path}", "next", "next", "exit"])
    assert_output_in_order(output, [
        f"Loaded code from {code_file_path}",
        "Program counter reset to 0, 12 instructions loaded.",
        "Executed: LOAD_CONST (10,)",
        "PC: 1, Function: $entrypoint$",
        "Executed: BREAKPOINT",
        "PC: 2, Function: $entrypoint$",
        "Exiting..."
    ])


def test_frame_variables(code_file_path):
    output = run_debugger_commands([f"load {code_file_path}", "step", "next", "frame", "exit"])
    assert_output_in_order(output, [
        f"Loaded code from {code_file_path}",
        "Program counter reset to 0, 12 instructions loaded.",
        "Executed: LOAD_CONST (10,)",
        "Executed: BREAKPOINT",
        "PC: 2, Function: $entrypoint$",
        "No variables in current frame.",
        "Exiting..."
    ])


def test_run_to_print(code_file_path):
    output = run_debugger_commands([f"load {code_file_path}", "run", "run", "exit"])
    assert_output_in_order(output, [
        f"Loaded code from {code_file_path}",
        "Program counter reset to 0, 12 instructions loaded.",
        "Hit breakpoint at PC 2",
        "Executed 2 instructions, stopped at breakpoint at PC 2",
        "Hit breakpoint at PC 5",
        "Executed 3 instructions, stopped at breakpoint at PC 5",
        "Exiting..."
    ])


def test_exit_command():
    output = run_debugger_commands(["exit"])
    assert_output_in_order(output, [
        "Exiting..."
    ])
