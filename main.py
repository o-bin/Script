#!/usr/bin/env python3
import sys
import os
import re

# =====================================================================
# 1. LEXER (Analizador Léxico)
# =====================================================================

TOKEN_SPEC = [
    ('COMMENT',  r'//.*'),
    ('FLOAT',    r'\d+\.\d+'),                  ('INTEGER',  r'\d+'),
    ('STRING',   r'"(?:\\.|[^"\\])*"'),
    ('INC',      r'\+\+'),
    ('DEC',      r'--'),
    ('LE',       r'<='),
    ('GE',       r'>='),
    ('EQ',       r'=='),
    ('NE',       r'!='),
    ('LT',       r'<'),
    ('GT',       r'>'),
    ('ASSIGN',   r'='),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('MUL',      r'\*'),
    ('DIV',      r'/'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('COLON',    r':'),
    ('SEMI',     r';'),
    ('COMMA',    r','),
    ('DOT',      r'\.'),
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),
    ('NEWLINE',  r'\n'),
    ('SKIP',     r'[ \t\r]+'),
    ('MISMATCH', r'.'),
]

KEYWORDS = {
    'var', 'fn', 'struct', 'if', 'else', 'or', 'while',
    'true', 'false', 'return'
}

STRUCT_TYPES = {'string', 'integer', 'float'}

class Token:
    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line})"

def tokenize(code):
    tokens = []
    line_num = 1
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NEWLINE':
            line_num += 1
        elif kind in ('SKIP', 'COMMENT'):
            continue
        elif kind == 'ID':
            if value in KEYWORDS:
                kind = value.upper()
            elif value in STRUCT_TYPES:
                kind = 'TYPE'
            tokens.append(Token(kind, value, line_num))
        elif kind == 'MISMATCH':
            raise SyntaxError(f"[Línea {line_num}] Carácter inesperado: {repr(value)}")
        else:
            tokens.append(Token(kind, value, line_num))
    tokens.append(Token('EOF', '', line_num))
    return tokens


# =====================================================================
# 2. PARSER & AST (Analizador Sintáctico)
# =====================================================================

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def eat(self, token_type=None):
        tok = self.current()
        if token_type and tok.type != token_type:
            raise SyntaxError(
                f"[Línea {tok.line}] Se esperaba '{token_type}', pero se obtuvo '{tok.type}' ({repr(tok.value)})"
            )
        self.pos += 1
        return tok

    def match(self, *token_types):
        if self.current().type in token_types:
            return self.eat()
        return None

    def parse(self):
        stmts = []
        while self.current().type != 'EOF':
            stmts.append(self.statement())
        return ('PROGRAM', stmts)

    def statement(self):
        tok_type = self.current().type
        if tok_type == 'VAR':
            return self.var_decl()
        elif tok_type == 'FN':
            return self.fn_decl()
        elif tok_type == 'STRUCT':
            return self.struct_decl()
        elif tok_type == 'IF':
            return self.if_stmt()
        elif tok_type == 'WHILE':
            return self.while_stmt()
        elif tok_type == 'RETURN':
            return self.return_stmt()
        else:
            return self.expr_or_assign_stmt()

    def var_decl(self):
        self.eat('VAR')
        name = self.eat('ID').value
        self.eat('ASSIGN')
        expr = self.expression()
        self.eat('SEMI')
        return ('VAR_DECL', name, expr)

    def fn_decl(self):
        self.eat('FN')
        name = self.eat('ID').value
        self.eat('LPAREN')
        params = []
        if self.current().type != 'RPAREN':
            params.append(self.eat('ID').value)
            while self.match('COMMA'):
                params.append(self.eat('ID').value)
        self.eat('RPAREN')
        body = self.block()
        return ('FN_DECL', name, params, body)

    def struct_decl(self):
        self.eat('STRUCT')
        name = self.eat('ID').value
        self.eat('LBRACE')
        fields = []
        while self.current().type != 'RBRACE':
            field_name = self.eat('ID').value
            self.eat('COLON')
            # --- Reemplazar desde aquí ---
            if self.current().type == 'TYPE':
                field_type = self.eat('TYPE').value
            elif self.match('LBRACKET'):
                self.eat('RBRACKET')
                field_type = '[]'
            else:
                tok = self.current()
                raise SyntaxError(
                    f"[Línea {tok.line}] Tipo inválido '{tok.value}' en struct '{name}'. "
                    f"Solo se permiten: string, integer, float, []."
                )
            # --- Hasta aquí ---

            fields.append((field_name, field_type))
            self.match('COMMA')
        self.eat('RBRACE')
        self.eat('SEMI')
        return ('STRUCT_DECL', name, fields)

    def if_stmt(self):
        self.eat('IF')
        self.eat('LPAREN')
        cond = self.expression()
        self.eat('RPAREN')
        then_block = self.block()

        or_branches = []
        while self.match('OR'):
            self.eat('LPAREN')
            or_cond = self.expression()
            self.eat('RPAREN')
            or_block = self.block()
            or_branches.append((or_cond, or_block))

        else_block = None
        if self.match('ELSE'):
            else_block = self.block()

        return ('IF_STMT', cond, then_block, or_branches, else_block)

    def while_stmt(self):
        self.eat('WHILE')
        self.eat('LPAREN')
        cond = self.expression()
        self.eat('RPAREN')
        body = self.block()
        return ('WHILE_STMT', cond, body)

    def return_stmt(self):
        self.eat('RETURN')
        expr = None
        if self.current().type != 'SEMI':
            expr = self.expression()
        self.match('SEMI')
        return ('RETURN_STMT', expr)

    def block(self):
        self.eat('LBRACE')
        stmts = []
        while self.current().type != 'RBRACE':
            if self.current().type == 'EOF':
                raise SyntaxError("Fin de archivo inesperado dentro de un bloque '{ ... }'")
            stmts.append(self.statement())
        self.eat('RBRACE')
        return stmts

    def expr_or_assign_stmt(self):
        expr = self.expression()
        if self.match('ASSIGN'):
            val = self.expression()
            self.match('SEMI')
            return ('ASSIGN', expr, val)
        elif self.match('INC'):
            self.match('SEMI')
            return ('INC', expr)
        elif self.match('DEC'):
            self.match('SEMI')
            return ('DEC', expr)
        else:
            self.match('SEMI')
            return ('EXPR_STMT', expr)

    def expression(self):
        return self.comparison()

    def comparison(self):
        left = self.additive()
        while self.current().type in ('LT', 'LE', 'GT', 'GE', 'EQ', 'NE'):
            op = self.eat().value
            right = self.additive()
            left = ('BINOP', op, left, right)
        return left

    def additive(self):
        left = self.multiplicative()
        while self.current().type in ('PLUS', 'MINUS'):
            op = self.eat().value
            right = self.multiplicative()
            left = ('BINOP', op, left, right)
        return left

    def multiplicative(self):
        left = self.unary()
        while self.current().type in ('MUL', 'DIV'):
            op = self.eat().value
            right = self.unary()
            left = ('BINOP', op, left, right)
        return left

    def unary(self):
        if self.current().type == 'MINUS':
            op = self.eat().value
            return ('UNARY', op, self.unary())
        return self.postfix()

    def postfix(self):
        node = self.primary()
        while True:
            if self.match('LPAREN'):
                args = []
                if self.current().type != 'RPAREN':
                    args.append(self.expression())
                    while self.match('COMMA'):
                        args.append(self.expression())
                self.eat('RPAREN')
                node = ('CALL', node, args)
            elif self.match('DOT'):
                attr = self.eat('ID').value
                node = ('ATTR', node, attr)
                # <-- Agregar este bloque elif:
            elif self.match('LBRACKET'):
                idx = self.expression()
                self.eat('RBRACKET')
                node = ('INDEX', node, idx)
            elif self.node_is_struct_init(node):
                self.eat('LBRACE')
                init_fields = []
                while self.current().type != 'RBRACE':
                    f_name = self.eat('ID').value
                    self.eat('COLON')
                    f_val = self.expression()
                    init_fields.append((f_name, f_val))
                    self.match('COMMA')
                self.eat('RBRACE')
                node = ('STRUCT_INIT', node[1], init_fields)
            else:
                break
        return node

    def node_is_struct_init(self, node):
        """Detecta instanciación estilo Rust: Person { name: "Ana", age: 20, score: 9.5 }"""
        if node[0] != 'VAR' or self.current().type != 'LBRACE':
            return False
        if self.pos + 2 < len(self.tokens):
            t1 = self.tokens[self.pos + 1]
            t2 = self.tokens[self.pos + 2]
            if t1.type == 'RBRACE':
                return True
            if t1.type == 'ID' and t2.type == 'COLON':
                return True
        return False

    def primary(self):
        tok = self.current()
        if tok.type == 'INTEGER':
            self.eat()
            return ('INT', int(tok.value))
        elif tok.type == 'FLOAT':
            self.eat()
            return ('FLOAT', float(tok.value))
        elif tok.type == 'STRING':
            self.eat()
            return ('STR', tok.value)
        elif tok.type == 'TRUE':
            self.eat()
            return ('BOOL', True)
        elif tok.type == 'FALSE':
            self.eat()
            return ('BOOL', False)
        elif tok.type == 'ID':
            self.eat()
            return ('VAR', tok.value)
        elif tok.type == 'LPAREN':
            self.eat('LPAREN')
            expr = self.expression()
            self.eat('RPAREN')
            return expr
           # <-- Agregar este bloque elif:
        elif tok.type == 'LBRACKET':
            self.eat('LBRACKET')
            elements = []
            if self.current().type != 'RBRACKET':
                elements.append(self.expression())
                while self.match('COMMA'):
                    elements.append(self.expression())
            self.eat('RBRACKET')
            return ('ARRAY', elements)
        elif tok.type == 'TYPE':
            raise SyntaxError(
                f"[Línea {tok.line}] El tipo '{tok.value}' es exclusivo para declaraciones dentro de 'struct'."
            )
        else:
            raise SyntaxError(f"[Línea {tok.line}] Expresión inesperada: '{tok.value}' ({tok.type})")


# =====================================================================
# 3. TRANSPILER (Generador de Código Python Dinámico)
# =====================================================================

class Transpiler:
    def __init__(self):
        self.indent_level = 0
        self.in_function = False

    def indent(self):
        return "    " * self.indent_level

    def transpile(self, ast):
        lines = [
            "# --- Transpiled from .script ---",
            "def __script_fmt__(val):",
            "    if isinstance(val, list):",
            "        return ', '.join(__script_fmt__(x) for x in val)",
            "    return str(val)",
            "",
            "def __script_return__(val=None):",
            "    if val is not None:",
            "        print(val)",
            "    return val",
            "",
            "def __script_add__(a, b):",
            "    if isinstance(a, str) or isinstance(b, str):",
            "        return str(a) + str(b)",
            "    return a + b",
            ""
        ]
        for stmt in ast[1]:
            lines.append(self.visit_stmt(stmt))
        return "\n".join(lines)

    def visit_block(self, stmts):
        self.indent_level += 1
        if not stmts:
            res = f"{self.indent()}pass"
        else:
            res = "\n".join(self.visit_stmt(s) for s in stmts)
        self.indent_level -= 1
        return res

    def visit_stmt(self, node):
        ntype = node[0]
        ind = self.indent()

        if ntype == 'VAR_DECL':
            _, name, expr = node
            return f"{ind}{name} = {self.visit_expr(expr)}"

        elif ntype == 'ASSIGN':
            _, target, val = node
            return f"{ind}{self.visit_expr(target)} = {self.visit_expr(val)}"

        elif ntype == 'INC':
            _, target = node
            return f"{ind}{self.visit_expr(target)} += 1"

        elif ntype == 'DEC':
            _, target = node
            return f"{ind}{self.visit_expr(target)} -= 1"

        elif ntype == 'FN_DECL':
            _, name, params, body = node
            param_str = ", ".join(params)
            prev_fn_state = self.in_function
            self.in_function = True
            body_code = self.visit_block(body)
            self.in_function = prev_fn_state
            return f"{ind}def {name}({param_str}):\n{body_code}"

        elif ntype == 'STRUCT_DECL':
            _, name, fields = node
            type_map = {'string': 'str', 'integer': 'int', 'float': 'float'}
            lines = [f"{ind}class {name}:"]
            self.indent_level += 1
            f_ind = self.indent()

            if not fields:
                lines.append(f"{f_ind}def __init__(self): pass")
            else:
                params = ", ".join(f"{fname}=None" for fname, _ in fields)
                lines.append(f"{f_ind}def __init__(self, {params}):")
                self.indent_level += 1
                b_ind = self.indent()
                for fname, ftype in fields:
                    # py_type = type_map[ftype]
                    if ftype == 'float':
                        check = f"not isinstance({fname}, (int, float)) or isinstance({fname}, bool)"
                        conv = f"float({fname})"
                    elif ftype == 'integer':
                        check = f"not isinstance({fname}, int) or isinstance({fname}, bool)"
                        conv = f"{fname}"
                    elif ftype == '[]': # IS HERE
                        check = f"not isinstance({fname}, list)"
                        conv = f"{fname}"
                    else:
                        check = f"not isinstance({fname}, str)"
                        conv = f"{fname}"

                    lines.append(f"{b_ind}if { check }:")
                    lines.append(f"{b_ind}    raise TypeError(f\"Campo '{fname}' en struct '{name}' requiere '{ftype}'\")")
                    lines.append(f"{b_ind}self.{fname} = {conv}")
                self.indent_level -= 1

            lines.append(f"{f_ind}def __repr__(self):")
            repr_fields = "\\n".join(f"{fname}: {{__script_fmt__(self.{fname})}}" for fname, _ in fields)
            lines.append(f"{f_ind}    return f\"{repr_fields}\"")
            self.indent_level -= 1
            return "\n".join(lines)
        elif ntype == 'IF_STMT':
            _, cond, then_b, or_branches, else_b = node
            lines = [f"{ind}if {self.visit_expr(cond)}:", self.visit_block(then_b)]
            for or_cond, or_b in or_branches:
                lines.append(f"{ind}elif {self.visit_expr(or_cond)}:")
                lines.append(self.visit_block(or_b))
            if else_b is not None:
                lines.append(f"{ind}else:")
                lines.append(self.visit_block(else_b))
            return "\n".join(lines)

        elif ntype == 'WHILE_STMT':
            _, cond, body = node
            return f"{ind}while {self.visit_expr(cond)}:\n{self.visit_block(body)}"

        elif ntype == 'RETURN_STMT':
            _, expr = node
            val_code = self.visit_expr(expr) if expr is not None else "None"
            if self.in_function:
                return f"{ind}return __script_return__({val_code})"
            else:
                return f"{ind}__script_return__({val_code})"

        elif ntype == 'EXPR_STMT':
            _, expr = node
            return f"{ind}{self.visit_expr(expr)}"

        raise RuntimeError(f"Nodo de sentencia desconocido: {ntype}")

    def visit_expr(self, node):
        ntype = node[0]
        if ntype in ('INT', 'FLOAT'):
            return repr(node[1])
        elif ntype == 'STR':
            return node[1]
        elif ntype == 'BOOL':
            return "True" if node[1] else "False"
        elif ntype == 'VAR':
            return node[1]
        elif ntype == 'UNARY':
            _, op, operand = node
            return f"({op}{self.visit_expr(operand)})"
        elif ntype == 'BINOP':
            _, op, left, right = node
            if op == '+':
                return f"__script_add__({self.visit_expr(left)}, {self.visit_expr(right)})"
            return f"({self.visit_expr(left)} {op} {self.visit_expr(right)})"
        elif ntype == 'CALL':
            _, callee, args = node
            arg_str = ", ".join(self.visit_expr(a) for a in args)
            return f"{self.visit_expr(callee)}({arg_str})"
        elif ntype == 'ATTR':
            _, obj, attr = node
            return f"{self.visit_expr(obj)}.{attr}"
        elif ntype == 'STRUCT_INIT':
            _, sname, fields = node
            kwargs = ", ".join(f"{k}={self.visit_expr(v)}" for k, v in fields)
            return f"{sname}({kwargs})"
            # <-- Agregar estos dos bloques elif:
        elif ntype == 'ARRAY':
            _, elements = node
            el_str = ", ".join(self.visit_expr(e) for e in elements)
            return f"[{el_str}]"
        elif ntype == 'INDEX':
            _, target, idx = node
            return f"{self.visit_expr(target)}[{self.visit_expr(idx)}]"
            _, sname, fields = node
            kwargs = ", ".join(f"{k}={self.visit_expr(v)}" for k, v in fields)
            return f"{sname}({kwargs})"
        raise RuntimeError(f"Nodo de expresión desconocido: {ntype}")


# =====================================================================
# 4. PUNTO DE ENTRADA (CLI & Runtime)
# =====================================================================

def main():
    if len(sys.argv) != 2 or not sys.argv[1].endswith('.script'):
        print("usage: python main.py <name_of_your_file>.script")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.isfile(filepath):
        print(f"Error: file '{filepath}' not found.")
        sys.exit(1)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()

        tokens = tokenize(source_code)
        parser = Parser(tokens)
        ast = parser.parse()

        transpiler = Transpiler()
        python_code = transpiler.transpile(ast)

        # Ejecución dinámica del código transpilado
        exec_globals = {}
        exec(python_code, exec_globals)

    except Exception as e:
        print(f"Script Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
