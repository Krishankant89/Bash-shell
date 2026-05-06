import sys

def main():
    builtins = ["echo", "exit", "type"]

    while True:
        sys.stdout.write("$ ")

        command = input()

        if command == "exit":
            break

        elif command.startswith("echo"):
            print(command[5:])

        elif command.startswith("type"):
            cmd = command.split()[1]

            if cmd in builtins:
                print(f"{cmd} is a shell builtin")
            else:
                print(f"{cmd}: not found")

        else:
            print(f"{command}: command not found")

if __name__ == "__main__":
    main()