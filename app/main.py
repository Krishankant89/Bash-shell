import sys
import os
import subprocess
import shlex


def handle_exit(parts, output_stream):
    sys.exit(0)


def handle_echo(parts, output_stream):
    print(" ".join(parts[1:]), file=output_stream)


def handle_pwd(parts, output_stream):
    print(os.getcwd(), file=output_stream)


def handle_cd(parts, output_stream):
    if len(parts) < 2:
        return

    path = parts[1]

    # Handle "~"
    if path == "~":
        path = os.environ.get("HOME")

    if os.path.isdir(path):
        os.chdir(path)
    else:
        print(f"cd: {parts[1]}: No such file or directory")


def find_executable(cmd):
    path_dirs = os.environ.get("PATH", "").split(":")

    for directory in path_dirs:
        full_path = os.path.join(directory, cmd)

        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path

    return None


def handle_type(parts, output_stream):
    if len(parts) < 2:
        return

    cmd = parts[1]

    if cmd in commands:
        print(f"{cmd} is a shell builtin", file=output_stream)
        return

    path = find_executable(cmd)

    if path:
        print(f"{cmd} is {path}", file=output_stream)
    else:
        print(f"{cmd}: not found", file=output_stream)


commands = {
    "exit": handle_exit,
    "echo": handle_echo,
    "type": handle_type,
    "pwd": handle_pwd,
    "cd": handle_cd,
}


def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        try:
            userInput = input()
        except EOFError:
            break

        parts = shlex.split(userInput)

        if not parts:
            continue

        # Redirection handling
        stdout_target = None

        if ">" in parts:
            idx = parts.index(">")
            stdout_target = parts[idx + 1]
            parts = parts[:idx]

        elif "1>" in parts:
            idx = parts.index("1>")
            stdout_target = parts[idx + 1]
            parts = parts[:idx]

        if not parts:
            continue

        cmd = parts[0]

        output_stream = sys.stdout

        if stdout_target:
            output_stream = open(stdout_target, "w")

        try:
            # Builtin commands
            if cmd in commands:
                commands[cmd](parts, output_stream)

            # External commands
            else:
                # Handle quoted executable paths
                if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
                    path = cmd
                else:
                    path = find_executable(cmd)

                if path:
                    subprocess.run(
                        [cmd] + parts[1:],
                        executable=path,
                        stdout=output_stream
                    )
                else:
                    print(f"{cmd}: command not found")

        finally:
            if stdout_target:
                output_stream.close()


if __name__ == "__main__":
    main()