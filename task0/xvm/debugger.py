import cmd
from xvm.vm import VM, parse_string

class Debugger(cmd.Cmd):
    intro = "Welcome to VM Debugger. Type help or ? to list commands."
    prompt = "debugger> "

    def __init__(self):
        super().__init__()
        self.vm = VM()

    # --- Explicit commands ---
    def do_exit(self, _arg):
        """Exit the debugger."""
        print("Exiting...")
        return True   # returning True exits cmdloop()

    def do_stack(self, arg):
        """Show current stack contents."""
        index = int(arg) if arg.isdigit() else len(self.vm.stack)
        if not arg.isdigit() and arg:
            print("Usage: stack [arg] where arg is a positive integer.")
            return 
        
        if index > len(self.vm.stack):
            print(f"Stack has only {len(self.vm.stack)} elements.")
        else:
            print(self.vm.stack[-index:])

    def do_memory(self, _arg):
        """Show current memory (variables)."""
        if not self.vm.variables:
            print("No variables stored.")
        else:
            print("Variables:")
            for variable, value in self.vm.variables.items():
                print(f"{variable}: {value}")

    def do_print(self, arg):
        """Print the value of a variable. Usage: print <var_name>"""
        if arg in self.vm.variables:
            print(f"{arg} = {self.vm.variables[arg]}")
        else:
            print(f"Variable '{arg}' not found.")       

    def do_exec(self, line):
        """Execute a single operation. Usage: exec <OPCODE> [args...]"""
        op = parse_string(line)
        if not op:
            print("No operation provided.")
            return
        try:
            self.vm.run_op(op[0])
            print(f"Executed: {op[0].opcode} {op[0].args}")
        except Exception as e:
            print(f"Error executing operation: {e}")
    
    def do_load(self, line):
        """Load code from a file. Usage: load <file_path>"""
        if not line.strip():
            print("Usage: load <file_path>")
            return
        try:
            self.vm.load_code_from_json(line.strip())
            print(f"Loaded code from {line.strip()}")
            print(f"Program counter reset to 0, {len(self.vm.code)} instructions loaded.")
        except Exception:
            print("Error loading code")

    def do_step(self, _arg):
        """Execute one instruction from loaded code. Usage: step"""
        try:
            operation = self.vm.step()
            print(f"Executed: {operation.opcode.name} {operation.args if operation.args else ''}")
            print(f"PC: {self.vm.pc}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    def do_run(self, _arg):
        """Run all remaining code from current position. Usage: run"""
        if not self.vm.code:
            print("No code loaded. Use 'load <file>' first.")
            return
            
        try:
            instructions_executed = 0
            self.vm.clear_breakpoint()
            
            while self.vm.pc < len(self.vm.code):
                self.vm.step()
                instructions_executed += 1
                
                if self.vm.is_breakpoint_hit():
                    print(f"Hit breakpoint at PC {self.vm.pc}")
                    break
                    
            if self.vm.pc >= len(self.vm.code):
                print(f"Program execution completed. Executed {instructions_executed} instructions.")
            elif self.vm.is_breakpoint_hit():
                print(f"Executed {instructions_executed} instructions, stopped at breakpoint at PC {self.vm.pc}")
            else:
                print(f"Executed {instructions_executed} instructions, stopped at PC {self.vm.pc}")
                
        except Exception:
            print("Error during execution")

    def do_list(self, _arg):
        """List up to 5 instructions before and after the current one. Usage: list"""
        if not self.vm.code:
            print("No code loaded. Use 'load <file>' first.")
            return
            
        current_pc = self.vm.pc
        total_instructions = len(self.vm.code)
        
        start = max(0, current_pc - 5)
        end = min(total_instructions, current_pc + 6)
        
        print(f"Instructions around PC {current_pc}:")
        print("-" * 40)
        
        for i in range(start, end):
            marker = ">>> " if i == current_pc else "    "
            
            if i < len(self.vm.code):
                op = self.vm.code[i]
                if hasattr(op, 'args') and op.args:
                    if isinstance(op.args, list):
                        args_str = " " + " ".join(map(str, op.args))
                    else:
                        args_str = f" {op.args}"
                else:
                    args_str = ""
                
                print(f"{marker}{i:3d}: {op.opcode.name}{args_str}")
            else:
                print(f"{marker}{i:3d}: <end of code>")

    def do_next(self, _arg):
        """Execute next instruction. If it's a function call, execute the entire function. Usage: next"""
        try:
            operation = self.vm.next()
            print(f"Executed: {operation.opcode.name} {operation.args if operation.args else ''}")
            print(f"PC: {self.vm.pc}, Function: {self.vm.current_function}")
            
        except Exception as e:
            print(f"Error: {e}")

    def do_frame(self, _arg):
        """Print all variables in the current stack frame. Usage: frame"""
        frame_vars = self.vm.variables
        
        if not frame_vars:
            print("No variables in current frame.")
        else:
            print(f"Current frame: {self.vm.current_function}")
            print("Variables:")
            for variable, value in frame_vars.items():
                print(f"  {variable}: {value}")
        
        if self.vm.call_stack:
            print(f"\nCall stack depth: {len(self.vm.call_stack)}")
            print("Call stack:")
            for i, frame in enumerate(reversed(self.vm.call_stack)):
                print(f"  #{i}: {frame.function_name} (return to PC {frame.return_pc})")

    # --- Default (catch-all) ---
    def default(self, line):
        """Called when no other command matches."""
        print(f"[default handler] You entered: {line!r}")
