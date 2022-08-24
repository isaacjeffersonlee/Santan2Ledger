# https://ansi.gabebanks.net/
def red(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[31;1m"
    return escape_code + text + "\033[0m"


def gray(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[90;1m"  # Technically "bright black"
    return escape_code + text + "\033[0m"


def white(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[37;1m"
    return escape_code + text + "\033[0m"


def green(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[32;1m"
    return escape_code + text + "\033[0m"


def yellow(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[33;1m"
    return escape_code + text + "\033[0m"


def blue(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[34;1m"
    return escape_code + text + "\033[0m"


def magenta(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[35;1m"
    return escape_code + text + "\033[0m"


def cyan(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[36;1m"
    return escape_code + text + "\033[0m"

