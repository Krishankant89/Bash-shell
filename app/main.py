import sys


def main():
    # TODO: Uncomment the code below to pass the first stage
    # sys.stdout.write("$ ")
    while True:
        sys.stdout.write("$ ")

        command = input()
        if command == "exit":
            break
        # print(f"{command}: command not found")
        elif command.startswith("echo"):
            print(command[5:])
        else:
            print(f"{command}: command not found")

if __name__ == "__main__":
    main()
