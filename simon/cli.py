"""Command-line interface for Simon SDK: `simon chat | ask | index`."""

import argparse
import sys

from simon import Agent, Planner, chat


def _cmd_chat(args: argparse.Namespace) -> int:
    chat(model=args.model)
    return 0


def _cmd_ask(args: argparse.Namespace) -> int:
    agent = Agent(model=args.model)
    print(agent.run(args.prompt))
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    agent = Agent()
    count = agent.add_knowledge(args.path)
    print(f"Indexed {count} chunk(s) from {args.path}")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    planner = Planner(agent=Agent(model=args.model, knowledge=False))
    planner.run(args.goal)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="simon", description="Simon SDK command-line interface."
    )
    parser.add_argument(
        "-m", "--model", default=None, help="Force a provider (e.g. OPENAI_MODEL)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_chat = sub.add_parser("chat", help="Start an interactive terminal chat.")
    p_chat.set_defaults(func=_cmd_chat)

    p_ask = sub.add_parser("ask", help="Run a single prompt and print the answer.")
    p_ask.add_argument("prompt", help="The prompt to send to the agent.")
    p_ask.set_defaults(func=_cmd_ask)

    p_index = sub.add_parser("index", help="Index a file or folder into the knowledge base.")
    p_index.add_argument("path", help="File or directory path to index.")
    p_index.set_defaults(func=_cmd_index)

    p_plan = sub.add_parser("plan", help="Decompose a goal into tasks and run them.")
    p_plan.add_argument("goal", help="The goal to plan and execute.")
    p_plan.set_defaults(func=_cmd_plan)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
