"""Built-in workspace file and shell utility tools for zero-gravity agents."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
import fnmatch


def read_file(path: str) -> str:
    """Read the content of a file at the given relative or absolute path.

    Args:
        path: The path of the file to read.

    Returns:
        The text content of the file.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return p.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    """Write or overwrite the content to a file at the given path.

    Args:
        path: The path of the file to write to.
        content: The text content to write.

    Returns:
        A success message.
    """
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Successfully wrote to {path}"


def edit_file(path: str, target: str, replacement: str) -> str:
    """Edit a file by replacing a target string with a replacement string.

    Args:
        path: The path of the file to edit.
        target: The exact string block to replace.
        replacement: The string block to replace the target with.

    Returns:
        A success message.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    content = p.read_text(encoding="utf-8")
    if target not in content:
        raise ValueError(f"Target string not found in {path}")
    new_content = content.replace(target, replacement, 1)
    p.write_text(new_content, encoding="utf-8")
    return f"Successfully edited {path}"


def run_command(cmd: str) -> str:
    """Run a shell command in the current directory and return stdout and stderr combined.

    Args:
        cmd: The shell command to execute.

    Returns:
        The output of the command.
    """
    try:
        # Run command using subprocess
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append(result.stderr)
        return "\n".join(output) if output else "Command executed with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 120 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"


def search_files(pattern: str, path: str = ".") -> str:
    """Search for files matching a glob pattern or containing a text query.

    Args:
        pattern: The file glob pattern or search query (e.g. '*.py' or a string).
        path: The start directory for the search.

    Returns:
        A string listing all matching file paths.
    """
    start_path = Path(path).resolve()
    matches = []
    
    # Try finding files by pattern
    for root, _, filenames in os.walk(start_path):
        # Exclude common directories to speed up
        if any(ignored in root for ignored in [".git", ".venv", "__pycache__", ".zg"]):
            continue
        for filename in fnmatch.filter(filenames, pattern):
            rel_path = os.path.relpath(os.path.join(root, filename), start_path)
            matches.append(rel_path)

    # If no file matches by glob, treat pattern as text query and search within python/text files
    if not matches:
        for root, _, filenames in os.walk(start_path):
            if any(ignored in root for ignored in [".git", ".venv", "__pycache__", ".zg"]):
                continue
            for filename in filenames:
                if not filename.endswith((".py", ".md", ".json", ".yaml", ".txt")):
                    continue
                file_path = os.path.join(root, filename)
                try:
                    content = Path(file_path).read_text(encoding="utf-8")
                    if pattern in content:
                        rel_path = os.path.relpath(file_path, start_path)
                        matches.append(rel_path)
                except Exception:
                    continue

    if not matches:
        return "No matches found."
    return "\n".join(matches)


def list_directory(path: str = ".") -> str:
    """List the contents of the given directory.

    Args:
        path: The directory path to list.

    Returns:
        A list of directory contents.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not p.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    contents = []
    for item in p.iterdir():
        if item.name in [".git", "__pycache__"]:
            continue
        item_type = "DIR" if item.is_dir() else "FILE"
        contents.append(f"{item_type:4} {item.name}")
    
    if not contents:
        return "Directory is empty."
    return "\n".join(sorted(contents))
