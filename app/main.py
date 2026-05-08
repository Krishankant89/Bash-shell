import sys
import os
import subprocess
import shlex

try:
    import readline
except ImportError:
    readline = None


def handle_exit(parts, stdout_stream, stderr_stream):
    sys.exit(0)


def handle_echo(parts, stdout_stream, stderr_stream):
    print(" ".join(parts[1:]), file=stdout_stream)


def handle_pwd(parts, stdout_stream, stderr_stream):
    print(os.getcwd(), file=stdout_stream)


def handle_cd(parts, stdout_stream, stderr_stream):
    if len(parts) < 2:
        return

    path = parts[1]

    # Handle "~"
    if path == "~":
        path = os.environ.get("HOME")

    if os.path.isdir(path):
        os.chdir(path)
    else:
        print(
            f"cd: {parts[1]}: No such file or directory",
            file=stderr_stream
        )


def find_executable(cmd):
    path_dirs = os.environ.get("PATH", "").split(":")

    for directory in path_dirs:
        full_path = os.path.join(directory, cmd)

        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path

    return None


def handle_type(parts, stdout_stream, stderr_stream):
    if len(parts) < 2:
        return

    cmd = parts[1]

    if cmd in commands:
        print(f"{cmd} is a shell builtin", file=stdout_stream)
        return

    path = find_executable(cmd)

    if path:
        print(f"{cmd} is {path}", file=stdout_stream)
    else:
        print(f"{cmd}: not found", file=stdout_stream)


commands = {
    "exit": handle_exit,
    "echo": handle_echo,
    "type": handle_type,
    "pwd": handle_pwd,
    "cd": handle_cd,
}

autocomplete_commands = ("echo", "exit")


def complete_builtin_commands(text, state):
    if readline is None or readline.get_begidx() != 0:
        return None

    matches = [
        f"{cmd} "
        for cmd in autocomplete_commands
        if cmd.startswith(text)
    ]

    if state < len(matches):
        return matches[state]

    return None


def main():
    if readline is not None:
        readline.parse_and_bind("tab: complete")
        readline.set_completer(complete_builtin_commands)

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

        # -------------------------
        # Redirection handling
        # -------------------------

        stdout_target = None
        stderr_target = None

        stdout_mode = "w"
        stderr_mode = "w"

        # stdout overwrite
        if ">" in parts:
            idx = parts.index(">")
            stdout_target = parts[idx + 1]
            stdout_mode = "w"
            parts = parts[:idx]

        elif "1>" in parts:
            idx = parts.index("1>")
            stdout_target = parts[idx + 1]
            stdout_mode = "w"
            parts = parts[:idx]

        # stdout append
        elif ">>" in parts:
            idx = parts.index(">>")
            stdout_target = parts[idx + 1]
            stdout_mode = "a"
            parts = parts[:idx]

        elif "1>>" in parts:
            idx = parts.index("1>>")
            stdout_target = parts[idx + 1]
            stdout_mode = "a"
            parts = parts[:idx]

        # stderr overwrite
        elif "2>" in parts:
            idx = parts.index("2>")
            stderr_target = parts[idx + 1]
            stderr_mode = "w"
            parts = parts[:idx]

        # stderr append
        elif "2>>" in parts:
            idx = parts.index("2>>")
            stderr_target = parts[idx + 1]
            stderr_mode = "a"
            parts = parts[:idx]

        if not parts:
            continue

        cmd = parts[0]

        stdout_stream = sys.stdout
        stderr_stream = sys.stderr

        if stdout_target:
            stdout_stream = open(stdout_target, stdout_mode)

        if stderr_target:
            stderr_stream = open(stderr_target, stderr_mode)

        try:
            # -------------------------
            # Builtin commands
            # -------------------------

            if cmd in commands:
                commands[cmd](
                    parts,
                    stdout_stream,
                    stderr_stream
                )

            # -------------------------
            # External commands
            # -------------------------

            else:
                # Handle direct executable path
                if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
                    path = cmd
                else:
                    path = find_executable(cmd)

                if path:
                    subprocess.run(
                        [cmd] + parts[1:],
                        executable=path,
                        stdout=stdout_stream,
                        stderr=stderr_stream
                    )
                else:
                    print(
                        f"{cmd}: command not found",
                        file=stderr_stream
                    )

        finally:
            if stdout_target:
                stdout_stream.close()

            if stderr_target:
                stderr_stream.close()


if __name__ == "__main__":
    main()
