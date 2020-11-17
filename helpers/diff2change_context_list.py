#!/usr/bin/env python

import argparse
import re

DESCRIPTION = """
Tool for listing changed files and/or code contexts from a git diff.
The output can be used as test run metadata or input for ChangeEngine.
"""

USAGE_EXAMPLE = """
Example usage: git diff | diff2change_context_list.py
"""

DEFAULT_CONTEXT_SEPARATOR = '|-|'
FILE_PATTERN = r"^diff --git a/(.+) b/(.+)$"
BLOCK_PATTERN = r"^@@ [-\+0-9,]+ [-\+0-9,]+ @@ (.+)$"


def main():
    args = argument_parser().parse_args()

    changes = set()
    current_file = None

    line = input()
    while True:
        match = re.search(FILE_PATTERN, line)
        if match:
            old_file = match.group(1)
            if args.files:
                changes.add(old_file)
            current_file = match.group(2)
            if args.files:
                changes.add(current_file)

        if args.change_context:
            match = re.search(BLOCK_PATTERN, line)
            if match:
                change_context = match.group(1)
                if change_context:
                    changes.add('{}{}{}'.format(current_file, args.separator, change_context))

        try:
            line = input()
        except EOFError:
            break

    for change in sorted(list(changes)):
        print(change)


def argument_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=USAGE_EXAMPLE)
    parser.add_argument('--no-files', dest='files', action='store_false',
                        help='Do not list files')
    parser.add_argument('--no-change-context', dest='change_context', action='store_false',
                        help='Do not list change contexts')
    parser.add_argument('--separator', dest='separator', default=DEFAULT_CONTEXT_SEPARATOR,
                        help='Context separator string used between file name and context')
    return parser


if __name__ == '__main__':
    main()
