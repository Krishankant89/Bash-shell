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
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)

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


completion_specs = {}


def handle_complete(parts, stdout_stream, stderr_stream):
    if len(parts) < 2:
        return

    if parts[1] == "-C" and len(parts) >= 4:
        completer_script = parts[2]
        command_name = parts[3]
        completion_specs[command_name] = completer_script
        return

    if parts[1] == "-p" and len(parts) >= 3:
        command_name = parts[2]
        completer_script = completion_specs.get(command_name)

        if completer_script is None:
            print(
                f"complete: {command_name}: no completion specification",
                file=stderr_stream
            )
            return

        print(
            f"complete -C '{completer_script}' {command_name}",
            file=stdout_stream
        )
    return


commands = {
    "exit": handle_exit,
    "echo": handle_echo,
    "type": handle_type,
    "pwd": handle_pwd,
    "cd": handle_cd,
    "complete": handle_complete,
}

autocomplete_commands = ("echo", "exit")
completion_cache_key = None
completion_cache_matches = []


def find_matching_executables(prefix):
    matches = set()
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)

    for directory in path_dirs:
        if not directory or not os.path.isdir(directory):
            continue

        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if (
                        entry.name.startswith(prefix)
                        and entry.is_file()
                        and os.access(entry.path, os.X_OK)
                    ):
                        matches.add(entry.name)
        except OSError:
            continue

    return matches


def find_matching_paths(partial_path):
    if "/" in partial_path:
        directory_path, prefix = partial_path.rsplit("/", 1)
        search_directory = directory_path if directory_path else "."
        completion_prefix = f"{directory_path}/"
    else:
        prefix = partial_path
        search_directory = "."
        completion_prefix = ""

    matches = set()

    try:
        with os.scandir(search_directory) as entries:
            for entry in entries:
                if not entry.name.startswith(prefix):
                    continue

                if entry.is_dir():
                    matches.add(f"{completion_prefix}{entry.name}/")
                elif entry.is_file():
                    matches.add(f"{completion_prefix}{entry.name}")
    except OSError:
        return []

    return sorted(matches)


def complete_command(text, state):
    global completion_cache_key
    global completion_cache_matches

    if readline is None:
        return None

    line_buffer = readline.get_line_buffer()
    begin_index = readline.get_begidx()
    end_index = readline.get_endidx()

    token_start = line_buffer.rfind(" ", 0, end_index) + 1
    token = line_buffer[token_start:end_index]
    prefix_before_text = token[:-len(text)] if text else token
    completion_key = (line_buffer, begin_index, end_index, text)

    if state == 0 or completion_key != completion_cache_key:
        completion_cache_key = completion_key

        if begin_index == 0:
            builtin_matches = {
                cmd
                for cmd in autocomplete_commands
                if cmd.startswith(text)
            }
            executable_matches = find_matching_executables(text)
            completion_cache_matches = sorted(
                builtin_matches | executable_matches
            )
        else:
            path_matches = find_matching_paths(token)
            completion_cache_matches = sorted(
                match[len(prefix_before_text):]
                for match in path_matches
                if match.startswith(prefix_before_text)
            )

    if state < len(completion_cache_matches):
        match = completion_cache_matches[state]
        if len(completion_cache_matches) == 1:
            if match.endswith("/"):
                return match
            return f"{match} "
        return match

    return None


def main():
    if readline is not None:
        readline.parse_and_bind("tab: complete")
        readline.set_completer(complete_command)

    while True:
        try:
            userInput = input("$ ")
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
