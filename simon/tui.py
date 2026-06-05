"""Minimal terminal chat interface for Simon SDK — no external dependencies."""

import os
import sys
import termios
import tty

from simon.agent import Agent
from simon.agent.response import AgentResponse

_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_DIM = "\033[2m"
_RED = "\033[91m"

_EXIT_COMMANDS = {"/quit"}
_CLEAR_COMMANDS = {"/clear"}
_ALL_COMMANDS = sorted(_EXIT_COMMANDS | _CLEAR_COMMANDS)

# ANSI cursor helpers
_UP = "\033[1A"
_EL = "\033[2K"  # erase entire line
_CR = "\r"


def _read_line(prompt: str) -> str:
    """Read a line from stdin, showing command hints when the user types '/'."""

    sys.stdout.write(prompt)
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    buf: list[str] = []
    hints_visible = False

    def _redraw(hints: list[str]) -> None:
        nonlocal hints_visible
        # Erase current line
        sys.stdout.write(_CR + _EL)
        # If there were hints, erase that line too
        if hints_visible:
            sys.stdout.write(_UP + _CR + _EL)
        if hints:
            hint_str = "  ".join(f"{_CYAN}{c}{_RESET}" for c in hints)
            sys.stdout.write(f"{_DIM}  → {hint_str}{_RESET}\n")
            hints_visible = True
        else:
            hints_visible = False
        sys.stdout.write(prompt + "".join(buf))
        sys.stdout.flush()

    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)

            if ch in ("\r", "\n"):
                # Clear hints line before submitting
                if hints_visible:
                    sys.stdout.write(_CR + _EL + _UP + _CR + _EL)
                    hints_visible = False
                sys.stdout.write("\n")
                sys.stdout.flush()
                break

            elif ch == "\x03":  # Ctrl+C
                sys.stdout.write("\n")
                sys.stdout.flush()
                raise KeyboardInterrupt

            elif ch == "\x04":  # Ctrl+D / EOF
                sys.stdout.write("\n")
                sys.stdout.flush()
                raise EOFError

            elif ch == "\x09":  # Tab — autocomplete command
                text = "".join(buf)
                if text.startswith("/"):
                    matches = [c for c in _ALL_COMMANDS if c.startswith(text)]
                    if len(matches) == 1:
                        buf = list(matches[0])
                    elif len(matches) > 1:
                        # fill up to the longest common prefix
                        common = os.path.commonprefix(matches)
                        buf = list(common)
                    hints = [c for c in _ALL_COMMANDS if c.startswith("".join(buf))] if "".join(buf).startswith("/") else []
                    _redraw(hints)

            elif ch in ("\x7f", "\x08"):  # Backspace
                if buf:
                    buf.pop()
                text = "".join(buf)
                hints = (
                    [c for c in _ALL_COMMANDS if c.startswith(text)]
                    if text.startswith("/")
                    else []
                )
                _redraw(hints)

            else:
                buf.append(ch)
                text = "".join(buf)
                hints = (
                    [c for c in _ALL_COMMANDS if c.startswith(text)]
                    if text.startswith("/")
                    else []
                )
                _redraw(hints)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return "".join(buf)


def chat(
    agent: Agent | None = None,
    *,
    memory: bool = True,
    tools: list | None = None,
    model: str | None = None,
    name: str = "Simon",
) -> None:
    """Start an interactive chat loop in the terminal."""

    if agent is None:
        agent = Agent(model=model, memory=memory, tools=tools, name=name)

    print(
        f"\n{_YELLOW}{_BOLD}{'─' * 48}{_RESET}\n"
        f"{_YELLOW}{_BOLD}  {agent.name}{_RESET}\n"
        f"{_YELLOW}{_BOLD}{'─' * 48}{_RESET}\n"
        f"{_DIM}  /exit  to quit  |  /clear  to clear screen{_RESET}\n"
    )

    try:
        while True:
            try:
                user_input = _read_line(f"{_CYAN}{_BOLD}[You]{_RESET} ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in _EXIT_COMMANDS:
                print(f"\n{_DIM}Bye!{_RESET}\n")
                break

            if user_input.lower() in _CLEAR_COMMANDS:
                os.system("clear")
                continue

            try:
                response: AgentResponse = agent.run(user_input)
                print(f"\n{_GREEN}{_BOLD}[{agent.name}]{_RESET} {response.text}\n")
                if response.usage:
                    u = response.usage
                    print(
                        f"{_DIM}  tokens — input: {u.input_tokens}  "
                        f"output: {u.output_tokens}  total: {u.total_tokens}{_RESET}\n"
                    )
            except Exception as exc:
                print(f"\n{_RED}Error: {exc}{_RESET}\n")

    except KeyboardInterrupt:
        print(f"\n\n{_DIM}Bye!{_RESET}\n")
