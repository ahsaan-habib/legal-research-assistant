from __future__ import annotations

import argparse

from . import retrieve
from .consult import consult
from .present import render


def main() -> None:
    ap = argparse.ArgumentParser(prog="legal")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index")
    a = sub.add_parser("ask")
    a.add_argument("description")
    a.add_argument("-j", "--jurisdiction")
    args = ap.parse_args()
    if args.cmd == "index":
        print(f"indexed {retrieve.index()} provisions: {', '.join(retrieve.jurisdictions())}")
    else:
        print(render(consult(args.description, args.jurisdiction)))


if __name__ == "__main__":
    main()
