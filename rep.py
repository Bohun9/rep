import sys


class NFANode:
    def __init__(self):
        self.edges = {}

    def get_edges(self, c):
        if c not in self.edges:
            return set()
        else:
            return self.edges[c]

    def add_edge(self, x, c):
        if c not in self.edges:
            self.edges[c] = {x}
        else:
            self.edges[c] |= {x}


class NFA:
    def __init__(self, start, final):
        self.start = start
        self.final = final


class REOr:
    def __init__(self, r1, r2):
        self.r1 = r1
        self.r2 = r2

    def __str__(self):
        return f"({self.r1}|{self.r2})"

    def to_nfa(self):
        nfa1 = self.r1.to_nfa()
        nfa2 = self.r2.to_nfa()
        start = NFANode()
        final = NFANode()
        start.add_edge(nfa1.start, None)
        start.add_edge(nfa2.start, None)
        nfa1.final.add_edge(final, None)
        nfa2.final.add_edge(final, None)
        return NFA(start, final)


class REConcat:
    def __init__(self, r1, r2):
        self.r1 = r1
        self.r2 = r2

    def __str__(self):
        return f"({self.r1}{self.r2})"

    def to_nfa(self):
        nfa1 = self.r1.to_nfa()
        nfa2 = self.r2.to_nfa()
        nfa1.final.add_edge(nfa2.start, None)
        return NFA(nfa1.start, nfa2.final)


class REStar:
    def __init__(self, r):
        self.r = r

    def __str__(self):
        return f"{self.r}*"

    def to_nfa(self):
        nfa = self.r.to_nfa()
        start = NFANode()
        final = NFANode()
        start.add_edge(final, None)
        start.add_edge(nfa.start, None)
        nfa.final.add_edge(final, None)
        nfa.final.add_edge(nfa.start, None)
        return NFA(start, final)


class RESymbol:
    def __init__(self, c):
        self.c = c

    def __str__(self):
        return f"{self.c}"

    def to_nfa(self):
        start = NFANode()
        final = NFANode()
        start.add_edge(final, self.c)
        return NFA(start, final)


parser_index = 0

reserved_symbols = {"|", "*", ")"}


def parser_error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def lookahead():
    if parser_index >= len(re_str):
        return None
    else:
        return re_str[parser_index]


def get_char():
    global parser_index
    c = lookahead()
    parser_index += 1
    return c


def parse_re():
    r = parse_concat()
    match lookahead():
        case "|":
            get_char()
            return REOr(r, parse_re())
        case _:
            return r


def parse_concat():
    r1 = parse_star()
    match lookahead():
        case None:
            return r1
        case c if c in reserved_symbols:
            return r1
        case _:
            return REConcat(r1, parse_concat())


def parse_star():
    r = parse_atomic()
    match lookahead():
        case "*":
            get_char()
            return REStar(r)
        case _:
            return r


def parse_atomic():
    match get_char():
        case None:
            parser_error("Unexpected end of the regular expression.")
        case "(":
            re = parse_re()
            match get_char():
                case None:
                    parser_error("Unexpected end of the regular expression.")
                case ")":
                    return re
                case c:
                    parser_error(f"Expected ')' character at index {parser_index}.")
        case c:
            return RESymbol(c)


def re_matcher(text, nfa):
    reachable = set()

    def add_state(x, reachable):
        if x in reachable:
            return
        reachable |= {x}
        for y in x.get_edges(None):
            add_state(y, reachable)

    add_state(nfa.start, reachable)

    max_match = 0 if nfa.final in reachable else None

    for (i, c) in enumerate(text):
        new_reachable = set()
        for x in reachable:
            for y in x.get_edges(c):
                add_state(y, new_reachable)
        reachable = new_reachable
        if nfa.final in reachable:
            max_match = i + 1
        if not reachable:
            break

    return max_match


args = sys.argv
if len(args) < 2:
    print(f"usage: python3 {sys.argv[0]} <re> <file> ...", file=sys.stderr)
    sys.exit(1)

re_str = args[1]
files = args[2:]

re = parse_re()
nfa = re.to_nfa()

for file in files:
    with open(file) as f:
        for line in f.read().split("\n"):
            matches = []
            index = 0
            while index < len(line):
                match_len = re_matcher(line[index:], nfa)
                if match_len == None or match_len == 0:
                    index += 1
                else:
                    matches.append((index, index + match_len))
                    index += match_len
            if matches:
                for (i, c) in enumerate(line):
                    matched = any(map(lambda m: m[0] <= i and i < m[1], matches))
                    if matched:
                        print("\033[31m", end="")
                    print(c, end="")
                    if matched:
                        print("\033[0m", end="")
                print("")
