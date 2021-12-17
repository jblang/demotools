import petscii
import bisect
from util import to_word, to_bytes

# fmt: off
basic_tokens = (
    "END", "FOR", "NEXT", "DATA", "INPUT#", "INPUT", "DIM", "READ", "LET",
    "GOTO", "RUN", "IF", "RESTORE", "GOSUB", "RETURN", "REM", "STOP", "ON",
    "WAIT", "LOAD", "SAVE", "VERIFY", "DEF", "POKE", "PRINT#", "PRINT",
    "CONT", "LIST", "CLR", "CMD", "SYS", "OPEN", "CLOSE", "GET", "NEW",
    "TAB(", "TO", "FN", "SPC(", "THEN", "NOT", "STEP", "+", "-", "*", "/",
    "↑", "AND", "OR", ">", "=", "<", "SGN", "INT", "ABS", "USR", "FRE",
    "POS", "SQR", "RND", "LOG", "EXP", "COS", "SIN", "TAN", "ATN", "PEEK",
    "LEN", "STR$", "VAL", "ASC", "CHR$", "LEFT$", "RIGHT$", "MID$", "π"
)
# fmt: on


# fmt: off
operand_formats = {
    "#": "#{}",         # immediate
    "A": "a",           # accumulator
    "I": "",            # implied
    "s": "",            # stack
    "i": "({})",        # jmp (indirect)
    "ix": "({},x)",     # (indirect,x)
    "iy": "({}),y",     # (indirect),y
    "z": "{}",          # zeropage
    "zx": "{},x",       # zeropage,x
    "zy": "{},y",       # zeropage,y
    "a": "{}",          # absolute
    "ax": "{},x",       # absolute,x
    "ay": "{},y",       # absolute,y
    "r": "{}",          # relative
}
# fmt: on

class Opcode:
    def __init__(self, mnemonic, mode, length, cycles, variable, undocumented):
        self.mnemonic = mnemonic
        self.mode = mode
        self.length = length
        self.cycles = cycles
        self.variable = variable
        self.undocumented = undocumented

opcodes = (
    Opcode("brk", "s", 2, 7, False, False),
    Opcode("ora", "ix", 2, 6, False, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("slo", "ix", 2, 8, False, True),
    Opcode("nop", "z", 2, 3, False, True),
    Opcode("ora", "z", 2, 3, False, False),
    Opcode("asl", "z", 2, 5, False, False),
    Opcode("slo", "z", 2, 5, False, True),
    Opcode("php", "s", 1, 3, False, False),
    Opcode("ora", "#", 2, 2, False, False),
    Opcode("asl", "A", 1, 2, False, False),
    Opcode("anc", "#", 2, 2, False, True),
    Opcode("nop", "a", 3, 4, False, True),
    Opcode("ora", "a", 3, 4, False, False),
    Opcode("asl", "a", 3, 6, False, False),
    Opcode("slo", "a", 3, 6, False, True),
    Opcode("bpl", "r", 2, 2, True, False),
    Opcode("ora", "iy", 2, 5, True, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("slo", "iy", 2, 8, False, True),
    Opcode("nop", "zx", 2, 4, False, True),
    Opcode("ora", "zx", 2, 4, False, False),
    Opcode("asl", "zx", 2, 6, False, False),
    Opcode("slo", "zx", 2, 6, False, True),
    Opcode("clc", "I", 1, 2, False, False),
    Opcode("ora", "ay", 3, 4, True, False),
    Opcode("nop", "I", 1, 2, False, True),
    Opcode("slo", "ay", 3, 7, False, True),
    Opcode("nop", "ax", 3, 4, True, True),
    Opcode("ora", "ax", 3, 4, True, False),
    Opcode("asl", "ax", 3, 7, False, False),
    Opcode("slo", "ax", 3, 7, False, True),
    Opcode("jsr", "a", 3, 6, False, False),
    Opcode("and", "ix", 2, 6, False, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("rla", "ix", 2, 8, False, True),
    Opcode("bit", "z", 2, 3, False, False),
    Opcode("and", "z", 2, 3, False, False),
    Opcode("rol", "z", 2, 5, False, False),
    Opcode("rla", "z", 2, 5, False, True),
    Opcode("plp", "s", 1, 4, False, False),
    Opcode("and", "#", 2, 2, False, False),
    Opcode("rol", "A", 1, 2, False, False),
    Opcode("anc", "#", 2, 2, False, True),
    Opcode("bit", "a", 3, 4, False, False),
    Opcode("and", "a", 3, 4, False, False),
    Opcode("rol", "a", 3, 6, False, False),
    Opcode("rla", "a", 3, 6, False, True),
    Opcode("bmi", "r", 2, 2, True, False),
    Opcode("and", "iy", 2, 5, True, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("rla", "iy", 2, 8, False, True),
    Opcode("nop", "zx", 2, 4, False, True),
    Opcode("and", "zx", 2, 4, False, False),
    Opcode("rol", "zx", 2, 6, False, False),
    Opcode("rla", "zx", 2, 6, False, True),
    Opcode("sec", "I", 1, 2, False, False),
    Opcode("and", "ay", 3, 4, True, False),
    Opcode("nop", "I", 1, 2, False, True),
    Opcode("rla", "ay", 3, 7, False, True),
    Opcode("nop", "ax", 3, 4, True, True),
    Opcode("and", "ax", 3, 4, True, False),
    Opcode("rol", "ax", 3, 7, False, False),
    Opcode("rla", "ax", 3, 7, False, True),
    Opcode("rti", "s", 1, 6, False, False),
    Opcode("eor", "ix", 2, 6, False, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("sre", "ix", 2, 8, False, True),
    Opcode("nop", "z", 2, 3, False, True),
    Opcode("eor", "z", 2, 3, False, False),
    Opcode("lsr", "z", 2, 5, False, False),
    Opcode("sre", "z", 2, 5, False, True),
    Opcode("pha", "s", 1, 3, False, False),
    Opcode("eor", "#", 2, 2, False, False),
    Opcode("lsr", "A", 1, 2, False, False),
    Opcode("asr", "#", 2, 2, False, True),
    Opcode("jmp", "a", 3, 3, False, False),
    Opcode("eor", "a", 3, 4, False, False),
    Opcode("lsr", "a", 3, 6, False, False),
    Opcode("sre", "a", 3, 6, False, True),
    Opcode("bvc", "r", 2, 2, True, False),
    Opcode("eor", "iy", 2, 5, True, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("sre", "iy", 2, 8, False, True),
    Opcode("nop", "zx", 2, 4, False, True),
    Opcode("eor", "zx", 2, 4, False, False),
    Opcode("lsr", "zx", 2, 6, False, False),
    Opcode("sre", "zx", 2, 6, False, True),
    Opcode("cli", "I", 1, 2, False, False),
    Opcode("eor", "ay", 3, 4, True, False),
    Opcode("nop", "I", 1, 2, False, True),
    Opcode("sre", "ay", 3, 7, False, True),
    Opcode("nop", "ax", 3, 4, True, True),
    Opcode("eor", "ax", 3, 4, True, False),
    Opcode("lsr", "ax", 3, 7, False, False),
    Opcode("sre", "ax", 3, 7, False, True),
    Opcode("rts", "s", 1, 6, False, False),
    Opcode("adc", "ix", 2, 6, False, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("rra", "ix", 2, 8, False, True),
    Opcode("nop", "z", 2, 3, False, True),
    Opcode("adc", "z", 2, 3, False, False),
    Opcode("ror", "z", 2, 5, False, False),
    Opcode("rra", "z", 2, 5, False, True),
    Opcode("pla", "s", 1, 4, False, False),
    Opcode("adc", "#", 2, 2, False, False),
    Opcode("ror", "A", 1, 2, False, False),
    Opcode("arr", "#", 2, 2, False, True),
    Opcode("jmp", "i", 3, 5, False, False),
    Opcode("adc", "a", 3, 4, False, False),
    Opcode("ror", "a", 3, 6, False, False),
    Opcode("rra", "a", 3, 6, False, True),
    Opcode("bvs", "r", 2, 2, True, False),
    Opcode("adc", "iy", 2, 5, True, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("rra", "iy", 2, 8, False, True),
    Opcode("nop", "zx", 2, 4, False, True),
    Opcode("adc", "zx", 2, 4, False, False),
    Opcode("ror", "zx", 2, 6, False, False),
    Opcode("rra", "zx", 2, 6, False, True),
    Opcode("sei", "I", 1, 2, False, False),
    Opcode("adc", "ay", 3, 4, True, False),
    Opcode("nop", "I", 1, 2, False, True),
    Opcode("rra", "ay", 3, 7, False, True),
    Opcode("nop", "ax", 3, 4, True, True),
    Opcode("adc", "ax", 3, 4, True, False),
    Opcode("ror", "ax", 3, 7, False, False),
    Opcode("rra", "ax", 3, 7, False, True),
    Opcode("nop", "#", 2, 2, False, True),
    Opcode("sta", "ix", 2, 6, False, False),
    Opcode("nop", "#", 2, 2, False, True),
    Opcode("sax", "ix", 2, 6, False, True),
    Opcode("sty", "z", 2, 3, False, False),
    Opcode("sta", "z", 2, 3, False, False),
    Opcode("stx", "z", 2, 3, False, False),
    Opcode("sax", "z", 2, 3, False, True),
    Opcode("dey", "I", 1, 2, False, False),
    Opcode("nop", "#", 2, 2, False, True),
    Opcode("txa", "I", 1, 2, False, False),
    Opcode("ane", "#", 2, 2, False, True),
    Opcode("sty", "a", 3, 4, False, False),
    Opcode("sta", "a", 3, 4, False, False),
    Opcode("stx", "a", 3, 4, False, False),
    Opcode("sax", "a", 3, 4, False, True),
    Opcode("bcc", "r", 2, 2, True, False),
    Opcode("sta", "iy", 2, 6, False, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("sha", "ax", 3, 5, False, True),
    Opcode("sty", "zx", 2, 4, False, False),
    Opcode("sta", "zx", 2, 4, False, False),
    Opcode("stx", "zy", 2, 4, False, False),
    Opcode("sax", "zy", 2, 4, False, True),
    Opcode("tya", "I", 1, 2, False, False),
    Opcode("sta", "ay", 3, 5, False, False),
    Opcode("txs", "I", 1, 2, False, False),
    Opcode("shs", "ax", 3, 5, False, True),
    Opcode("shy", "ay", 3, 5, False, True),
    Opcode("sta", "ax", 3, 5, False, False),
    Opcode("shx", "ay", 3, 5, False, True),
    Opcode("sha", "ay", 3, 5, False, True),
    Opcode("ldy", "#", 2, 2, False, False),
    Opcode("lda", "ix", 2, 6, False, False),
    Opcode("ldx", "#", 2, 2, False, False),
    Opcode("lax", "ix", 2, 6, False, True),
    Opcode("ldy", "z", 2, 3, False, False),
    Opcode("lda", "z", 2, 3, False, False),
    Opcode("ldx", "z", 2, 3, False, False),
    Opcode("lax", "z", 2, 3, False, True),
    Opcode("tay", "I", 1, 2, False, False),
    Opcode("lda", "#", 2, 2, False, False),
    Opcode("tax", "I", 1, 2, False, False),
    Opcode("lxa", "#", 2, 2, False, True),
    Opcode("ldy", "a", 3, 4, False, False),
    Opcode("lda", "a", 3, 4, False, False),
    Opcode("ldx", "a", 3, 4, False, False),
    Opcode("lax", "a", 3, 4, False, True),
    Opcode("bcs", "r", 2, 2, True, False),
    Opcode("lda", "iy", 2, 5, True, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("lax", "iy", 2, 5, True, True),
    Opcode("ldy", "zx", 2, 4, False, False),
    Opcode("lda", "zx", 2, 4, False, False),
    Opcode("ldx", "zy", 2, 4, False, False),
    Opcode("lax", "zy", 2, 4, False, True),
    Opcode("clv", "I", 1, 2, False, False),
    Opcode("lda", "ay", 3, 4, True, False),
    Opcode("tsx", "I", 1, 2, False, False),
    Opcode("lae", "ay", 3, 4, True, True),
    Opcode("ldy", "ax", 3, 4, False, False),
    Opcode("lda", "ax", 3, 4, True, False),
    Opcode("ldx", "ay", 3, 4, True, False),
    Opcode("lax", "ay", 3, 4, True, True),
    Opcode("cpy", "#", 2, 2, False, False),
    Opcode("cmp", "ix", 2, 6, False, False),
    Opcode("nop", "#", 2, 2, False, True),
    Opcode("dcp", "ix", 2, 8, False, True),
    Opcode("cpy", "z", 2, 3, False, False),
    Opcode("cmp", "z", 2, 3, False, False),
    Opcode("dec", "z", 2, 5, False, False),
    Opcode("dcp", "z", 2, 5, False, True),
    Opcode("iny", "I", 1, 2, False, False),
    Opcode("cmp", "#", 2, 2, False, False),
    Opcode("dex", "I", 1, 2, False, False),
    Opcode("sbx", "#", 2, 2, False, True),
    Opcode("cpy", "a", 3, 4, False, False),
    Opcode("cmp", "a", 3, 4, False, False),
    Opcode("dec", "a", 3, 4, False, False),
    Opcode("dcp", "a", 3, 6, False, True),
    Opcode("bne", "r", 2, 2, True, False),
    Opcode("cmp", "iy", 2, 5, True, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("dcp", "iy", 2, 8, False, True),
    Opcode("nop", "zx", 2, 4, False, True),
    Opcode("cmp", "zx", 2, 4, False, False),
    Opcode("dec", "zx", 2, 6, False, False),
    Opcode("dcp", "zx", 2, 6, False, True),
    Opcode("cld", "I", 1, 2, False, False),
    Opcode("cmp", "ay", 3, 4, True, False),
    Opcode("nop", "I", 1, 2, False, True),
    Opcode("dcp", "ay", 3, 7, False, True),
    Opcode("nop", "ax", 3, 4, True, True),
    Opcode("cmp", "ax", 3, 4, True, False),
    Opcode("dec", "ax", 3, 7, False, False),
    Opcode("dcp", "ax", 3, 7, False, True),
    Opcode("cpx", "#", 2, 2, False, False),
    Opcode("sbc", "ix", 2, 6, False, False),
    Opcode("nop", "#", 2, 2, False, True),
    Opcode("isb", "ix", 2, 8, False, True),
    Opcode("cpx", "z", 2, 3, False, False),
    Opcode("sbc", "z", 2, 3, False, False),
    Opcode("inc", "z", 2, 5, False, False),
    Opcode("isb", "z", 2, 5, False, True),
    Opcode("inx", "I", 1, 2, False, False),
    Opcode("sbc", "#", 2, 2, False, False),
    Opcode("nop", "I", 1, 2, False, False),
    Opcode("sbc", "#", 2, 2, False, True),
    Opcode("cpx", "a", 3, 4, False, False),
    Opcode("sbc", "a", 3, 4, False, False),
    Opcode("inc", "a", 3, 6, False, False),
    Opcode("isb", "a", 3, 6, False, True),
    Opcode("beq", "r", 2, 2, True, False),
    Opcode("sbc", "iy", 2, 5, True, False),
    Opcode("jam", "I", 1, 0, False, True),
    Opcode("isb", "iy", 2, 8, False, True),
    Opcode("nop", "zx", 2, 4, False, True),
    Opcode("sbc", "zx", 2, 4, False, False),
    Opcode("inc", "zx", 2, 6, False, False),
    Opcode("isb", "zx", 2, 6, False, True),
    Opcode("sed", "I", 1, 2, False, False),
    Opcode("sbc", "ay", 3, 4, True, False),
    Opcode("nop", "I", 1, 2, False, True),
    Opcode("isb", "ay", 3, 7, False, True),
    Opcode("nop", "ax", 3, 4, True, True),
    Opcode("sbc", "ax", 3, 4, True, False),
    Opcode("inc", "ax", 3, 7, False, False),
    Opcode("isb", "ax", 3, 7, False, True),
)


class AsmInstr:
    def __init__(self, addr, data):
        self.addr = addr
        self.bytes = bytes(data)
        self.opcode = opcodes[data[0]]
        if len(data) == 3:
            self.operand = to_word(data[1:])
        elif len(data) == 2:
            self.operand = self.bytes[1]
            if self.opcode.mode == "r":
                if self.operand & 0x80:
                    self.operand = (self.operand & 0x7F) - 0x80
                self.operand += self.addr
        else:
            self.operand = None

    def format(self, symbols=None, lower=True, addr=True, bytes=True):
        if self.operand is not None:
            if symbols and self.operand in symbols:
                sym = symbols[self.operand]
            else:
                if self.opcode.length == 2:
                    if self.opcode.mode == "r":
                        sym = f"${self.operand:04x}"
                    else:
                        sym = f"${self.operand:02x}"
                elif self.opcode.length == 3:
                    sym = f"${self.operand:04x}"
                if not lower:
                    sym = sym.upper()
        else:
            sym = ""
        nem = self.opcode.mnemonic
        fmt = operand_formats[self.opcode.mode]
        if not lower:
            nem = nem.upper()
            fmt = fmt.upper()
        text = ""
        if addr:
            text += f"{self.addr:04x}  "
        if bytes:
            text += f"{self.bytes.hex(' '): <9}  "
        text += f"{nem} {fmt.format(sym)}"
        return text

    def __str__(self):
        return self.format()

    def __repr__(self):
        classname = self.__class__.__name__
        return f"{classname}(0x{self.addr:04x}, {self.bytes})"

    def __lt__(self, other):
        return self.addr < other.addr


class BasicLine:
    def __init__(self, addr, bytes):
        self.addr = addr
        self.bytes = bytes
        self.link = to_word(bytes)
        self.lineno = to_word(bytes[2:])

    def format(self, lower=False):
        line = [f"{self.lineno} "]
        for byte in self.bytes[4:-1]:
            if byte >= 0x80 and byte <= 0xCA:
                token = basic_tokens[byte - 0x80]
                line.append(token.lower() if lower else token)
            elif byte == 0xFF:
                line.append(basic_tokens[-1])  # pi
            else:
                line.append(petscii.to_unicode(bytes([byte]), lower))
        return "".join(line)

    def syscalls(self):
        addrs = []
        try:
            tok = self.bytes[4:]
            while True:
                beg = tok.index(0x9e) + 1
                while tok[beg] == 0x20:
                    beg += 1
                end = beg
                while tok[end] >= 0x30 and tok[end] <= 0x39:
                    end += 1
                addrs.append(int(tok[beg:end]))
                tok = tok[end:]
        except Exception as e:
            pass
        return addrs

    def __str__(self):
        return self.format()

    def __repr__(self):
        classname = self.__class__.__name__
        return f"{classname}(0x{self.addr:04x}, {self.bytes})"

    def __lt__(self, other):
        return self.addr < other.addr

class Data:
    def __init__(self, addr, bytes):
        self.addr = addr
        self.bytes = bytes

    def format(self):
        lines = []
        for i in range(len(0, self.data), 16):
            lines.append(f"{self.addr+i}  {self.data[i:i+16].hex(' ')}")
        return "\n".join(lines)

    def __str__(self):
        return self.format()

    def __lt__(self, other):
        return self.addr < other.addr

branchops = {'bvs', 'bcs', 'beq', 'bmi', 'bcc', 'bne', 'bpl', 'bvc', 'jsr'}

class State:
    def __init__(self):
        self.mem = bytearray(64*1024)
        self.claimed = set()
        self.blocks = []

    def load_prg(self, data):
        load = to_word(data)
        data = data[2:]
        self.mem[load:load+len(data)] = data
        if load == 0x801:
            self.parse_basic(0x801)
        
    def parse_basic(self, addr):
        prev = None
        while True:
            it = iter(self.mem[addr:])
            try:
                line = []
                for _ in range(4):
                    line.append(next(it))
                link = to_word(line)
                if link == 0:
                    break
                b = 0xFF
                while b != 0:
                    b = next(it)
                    line.append(b)
                cur = BasicLine(addr, bytes(line))
                self.insert_block(cur)
                if prev is not None:
                    prev.next = cur
                addr = link
            except StopIteration:
                break

    def trace_asm(self, start):
        heads = set()
        next = start
        while True:
            op = opcodes[self.mem[next]]
            instr = AsmInstr(next, self.mem[next:next+op.length])
            next += op.length
            instaddrs = set(range(instr.addr, next))
            if (
                op.mnemonic in ("rts", "brk") or 
                op.undocumented or 
                self.claimed & instaddrs
            ):
                if len(heads) > 0:
                    next = heads.pop()
                else:
                    break
            else:
                self.claimed.update(instaddrs)
                self.insert_block(instr)
                if op.mnemonic == "jmp":
                    if op.mode == "a":
                        next = instr.operand
                    elif op.mode == "i":
                        next = to_word(self.mem[instr.operand])
                elif op.mnemonic in branchops:
                    heads.add(instr.operand)

    def insert_block(self, block):
        bisect.insort_right(self.blocks, block)

    def __str__(self):
        return "\n".join(str(b) for b in self.blocks)