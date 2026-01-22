#!/usr/bin/env python3.14
import re, sys, os, time
from colorama import init, Fore, Style
init()
del init


class BrainFuckSharp:
    # =========================
    #   BF# STD ERROR SYSTEM
    # =========================
    class std:
        class err:
            @classmethod
            def new(cls, *args, sep=" ", end="\n", color=Fore.RED + Style.BRIGHT):
                self = cls()
                self.write = lambda: cls.write(*args, sep=sep, end=end, color=color)
                return self

            @staticmethod
            def write(*args, sep=" ", end="\n", color=Fore.RED + Style.BRIGHT):
                text = sep.join(map(str, args)) + end
                sys.stderr.write(color + text + Style.RESET_ALL)
                sys.stderr.flush()
    
BrainFuckSharp.__name__ = "BrainFuck#"


class Interpreter:
    # =========================
    #   LEXER CONSTANTS
    # =========================
    HEX = r'[0-9A-Fa-f]'  # SIN +

    # =========================
    #   INIT
    # =========================
    def __init__(self, cells_size=30000):
        self.cells_size = cells_size
        self.cells = [0] * cells_size

    # =========================
    #   IMPORTS
    # =========================
    @staticmethod
    def parse_imports(code, base_path=None):
        imports = re.findall(r'@\s*([^;]+);', code)
        for module in imports:
            module_path = module if base_path is None else os.path.join(base_path, module)
            if not os.path.isfile(module_path):
                raise ImportError(f"Module '{module}' not found")

            with open(module_path, "r", encoding="utf-8") as f:
                module_code = f.read()

            code = re.sub(r'@\s*' + re.escape(module) + r';', module_code, code)
        return code

    # =========================
    #   EXPANSIONS (+HEX -HEX =HEX)
    # =========================
    @staticmethod
    def parse_to_standar(code):
        code = re.sub(
            r"\+([0-9A-Fa-f]+)",
            lambda m: "+" * int(m.group(1), 16),
            code
        )
        code = re.sub(
            r"\-([0-9A-Fa-f]+)",
            lambda m: "-" * int(m.group(1), 16),
            code
        )
        code = re.sub(
            r"\=([0-9A-Fa-f]+)",
            lambda m: f"[-]{'+' * int(m.group(1), 16)}",
            code
        )
        return code

    # =========================
    #   PRE-PARSE
    # =========================
    @staticmethod
    def parse(code, base_path=None):
        code = code or ""

        # comments
        code = re.sub(r"\|[^|]*\|", "", code, flags=re.DOTALL)
        code = re.sub(r"\|.*", "", code)

        # imports
        depth = 0
        while re.search(r'@\s*([^;]+);', code):
            code = Interpreter.parse_imports(code, base_path)
            depth += 1
            if depth > 0xFFF:
                BrainFuckSharp.std.err.write("ImportError: Infinite import loop")
                sys.exit(1)

        return Interpreter.parse_to_standar(code)

    # =========================
    #   TOKENIZER (HEX REAL)
    # =========================
    @staticmethod
    def tokenize(code):
        H = Interpreter.HEX
        token_re = (
            rf'[+\-<>\[\].,%!?^#\{{\}}\(\)]'
            rf'|\${H}+'
            rf'|&{H}+'
            rf'|\*{H}+'
            rf'|/{H}+/'
            rf'|~{H}+'
            rf'|"(?:[^"]|\\.)*"'
            rf'|r`[^`]*`'
            rf'|w`[^`]*`'
        )
        return re.findall(token_re, code)

    # =========================
    #   VM CORE
    # =========================
    @staticmethod
    def run(code=None, cells_size=30000):
        cells = [0] * cells_size
        stack = []
        ptr = 0

        tokens = Interpreter.tokenize(Interpreter.parse(code))
        loop_stack = [[], []]
        i = 0

        while i < len(tokens):
            t = tokens[i]

            match t:
                case '+': cells[ptr] = (cells[ptr] + 1) % sys.maxunicode
                case '-': cells[ptr] = (cells[ptr] - 1) % sys.maxunicode
                case '>': ptr = (ptr + 1) % cells_size
                case '<': ptr = (ptr - 1) % cells_size
                case '.': print(chr(cells[ptr]), end="")
                case ',': cells[ptr] = ord(input()[:1] or '\0')

                case '[':
                    if cells[ptr] == 0:
                        d = 1
                        while d:
                            i += 1
                            if tokens[i] == '[': d += 1
                            elif tokens[i] == ']': d -= 1
                    else:
                        loop_stack[0].append(i)

                case ']':
                    if cells[ptr] != 0:
                        i = loop_stack[0][-1]
                    else:
                        loop_stack[0].pop()

                case '{':
                    if cells[ptr] != 0:
                        d = 1
                        while d:
                            i += 1
                            if tokens[i] == '{': d += 1
                            elif tokens[i] == '}': d -= 1
                    else:
                        loop_stack[1].append(i)

                case '}':
                    if cells[ptr] == 0:
                        i = loop_stack[1][-1]
                    else:
                        loop_stack[1].pop()

                case '^': stack.insert(0, cells[ptr])
                case '!': cells[ptr] = stack.pop(0)
                case '?': cells[ptr] = stack[0]
                case '#': stack.reverse()
                case '%': return cells

                case _:
                    op = t[0]

                    if op == '$':
                        time.sleep(int(t[1:], 16) / 1000)

                    elif op == '&':
                        n = int(t[1:], 16)
                        if n == 0:
                            ptr = cells[ptr] % cells_size
                        else:
                            stack[n - 1] = cells[ptr]

                    elif op == '*':
                        n = int(t[1:], 16)
                        cells[ptr] = ptr if n == 0 else stack[n - 1]

                    elif op == '"':
                        stack.append(t[1:-1])

                    elif op == '/':
                        BrainFuckSharp.std.err.write(stack[int(t[1:-1], 16) - 1])

                    elif op == '~':
                        sys.exit(int(t[1:], 16))

                    elif op == 'r':
                        with open(t[2:-1], "r", encoding="utf-8") as f:
                            stack.append(f.read())

                    elif op == 'w':
                        with open(t[2:-1], "w", encoding="utf-8") as f:
                            f.write(str(stack.pop(0)))

            i += 1

        return cells

    # =========================
    #   VERIFY (PURE)
    # =========================
    @staticmethod
    def verify(code=None, cells_size=30000):
        try:
            Interpreter.run(code, cells_size)
            return []
        except SystemExit as e:
            if e.code:
                return [BrainFuckSharp.std.err.new(f"ExitError: {e.code}")]
            return []
        except Exception as e:
            return [BrainFuckSharp.std.err.new(f"VerifyError: {e}")]

    # =========================
    #   CALL
    # =========================
    def __call__(self, code=None, returnCells=False, verify=False) -> Interpreter | list:
        if verify:
            errs = self.verify(code, self.cells_size)
            if errs:
                for e in errs:
                    e.write()
                sys.exit(1)

        self.cells = self.run(code, self.cells_size)
        return self.cells if returnCells else self


runner = type("bf#", (object,), {
    "run": staticmethod(lambda code, cells_size=30000, verify=False: Interpreter(cells_size)(code, True, verify)),
    "__call__": lambda self, code=None, cells_size=30000, returnCells=False, verify=False: Interpreter(cells_size)(code, returnCells, verify)
})


# =========================
#   CLI
# =========================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        BrainFuckSharp.std.err.write("Uso: python bfsi.py archivo.bfs [--verify]")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        code = f.read()

    if "--verify" in sys.argv:
        Interpreter().verify(code)
    else:
        Interpreter.run(code)
