import argparse
import json
import os
import sys
from xvm.vm import VM

def main():
    parser = argparse.ArgumentParser(
        description="Execute XVM bytecode from a JSON file."
    )
    parser.add_argument(
        "code_file_path",
        type=str,
        help="Path to the JSON file containing the XVM bytecode."
    )
    
    args = parser.parse_args()
    code_path = args.code_file_path

    if not os.path.exists(code_path):
        print(f"Error: File not found at '{code_path}'", file=sys.stderr)
        sys.exit(1)

    vm = VM(input_fn=input, print_fn=print)
    
    print(f"--- XVM: Running Bytecode from {code_path} ---")
    
    try:
        final_stack, final_variables = vm.run_code_from_json(code_path)
        
        print("\n--- Program Finished Successfully ---")

        if final_stack:
            print(f"Final stack value: {final_stack[-1]}")

    except json.JSONDecodeError:
        print(f"\nError: Failed to parse JSON file at '{code_path}'. Ensure it is correctly formatted.", file=sys.stderr)
        sys.exit(1)
    except NameError as e:
        print(f"\nVM Runtime Error (Name): {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nVM Runtime Error: {e}", file=sys.stderr)
        print(f"PC: {vm.pc}, Function: {vm.current_function}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()