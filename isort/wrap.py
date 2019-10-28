import copy
import re
from typing import Any, Dict, List, Sequence

from .wrap_modes import WrapModes as Modes
from .wrap_modes import formatter_from_string


def import_statement(
    import_start: str,
    from_imports: List[str],
    comments: Sequence[str],
    config: Dict[str, Any],
    line_separator: str,
) -> str:
    """Returns a multi-line wrapped form of the provided from import statement."""
    formatter = formatter_from_string(config["multi_line_output"].name)
    dynamic_indent = " " * (len(import_start) + 1)
    indent = config["indent"]
    line_length = config["wrap_length"] or config["line_length"]
    import_statement = formatter(
        statement=import_start,
        imports=copy.copy(from_imports),
        white_space=dynamic_indent,
        indent=indent,
        line_length=line_length,
        comments=comments,
        line_separator=line_separator,
        comment_prefix=config["comment_prefix"],
        include_trailing_comma=config["include_trailing_comma"],
        remove_comments=config["ignore_comments"],
    )
    if config["balanced_wrapping"]:
        lines = import_statement.split(line_separator)
        line_count = len(lines)
        if len(lines) > 1:
            minimum_length = min(len(line) for line in lines[:-1])
        else:
            minimum_length = 0
        new_import_statement = import_statement
        while len(lines[-1]) < minimum_length and len(lines) == line_count and line_length > 10:
            import_statement = new_import_statement
            line_length -= 1
            new_import_statement = formatter(
                statement=import_start,
                imports=copy.copy(from_imports),
                white_space=dynamic_indent,
                indent=indent,
                line_length=line_length,
                comments=comments,
                line_separator=line_separator,
                comment_prefix=config["comment_prefix"],
                include_trailing_comma=config["include_trailing_comma"],
                remove_comments=config["ignore_comments"],
            )
            lines = new_import_statement.split(line_separator)
    if import_statement.count(line_separator) == 0:
        return _wrap_line(import_statement, line_separator, config)
    return import_statement


def line(line: str, line_separator: str, config: Dict[str, Any]) -> str:
    """Returns a line wrapped to the specified line-length, if possible."""
    wrap_mode = config["multi_line_output"]
    if len(line) > config["line_length"] and wrap_mode != Modes.NOQA:  # type: ignore
        line_without_comment = line
        comment = None
        if "#" in line:
            line_without_comment, comment = line.split("#", 1)
        for splitter in ("import ", ".", "as "):
            exp = r"\b" + re.escape(splitter) + r"\b"
            if re.search(exp, line_without_comment) and not line_without_comment.strip().startswith(
                splitter
            ):
                line_parts = re.split(exp, line_without_comment)
                if comment:
                    _comma_maybe = "," if config["include_trailing_comma"] else ""
                    line_parts[-1] = f"{line_parts[-1].strip()}{_comma_maybe}  #{comment}"
                next_line = []
                while (len(line) + 2) > (
                    config["wrap_length"] or config["line_length"]
                ) and line_parts:
                    next_line.append(line_parts.pop())
                    line = splitter.join(line_parts)
                if not line:
                    line = next_line.pop()

                cont_line = _wrap_line(
                    config["indent"] + splitter.join(next_line).lstrip(), line_separator, config
                )
                if config["use_parentheses"]:
                    if splitter == "as ":
                        output = f"{line}{splitter}{cont_line.lstrip()}"
                    else:
                        _comma = "," if config["include_trailing_comma"] and not comment else ""
                        if wrap_mode in (
                            Modes.VERTICAL_HANGING_INDENT,  # type: ignore
                            Modes.VERTICAL_GRID_GROUPED,  # type: ignore
                        ):
                            _separator = line_separator
                        else:
                            _separator = ""
                        output = (
                            f"{line}{splitter}({line_separator}{cont_line}{_comma}{_separator})"
                        )
                    lines = output.split(line_separator)
                    if config["comment_prefix"] in lines[-1] and lines[-1].endswith(")"):
                        line, comment = lines[-1].split(config["comment_prefix"], 1)
                        lines[-1] = line + ")" + config["comment_prefix"] + comment[:-1]
                    return line_separator.join(lines)
                return f"{line}{splitter}\\{line_separator}{cont_line}"
    elif len(line) > config["line_length"] and wrap_mode == Modes.NOQA:  # type: ignore
        if "# NOQA" not in line:
            return f"{line}{config['comment_prefix']} NOQA"

    return line


_wrap_line = line
