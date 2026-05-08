import sys
import os
import subprocess

commands = {
    "exit": lambda userInput: sys.exit(0),
    "echo": lambda userInput: print(userInput[5:]),
    "type": lambda userInput: handle_type(userInput),
    "pwd" : lambda userInput: print(os.getcwd())
}

def find_executable(cmd):
    path_dirs = os.environ.get("PATH", "").split(":")

    for directory in path_dirs:
        full_path = os.path.join(directory, cmd)

        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path

    return None


def handle_type(userInput):
    parts = userInput.split()

    if len(parts) < 2:
        return

    cmd = parts[1]

    if cmd in commands:
        print(f"{cmd} is a shell builtin")
        return

    path = find_executable(cmd)

    if path:
        print(f"{cmd} is {path}")
    else:
        print(f"{cmd}: not found")


def main():
    while True:
        sys.stdout.write("$ ")

        userInput = input()
        parts = userInput.split()

        if not parts:
            continue

        cmd = parts[0]

        
        if cmd in commands:
            commands[cmd](userInput)

        else:
            path = find_executable(cmd)

            if path:
                try:
                    subprocess.run([cmd] + parts[1:], executable=path)
                except Exception as e:
                    print(f"Error running command: {e}")
            else:
                print(f"{cmd}: command not found")


if __name__ == "__main__":
    main()