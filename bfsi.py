#!/usr/bin/env python3
import sys, os, time

# =========================
# CONFIG
# =========================
CELL_BITS = 8
CELL_MASK = (1 << CELL_BITS) - 1
DEFAULT_CELLS = 30000

# =========================
# ERR SYSTEM
# =========================
class BFErr:
    @staticmethod
    def die(msg, end="\n"):
        sys.stderr.write(msg + end)
        sys.exit(1)

# =========================
# PREPARSE
# =========================
def strip_comments(code: str) -> str:
    out = []
    i = 0
    n = len(code)
    while i < n:
        if code[i] == '|':
            i += 1
            while i < n and code[i] != '|':
                i += 1
            i += 1
        else:
            out.append(code[i])
            i += 1
    return "".join(out)

def parse_imports(code: str, base=".", stack=None, cache=None) -> str:
    if stack is None:
        stack = set()
    if cache is None:
        cache = {}

    out = []
    i = 0
    n = len(code)

    while i < n:
        if code[i] == '@':
            i += 1
            start = i
            while i < n and code[i] != ';':
                i += 1
            path = code[start:i].strip()
            i += 1

            full = os.path.abspath(os.path.join(base, path))
            if full in stack:
                BFErr.die(f"ImportError: circular import: {path}")
            if full in cache:
                out.append(cache[full])
                continue
            if not os.path.isfile(full):
                BFErr.die(f"ImportError: {path}")

            stack.add(full)
            with open(full, "r", encoding="utf8") as f:
                content = strip_comments(f.read())
                expanded = parse_imports(content, os.path.dirname(full), stack, cache)
            stack.remove(full)
            cache[full] = expanded
            out.append(expanded)
        else:
            out.append(code[i])
            i += 1

    return "".join(out)

def expand_hex(code: str) -> str:
    out = []
    i = 0
    n = len(code)
    while i < n:
        c = code[i]
        if c in "+-=" and i + 1 < n and code[i+1].isalnum():
            j = i + 1
            while j < n and code[j].isalnum():
                j += 1
            val = int(code[i+1:j], 16)
            if c == '+':
                out.append('+' * val)
            elif c == '-':
                out.append('-' * val)
            else:
                out.append('[-]' + '+' * val)
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)

# =========================
# TOKENIZER
# =========================
OPS = set("+-<>[].,%!?^#{}")
def tokenize(code: str):
    tokens = []
    i = 0
    n = len(code)
    while i < n:
        c = code[i]
        if c in OPS:
            tokens.append((c, None))
            i += 1
        elif c == '$':
            i += 1
            j = i
            while j < n and code[j].isalnum():
                j += 1
            tokens.append(('$', int(code[i:j], 16)))
            i = j
        elif c == '~':
            i += 1
            j = i
            while j < n and code[j].isalnum():
                j += 1
            tokens.append(('~', int(code[i:j], 16)))
            i = j
        elif c == '"':
            i += 1
            start = i
            while code[i] != '"':
                i += 1
            tokens.append(('"', code[start:i]))
            i += 1
        else:
            i += 1
    return tokens

# =========================
# COMPILE JUMPS
# =========================
def compile(tokens):
    jumps = {}
    stack = []
    stack_inv = []
    for i, (op, _) in enumerate(tokens):
        if op == '[':
            stack.append(i)
        elif op == ']':
            j = stack.pop()
            jumps[i] = j
            jumps[j] = i
        elif op == '{':
            stack_inv.append(i)
        elif op == '}':
            j = stack_inv.pop()
            jumps[i] = j
            jumps[j] = i
    if stack or stack_inv:
        BFErr.die("SyntaxError: unbalanced loop")
    return jumps

# =========================
# VM
# =========================
def run(code: str, cells_size=DEFAULT_CELLS):
    code = strip_comments(code)
    code = parse_imports(code)
    code = expand_hex(code)
    tokens = tokenize(code)
    jumps = compile(tokens)

    cells = [0] * cells_size
    stack = []
    ptr = 0
    ip = 0

    while ip < len(tokens):
        op, arg = tokens[ip]

        if op == '+':
            cells[ptr] = (cells[ptr] + 1) & CELL_MASK
        elif op == '-':
            cells[ptr] = (cells[ptr] - 1) & CELL_MASK
        elif op == '>':
            ptr = (ptr + 1) % cells_size
        elif op == '<':
            ptr = (ptr - 1) % cells_size
        elif op == '.':
            sys.stdout.write(chr(cells[ptr]))
        elif op == ',':
            data = sys.stdin.read(1)
            cells[ptr] = ord(data) & CELL_MASK if data else 0
        elif op == '[' and cells[ptr] == 0:
            ip = jumps[ip]
        elif op == ']' and cells[ptr] != 0:
            ip = jumps[ip]
        elif op == '{' and cells[ptr] != 0:
            ip = jumps[ip]
        elif op == '}' and cells[ptr] == 0:
            ip = jumps[ip]
        elif op == '^':
            stack.append(cells[ptr])
        elif op == '!':
            cells[ptr] = stack.pop()
        elif op == '?':
            cells[ptr] = stack[-1]
        elif op == '#':
            stack.reverse()
        elif op == '$':
            time.sleep(arg / 1000)
        elif op == '"':
            stack.append(arg)
        elif op == '%':
            return cells
        elif op == '~':
            sys.exit(arg)

        ip += 1

    return cells

# =========================
# CLI
# =========================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        BFErr.die("Uso: bfsharp archivo.bfs")
    with open(sys.argv[1], "r", encoding="utf8") as f:
        run(f.read())
