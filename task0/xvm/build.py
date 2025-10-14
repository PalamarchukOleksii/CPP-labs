import os
import json
import sys

def parse_line(line):
    line = line.strip()
    if not line or line.startswith("//"):
        return None

    parts = line.split(maxsplit=1)
    op = parts[0]
    if len(parts) == 2:
        arg = parts[1].strip()
        if arg.startswith('"') and arg.endswith('"'):
            arg = arg[1:-1]
        else:
            try:
                arg = int(arg)
            except ValueError:
                try:
                    arg = float(arg)
                except ValueError:
                    pass
        return {"op": op, "arg": arg}
    else:
        return {"op": op}

def parse_file_to_json(txt_file_path):
    funcs = {}
    current_name = None
    current_ops = []

    with open(txt_file_path, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#"):
                if current_name is not None:
                    funcs[current_name] = current_ops
                func_name = line[1:].strip()
                current_name = func_name
                current_ops = []
            else:
                op_obj = parse_line(line)
                if op_obj:
                    current_ops.append(op_obj)
        if current_name is not None:
            funcs[current_name] = current_ops

    json_file_path = os.path.splitext(txt_file_path)[0] + ".json"
    with open(json_file_path, "w") as f:
        json.dump(funcs, f, indent=4)
    print(f"Saved JSON to {json_file_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build.py <path_to_txt_file>")
        sys.exit(1)

    txt_file_path = sys.argv[1]
    if not os.path.isfile(txt_file_path):
        print(f"File not found: {txt_file_path}")
        sys.exit(1)

    parse_file_to_json(txt_file_path)
