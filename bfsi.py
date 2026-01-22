#!/usr/bin/env python3.14
import re, sys, os, time
from colorama import init, Fore, Style
init()
del init


class BrainFuckSharp:
    class std:
        class err:
            @classmethod
            def new(cls, *args, sep=" ", end="\n", color=Fore.RED + Style.BRIGHT):
                self = cls()
                self.write = lambda : cls.write(*args, sep=sep, end=end, color=color)
                return self
            
            @staticmethod
            def write(*args, sep=" ", end="\n", color=Fore.RED + Style.BRIGHT):
                text = sep.join(map(str, args)) + end
                sys.stderr.write(color + text + Style.RESET_ALL)
                sys.stderr.flush()
    
    def __init__(self, cells_size=30000):
        self.cells_size = cells_size
        self.cells = [0] * cells_size

    @staticmethod
    def parse_imports(code, base_path=None):
        imports = re.findall(r'@\s*([^;]+);', code)
        for module in imports:
            module_path = module if base_path is None else os.path.join(base_path, module)
            if not os.path.isfile(module_path):
                raise ImportError(f"Module '{module}' not found at '{module_path}'")
            with open(module_path, 'r') as f:
                module_code = f.read()
            code = re.sub(r'@\s*' + re.escape(module) + r';', module_code, code)
        return code

    @staticmethod
    def parse_to_standar(code):
        code = re.sub(r"\+(\d+)", lambda m: '+' * int(m.group(1)), code)
        code = re.sub(r"\-(\d+)", lambda m: '-' * int(m.group(1)), code)
        code = re.sub(r"=(\d+)", lambda m: f"[-]{'+'*int(m.group(1))}", code)
        return code

    @staticmethod
    def parse(code, base_path=None):
        i = 0
        code = re.sub(r"\|[^|]*\|", "", code, flags=re.DOTALL)
        code = re.sub(r"\|.*", "", code)
        
        while re.search(r'@\s*([^;]+);', code):
            code = BrainFuckSharp.parse_imports(code, base_path)
            i  += 1
            if i > 0xFFF:
                BrainFuckSharp.std.err.write("ImportError: Possible infinite import loop detected.")
                BrainFuckSharp.std.err.write("RecursionError: Maximum import depth exceeded.")
                sys.exit(1)
        code = BrainFuckSharp.parse_to_standar(code)
        return code

    @staticmethod
    def run(code=None, cells_size=None):
        if code is None:
            code = ""
        if cells_size is None:
            cells_size = 30000
        cells = [0] * cells_size
        stack = []
        ptr = 0
        i = 0
        code = BrainFuckSharp.parse(code)
        tokens = re.findall(r'[+\-<>\[\].,%!?^#\{\}\(\)]|\$\d+|&\d+|\*\d+|"(?:[^"]|\\.)*"|/\d*/|~\d+|r`[^`]*`|w`[^`]*`', code)
        loop_stack = [[], []]

        while i < len(tokens):
            token = tokens[i]
            match token:
                case '+': cells[ptr] = (cells[ptr] + 1) % sys.maxunicode
                case '-': cells[ptr] = (cells[ptr] - 1) % sys.maxunicode
                case '>': ptr = (ptr + 1) % cells_size
                case '<': ptr = (ptr - 1) % cells_size
                case '.': print(chr(cells[ptr]), end='')
                case ',': cells[ptr] = ord(input()[0])
                case '[':
                    if cells[ptr] == 0:
                        open_sqr_brackets = 1
                        while open_sqr_brackets != 0:
                            i += 1
                            if tokens[i] == '[': open_sqr_brackets += 1
                            elif tokens[i] == ']': open_sqr_brackets -= 1
                    else:
                        loop_stack[0].append(i)
                case ']':
                    if cells[ptr] != 0: i = loop_stack[0][-1]
                    else: loop_stack[0].pop()
                case '%':
                    return cells
                case '!':
                    if not stack:
                        BrainFuckSharp.std.err.write("StackError: Attempt to read and remove from an empty stack.")
                        sys.exit(1)
                    cells[ptr] = stack.pop(0)
                case '?':
                    if not stack:
                        BrainFuckSharp.std.err.write("StackError: Attempt to read from an empty stack.")
                        sys.exit(1)
                    cells[ptr] = stack[0]
                case '#':
                    if not stack:
                        BrainFuckSharp.std.err.write("StackError: Attempt to reverse an empty stack.")
                        sys.exit(1)
                    stack.reverse()
                case '{':
                    if cells[ptr] != 0:
                        open_brackets = 1
                        while open_brackets != 0:
                            i += 1
                            if tokens[i] == '{': open_brackets += 1
                            elif tokens[i] == '}': open_brackets -= 1
                    else:
                        loop_stack[1].append(i)
                case '}':
                    if cells[ptr] == 0: i = loop_stack[1][-1]
                    else: loop_stack[1].pop()
                case '(':
                    if cells[ptr] == 0:
                        open_brackets = 1
                        while open_brackets != 0:
                            i += 1
                            if tokens[i] == '(': open_brackets += 1
                            elif tokens[i] == ')': open_brackets -= 1
                case '^':
                    stack.insert(0, cells[ptr])
                case _: # "tokens" de mas de un caracter (patrones)
                    match token[0]:
                        case '$':
                            value = int(token[1:])
                            time.sleep(value / 1000)
                        case '&':
                            value = int(token[1:])
                            if value == 0:
                                ptr = cells[ptr]
                            else:
                                if len(stack) < value:
                                    BrainFuckSharp.std.err.write("StackError: Not enough values in stack for '&' operation.")
                                    sys.exit(1)
                                stack[value-1] = cells[ptr]
                        case '*':
                            value = int(token[1:])
                            if value == 0:
                                cells[ptr] = ptr
                            else:
                                if len(stack) < value:
                                    BrainFuckSharp.std.err.write("StackError: Not enough values in stack for '*' operation.")
                                    sys.exit(1)
                                cells[ptr] = stack[value - 1]
                        case '"':
                            strCont = token[1:-2]
                            stack.append(strCont)
                        case '/':
                            errIndex = int(token[1:-1])
                            if len(stack) < errIndex:
                                BrainFuckSharp.std.err.write("StackError: Not enough values in stack for '/' operation.")
                                sys.exit(1)
                            elif 1 >= errIndex:
                                BrainFuckSharp.std.err.write("StackError: '/' operation requires an index greater than 1.")
                            BrainFuckSharp.std.err.write(stack[errIndex-1])
                        case '~':
                            sys.exit(int(token[1:]) if len(token) > 1 else 0)
                        case 'r':
                            file = token[2:-1]
                            try:
                                with open(file, 'r') as f:
                                    content = f.read()
                                stack.append(content)
                            except Exception as e:
                                BrainFuckSharp.std.err.write(f"FileError: Could not read file '{file}'")
                                sys.exit(1)
                        case 'w':
                            file = token[2:-1]
                            try:
                                with open(file, 'w') as f:
                                    f.write(str(stack.pop(0)))
                            except Exception as e:
                                BrainFuckSharp.std.err.write(f"FileError: Could not write to file '{file}'")
                                sys.exit(1)
                            
                        
                
            ptr = max(0, min(cells_size - 1, ptr))
            for j, v in enumerate(cells):
                cells[j] = max(0, min(sys.maxunicode, v))     
            i += 1

        return cells
    
    @staticmethod
    def verify(code=None, cells_size=None):
        errors = []
        if code is None:
            code = ""
        if cells_size is None:
            cells_size = 30000
        cells = [0] * cells_size
        stack = []
        ptr = 0
        i = 0
        code = BrainFuckSharp.parse(code)
        tokens = re.findall(r'[+\-<>\[\].,%!?^#\{\}\(\)]|\$\d+|&\d+|\*\d+|"(?:[^"]|\\.)*"|/\d*/|~\d+|r`[^`]*`|w`[^`]*`', code)
        loop_stack = [[], []]

        while i < len(tokens):
            token = tokens[i]
            match token:
                case '+': cells[ptr] = (cells[ptr] + 1) % sys.maxunicode
                case '-': cells[ptr] = (cells[ptr] - 1) % sys.maxunicode
                case '>': ptr = (ptr + 1) % cells_size
                case '<': ptr = (ptr - 1) % cells_size
                case '[':
                    if cells[ptr] == 0:
                        open_sqr_brackets = 1
                        while open_sqr_brackets != 0:
                            i += 1
                            if tokens[i] == '[': open_sqr_brackets += 1
                            elif tokens[i] == ']': open_sqr_brackets -= 1
                    else:
                        loop_stack[0].append(i)
                case ']':
                    if cells[ptr] != 0: i = loop_stack[0][-1]
                    else: loop_stack[0].pop()
                case '%':
                    return cells
                case '!':
                    if not stack:
                        errors.append(BrainFuckSharp.std.err.new("StackError: Attempt to read and remove from an empty stack."))
                        sys.exit(1)
                    cells[ptr] = stack.pop(0)
                case '?':
                    if not stack:
                        errors.append(BrainFuckSharp.std.err.new("StackError: Attempt to read from an empty stack."))
                        sys.exit(1)
                    cells[ptr] = stack[0]
                case '#':
                    if not stack:
                        errors.append(BrainFuckSharp.std.err.new("StackError: Attempt to reverse an empty stack."))
                        sys.exit(1)
                    stack.reverse()
                case '{':
                    if cells[ptr] != 0:
                        open_brackets = 1
                        while open_brackets != 0:
                            i += 1
                            if tokens[i] == '{': open_brackets += 1
                            elif tokens[i] == '}': open_brackets -= 1
                    else:
                        loop_stack[1].append(i)
                case '}':
                    if cells[ptr] == 0: i = loop_stack[1][-1]
                    else: loop_stack[1].pop()
                case '(':
                    if cells[ptr] == 0:
                        open_brackets = 1
                        while open_brackets != 0:
                            i += 1
                            if tokens[i] == '(': open_brackets += 1
                            elif tokens[i] == ')': open_brackets -= 1
                case '^':
                    stack.insert(0, cells[ptr])
                case _: # "tokens" de mas de un caracter (patrones)
                    match token[0]:
                        case '&':
                            value = int(token[1:])
                            if value == 0:
                                ptr = cells[ptr]
                            else:
                                if len(stack) < value:
                                    errors.append(BrainFuckSharp.std.err.new("StackError: Not enough values in stack for '&' operation."))
                                    sys.exit(1)
                                stack[value-1] = cells[ptr]
                        case '*':
                            value = int(token[1:])
                            if value == 0:
                                cells[ptr] = ptr
                            else:
                                if len(stack) < value:
                                    errors.append(BrainFuckSharp.std.err.new("StackError: Not enough values in stack for '*' operation."))
                                    sys.exit(1)
                                cells[ptr] = stack[value - 1]
                        case '"':
                            strCont = token[1:-2]
                            stack.append(strCont)
                        case '/':
                            errIndex = int(token[1:-1])
                            if len(stack) < errIndex:
                                errors.append(BrainFuckSharp.std.err.new("StackError: Not enough values in stack for '/' operation."))
                            elif 1 >= errIndex:
                                errors.append(BrainFuckSharp.std.err.new("StackError: '/' operation requires an index greater than 1."))
                            errors.append(BrainFuckSharp.std.err.new(stack[errIndex-1]))
                        case '~':
                            r = int(token[1:]) if len(token) > 1 else 0 != 0
                            if r != 0:
                                errors.append(BrainFuckSharp.std.err.new(f"ExitError: Program would exit with code {r}"))
                            return errors
                        case 'r':
                            file = token[2:-1]
                            try:
                                with open(file, 'r') as f:
                                    content = f.read()
                                stack.append(content)
                            except Exception as e:
                                errors.append(BrainFuckSharp.std.err.new(f"FileError: Could not read file '{file}'"))
                                return errors
                        case 'w':
                            file = token[2:-1]
                            try:
                                with open(file, 'w') as f:
                                    f.write(str(stack.pop(0)))
                                os.rmdir(file)
                            except Exception as e:
                                errors.append(BrainFuckSharp.std.err.new(f"FileError: Could not write to file '{file}'"))
                                return errors
                        

            ptr = max(0, min(cells_size - 1, ptr))
            for j, v in enumerate(cells):
                cells[j] = max(0, min(sys.maxunicode, v))     
            i += 1
            if errors:
                return errors
        return errors

    def __call__(self, code=None, returnCells=False, verify=False):
        if not verify:
            self.cells = type(self).run(code, self.cells_size)
            return self if not returnCells else self.cells
        errors = type(self).verify(code, self.cells_size)
        if errors:
            for err in errors:
                err.write()
            sys.exit(1)
        else:
            self(code, returnCells, False)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        BrainFuckSharp.std.err.write("Uso: python bfsi.py archivo.bfs [--verify]")
        sys.exit(1)
    elif len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help", "help"):
        print("Uso: python bfsi.py archivo.bfs [--verify]")
        sys.exit(0)
    mainFile = sys.argv[1]
    with open(mainFile, 'r') as f:
        code = f.read()
    if len(sys.argv) >= 3 and ("-verify" in sys.argv[2:] or "--verify" in sys.argv[2:] or "verify" in sys.argv[2:]):
        BrainFuckSharp().__call__(code, verify=True)
        sys.exit(0)
    BrainFuckSharp.run(code)
