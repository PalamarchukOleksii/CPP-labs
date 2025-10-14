import sys
import subprocess

def main():
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-v"]))

if __name__ == "__main__":
    main()