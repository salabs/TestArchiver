import re

CONTEXT_SEPARATOR = '|-|'
FILE_PATTERN = r"^diff --git a/(.+) b/(.+)$"
BLOCK_PATTERN = r"^@@ [-\+0-9,]+ [-\+0-9,]+ @@ (.+)$"


def main():
    changes = set()
    current_file = None

    line = input()
    while True:
        m = re.search(FILE_PATTERN, line)
        if m:
            changes.add(m.group(1))
            current_file = m.group(2)
            changes.add(current_file)

        m = re.search(BLOCK_PATTERN, line)
        if m:
            context = m.group(1)
            if context:
                changes.add('{}{}{}'.format(current_file, CONTEXT_SEPARATOR, context))

        try:
            line = input()
        except EOFError:
            break

    for change in sorted(list(changes)):
        print(change)


if __name__ == '__main__':
    main()
