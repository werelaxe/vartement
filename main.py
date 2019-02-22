import re
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum

from utils import read_next_token

VARIABLE_TEMPLATE = re.compile(r"[a-zA-Z][a-zA-Z0-9]*")
NUMERIC_LITERAL_TEMPLATE = re.compile(r"-?\d+")


class VariableType(Enum):
    NOT_SET = -1
    TYPE = 0
    NUMERIC = 1
    NULL = 2

    def __str__(self):
        if self == VariableType.TYPE:
            return "type"
        elif self == VariableType.NUMERIC:
            return "value"
        elif self == VariableType.NULL:
            return ""
        else:
            return "-1!!!!!!!!!!!!!!!!!"
            # raise TranslationError("Can not translate not setted variable type")


TEMPLATE_ARG_TYPES = {
    VariableType.TYPE: "typename",
    VariableType.NUMERIC: "long long",
}


def translate_template_arg_type(arg_type: VariableType):
    if arg_type not in TEMPLATE_ARG_TYPES:
        raise TranslationError("Can not translate arg type '{}' into template parameter".format(arg_type))
    return TEMPLATE_ARG_TYPES[arg_type]


BUILT_IN_IDENTIFIERS = {
    'add': VariableType.NUMERIC,
    'sub': VariableType.NUMERIC,
    'mul': VariableType.NUMERIC,
    'div': VariableType.NUMERIC,
    'mod': VariableType.NUMERIC,
    'read': VariableType.NUMERIC,
    'print': VariableType.NULL,
    'list': VariableType.TYPE,
    'head': VariableType.NUMERIC,
    'tail': VariableType.TYPE,
    'size': VariableType.NUMERIC,
    'cons': VariableType.TYPE,
    'append': VariableType.TYPE,
    'concat': VariableType.TYPE,
    'lieq': VariableType.NUMERIC,
    'eq': VariableType.NUMERIC,
    'neq': VariableType.NUMERIC,
    'not': VariableType.NUMERIC,
    'bnot': VariableType.NUMERIC,
    'and': VariableType.NUMERIC,
    'band': VariableType.NUMERIC,
    'or': VariableType.NUMERIC,
    'bor': VariableType.NUMERIC,
    'xor': VariableType.NUMERIC,
    'bool': VariableType.NUMERIC,
    'lshift': VariableType.NUMERIC,
    'rshift': VariableType.NUMERIC,
    'lt': VariableType.NUMERIC,
    'leq': VariableType.NUMERIC,
    'gt': VariableType.NUMERIC,
    'geq': VariableType.NUMERIC,
    'if': VariableType.NUMERIC,
    'tif': VariableType.TYPE,
}


class ParsingError(Exception):
    pass


class TranslationError(Exception):
    pass


@dataclass
class Variable:
    _name: str
    count: int
    type: VariableType

    def __init__(self, name, type):
        if VARIABLE_TEMPLATE.match(name):
            self._name = name
            self.type = type
        elif name == 'null':
            self.type = VariableType.NULL
        else:
            raise ParsingError("'{}' is not correct name for a variable".format(name))
        self.count = 0

    def inc(self):
        self.count += 1

    @property
    def name(self):
        if self._name == 'null':
            return 'null'
        else:
            return "{}_{}".format(self._name, self.count)


def purify_name(name):
    return name[:name.rfind('_')]


class Assignment:
    def __init__(self, left_op, right_op):
        self.left_op = left_op
        self.right_op = right_op

    def __repr__(self):
        return "Assignment({}, {})".format(self.left_op, self.right_op)


@dataclass
class NumericLiteral:
    value: int

    def __init__(self, value):
        self.value = value


@dataclass
class VariableValue:
    name: str


class RvalueType(Enum):
    NUMERIC_LITERAL = 0
    VARIABLE_VALUE = 1
    CALL = 2
    LOCAL_VARIABLE = 3


@dataclass
class Call:
    identifier: str
    arguments: list


class FuncLitType(Enum):
    NUMERIC = 0
    TYPE = 1


FUNC_LIT_TYPES_STR = {
    "num": VariableType.NUMERIC,
    "type": VariableType.TYPE,
}


def get_func_lit_type(arg):
    if arg not in FUNC_LIT_TYPES_STR:
        raise ParsingError("Unknown function literal type: '{}'".format(arg))
    return FUNC_LIT_TYPES_STR[arg]


class FunctionalLiteral:
    def __init__(self, name, raw_expr, functional_literals, variables):
        self.name = name
        self.raw_expr = raw_expr
        tokens = get_tokens(raw_expr)
        self.func_lit_type = get_func_lit_type(tokens[0])
        if tokens[1] != "(":
            raise ParsingError("Bad function literal syntax. '(' expected after literal type")
        if ")" not in tokens:
            raise ParsingError("Bad function literal syntax. ')' expected somewhere")
        args = {}
        for i in range(2, len(tokens)):
            if tokens[i] == ")":
                break
            elif tokens[i] == ":":
                arg_name = tokens[i - 1]
                arg_type = get_func_lit_type(tokens[i + 1])
                args[arg_name] = arg_type
        self.args = args
        rvalue_start_index = tokens.index('>')
        rvalue_tokens = tokens[rvalue_start_index + 1:]
        self.rvalue = Rvalue(variables, ''.join(rvalue_tokens), functional_literals, args)

    def __str__(self):
        return "FunctionalLiteral(name={}, args={}, rvalue={})".format(self.name, self.args, self.rvalue)


@dataclass
class LocalVariable:
    name: str
    type: VariableType


def parse_call(variables, tokens, functional_literals, local_vars):
    if tokens[-1] != ")":
        raise ParsingError("Call must have ')' at the end")
    if tokens[1:] == ['(', ')']:
        return Call(tokens[0], [])
    last_index = 2
    deep = 0
    args = []
    for i in range(len(tokens)):
        token = tokens[i]
        if token == '(':
            deep += 1
        elif token == ')':
            deep -= 1
        elif token == ',' and deep == 1:
            args.append(Rvalue(variables, ''.join(tokens[last_index:i]), functional_literals, local_vars))
            last_index = i + 1
    args.append(Rvalue(variables, ''.join(tokens[last_index:-1]), functional_literals, local_vars))
    return Call(tokens[0], args)


class Rvalue:
    def __init__(self, variables, raw_rvalue, func_lit_types, local_vars):
        self.raw_rvalue = raw_rvalue
        if local_vars is not None:
            if raw_rvalue in local_vars:
                self.value = LocalVariable(raw_rvalue, local_vars[raw_rvalue])
                self.type = RvalueType.LOCAL_VARIABLE
                self.variable_type = local_vars[raw_rvalue]
                return
        if NUMERIC_LITERAL_TEMPLATE.match(raw_rvalue):
            self.value = NumericLiteral(int(raw_rvalue))
            self.type = RvalueType.NUMERIC_LITERAL
            self.variable_type = VariableType.NUMERIC
        elif raw_rvalue in variables:
            self.value = VariableValue(variables[raw_rvalue].name)
            self.type = RvalueType.VARIABLE_VALUE
            self.variable_type = variables[raw_rvalue].type
        else:
            tokens = get_tokens(raw_rvalue)
            if len(tokens) < 2:
                raise ParsingError("Unknown rvalue type: '{}'".format(raw_rvalue))
            if tokens[0] in func_lit_types and tokens[1] == "(":
                parsed_call = parse_call(variables, tokens, func_lit_types, local_vars)
                self.type = RvalueType.CALL
                self.value = parsed_call
                self.variable_type = func_lit_types[tokens[0]]
            elif tokens[0] in BUILT_IN_IDENTIFIERS and tokens[1] == "(":
                parsed_call = parse_call(variables, tokens, func_lit_types, local_vars)
                if parsed_call.identifier == 'read':
                    self.type = RvalueType.NUMERIC_LITERAL
                    numeric_literal = read_next_token()
                    if not NUMERIC_LITERAL_TEMPLATE.match(numeric_literal):
                        raise TranslationError("Invalid input-numeric literal: {}".format(numeric_literal))
                    self.value = NumericLiteral(numeric_literal)
                    self.variable_type = BUILT_IN_IDENTIFIERS[tokens[0]]
                else:
                    self.type = RvalueType.CALL
                    self.value = parsed_call
                    self.variable_type = BUILT_IN_IDENTIFIERS[tokens[0]]
            else:
                raise ParsingError("Unknown rvalue type: '{}'".format(raw_rvalue))

    def __repr__(self):
        return "Rvalue(type={}, value={}, variable_type={})".format(self.type, self.value, self.variable_type)


def get_variables(assignments):
    variables = set()
    for left_op, _ in assignments:
        if '(' not in left_op and ')' not in left_op:
            variables.add(left_op)
    return variables


def get_code_lines(source):
    assignments = []
    for line in source:
        if not line.strip() or line.strip().startswith('#'):
            continue
        eql_cnt = line.count('=')
        if eql_cnt != 1:
            raise ParsingError("Every line must contain exactly one assignment ({})".format(eql_cnt))
        left_op, right_op = line.split('=')
        left_op = left_op.strip()
        right_op = right_op.strip()
        assignments.append((left_op, right_op))
    return assignments


def is_same_type(c1: str, c2: str):
    if c1.isspace() and c2.isspace():
        return True
    elif c1.isalpha() and c2.isalpha():
        return True
    else:
        return False


def get_tokens(source):
    source = source.replace(' ', '')
    result = []
    last_index = 0
    for i in range(len(source) - 1):
        if not is_same_type(source[i], source[i + 1]):
            result.append(source[last_index:i + 1])
            last_index = i + 1
    result.append(source[last_index:])
    return result


def preparse_func_literals(raw_pairs):
    functional_literals = {}
    for raw_code_line in raw_pairs:
        if '->' in raw_code_line[1]:
            if raw_code_line[1].startswith("num"):
                functional_literals[raw_code_line[0]] = VariableType.NUMERIC
            elif raw_code_line[1].startswith("type"):
                functional_literals[raw_code_line[0]] = VariableType.TYPE
            else:
                raise ParsingError("Functional literal must starts with 'type' or 'num'")
    return functional_literals


class FunctionalLiteralSpecialization:
    def __init__(self, variables, func_lit_types, related_func_lit: FunctionalLiteral, raw_left, raw_right):
        self.related_func_lit = related_func_lit
        self.raw_left = raw_left
        self.raw_right = raw_right
        self.local_vars = {}
        tokens = get_tokens(raw_left)
        parameters = []
        for token in tokens[2:-1]:
            if token != ",":
                parameters.append(token)
            if VARIABLE_TEMPLATE.match(token):
                self.local_vars[token] = related_func_lit.args[token]
        self.parameters = parameters
        self.rvalue = Rvalue(variables, raw_right, func_lit_types, self.local_vars)
        self.name = get_func_lit_spec_name(raw_left)

    def __str__(self):
        return "FunctionalLiteralSpecialization(name={}, rvalue={}, " \
        "parameters={}, func_lit={}, left={}, right={}".format(
            self.name,
            self.rvalue,
            self.parameters,
            self.related_func_lit,
            self.raw_left,
            self.raw_right,
        )


class LineType(Enum):
    ASSIGNMENT = 0
    FUNC_LIT = 1
    FUNC_LIT_SPECIALIZATION = 2


CodeLine = namedtuple("CodeLine", ["line_type", "object"])


def get_func_lit_spec_name(raw_value):
    return get_tokens(raw_value)[0]


def parse_vta_code(variables, func_lit_types, raw_code_lines):
    code_lines = []
    functional_literals = {}
    for raw_code_line in raw_code_lines:
        if '->' in raw_code_line[1]:
            func_lit = FunctionalLiteral(*raw_code_line, func_lit_types, variables)
            functional_literals[func_lit.name] = func_lit
            code_lines.append(CodeLine(LineType.FUNC_LIT, func_lit))
        elif '(' in raw_code_line[0] and ')' in raw_code_line[0]:
            func_lit_spec_name = get_func_lit_spec_name(raw_code_line[0])
            if func_lit_spec_name not in functional_literals:
                raise ParsingError("No such functional literal with name '{}'".format(func_lit_spec_name))
            functional_literal = functional_literals[func_lit_spec_name]
            func_lit_spec = FunctionalLiteralSpecialization(variables, func_lit_types, functional_literal, *raw_code_line)
            code_lines.append(CodeLine(LineType.FUNC_LIT_SPECIALIZATION, func_lit_spec))
        else:
            rvalue = Rvalue(variables, raw_code_line[1], func_lit_types, {})
            variables[raw_code_line[0]].inc()
            lvalue_full_name = variables[raw_code_line[0]].name
            variables[raw_code_line[0]].type = rvalue.variable_type
            code_lines.append(CodeLine(LineType.ASSIGNMENT, Assignment(lvalue_full_name, rvalue)))
    return code_lines


def translate_left_op(assignment: Assignment):
    if assignment.right_op.variable_type == VariableType.NUMERIC:
        return """struct {} {{{{
    const static long long value = {{}};
}}}};\n""".format(assignment.left_op)
    elif assignment.right_op.variable_type == VariableType.TYPE:
        return """struct {} {{{{
    using type = {{}};
}}}};\n""".format(assignment.left_op)
    else:
        raise TranslationError("Unknown assignment rvalue type or trying assign null to a variable")


def translate_right_op(variables, functional_literals, right_op):
    if right_op.type == RvalueType.NUMERIC_LITERAL:
        return str(right_op.value.value)
    elif right_op.type == RvalueType.VARIABLE_VALUE:
        return "{}::{}".format(right_op.value.name, variables[purify_name(right_op.value.name)].type)
    elif right_op.type == RvalueType.CALL:
        identifier = right_op.value.identifier
        translated_args = []
        for arg in right_op.value.arguments:
            translated_args.append(translate_right_op(variables, functional_literals, arg))
        if identifier in BUILT_IN_IDENTIFIERS:
            return "__{}<{}>::{}".format(identifier, ', '.join(translated_args), str(BUILT_IN_IDENTIFIERS[identifier]))
        elif identifier in functional_literals:
            if translated_args:
                return "_{}<{}>::{}".format(identifier, ', '.join(translated_args),
                                            str(functional_literals[identifier]))
            else:
                return "_{}::{}".format(identifier, str(functional_literals[identifier]))
        else:
            raise TranslationError(
                "Identifier '{}' is not contains in built-in-identifires or declared functional literals".format(
                    identifier
                )
            )

    elif right_op.type == RvalueType.LOCAL_VARIABLE:
        return right_op.raw_rvalue
    else:
        raise ParsingError("Unknown rvalue type: '{}'".format(right_op))


def translate_print_func(variables, functional_literals, right_op):
    if right_op.type != RvalueType.CALL:
        raise TranslationError("Can not translate print as non-call")
    args = []
    for arg in right_op.value.arguments:
        args.append(translate_right_op(variables, functional_literals, arg))
    return '    cout << ' + ' << " " << '.join(args) + ' << endl;'


NULL_TRANSLATION_FUNCS = {
    'print': translate_print_func
}


def translate_functional_literal(variables, functional_literals, func_lit: FunctionalLiteral):
    pars = ", ".join(["{} {}".format(translate_template_arg_type(type), name) for name, type in func_lit.args.items()])
    result = ["template<{}>".format(pars)] if pars else []
    if func_lit.func_lit_type == VariableType.NUMERIC:
        result.append("""struct _{} {{
    const static long long value = {};
}};""".format(func_lit.name, translate_right_op(variables, functional_literals, func_lit.rvalue)))
    else:
        typename = "typename " if func_lit.rvalue.type == RvalueType.CALL else ""
        result.append("""struct _{} {{
    using type = {}{};
}};""".format(func_lit.name, typename, translate_right_op(variables, functional_literals, func_lit.rvalue)))
    return '\n'.join(result)


def translate_func_lit_spec(variables, func_lit_types, func_lit_spec: FunctionalLiteralSpecialization):
    tplt_args = ', '.join(
        "{} {}".format(translate_template_arg_type(type), name) for name, type in func_lit_spec.local_vars.items()
    )
    translated_pars = ', '.join(func_lit_spec.parameters)
    translated_rvalue = translate_right_op(variables, func_lit_types, func_lit_spec.rvalue)
    if func_lit_spec.rvalue.variable_type == VariableType.NUMERIC:
        return """template<{}>
struct _{}<{}> {{
    const static long long value = {};
}};""".format(tplt_args, func_lit_spec.name, translated_pars, translated_rvalue)
    else:
        return """template<{}>
struct _{}<{}> {{
    using type = {};
}};""".format(tplt_args, func_lit_spec.name, translated_pars, translated_rvalue)


def build_cpp_code(variables, code_lines, functional_literals):
    body_code = []
    main_func_code = []

    with open("vta_header.cpp") as vta_header_file:
        body_code.append(vta_header_file.read())

    with open("vta_stdlib.cpp") as vta_stdlib_file:
        body_code.append(vta_stdlib_file.read())

    for line_type, atomic_obj in code_lines:
        if line_type == LineType.FUNC_LIT:
            body_code.append(translate_functional_literal(variables, functional_literals, atomic_obj))
        elif line_type == LineType.ASSIGNMENT:
            if atomic_obj.left_op == 'null':
                identifier = atomic_obj.right_op.value.identifier
                if identifier not in NULL_TRANSLATION_FUNCS:
                    raise TranslationError("Can not translate non-null function '{}'".format(identifier))
                main_func_code.append(NULL_TRANSLATION_FUNCS[identifier](variables, functional_literals, atomic_obj.right_op))
            else:
                left_op = translate_left_op(atomic_obj)
                right_op = translate_right_op(variables, functional_literals, atomic_obj.right_op)
                body_code.append(left_op.format(right_op))
        elif line_type == LineType.FUNC_LIT_SPECIALIZATION:
            body_code.append(translate_func_lit_spec(variables, functional_literals, atomic_obj))
        else:
            raise TranslationError("Unknown line_type: '{}'".format(line_type))

    with open("main_func.cpp") as main_func_file:
        main_func_template = main_func_file.read()
        body_code.append(main_func_template.format('\n'.join(main_func_code)))

    return '\n'.join(body_code)


def main():
    with open("main.vta") as source:
        raw_code_lines = get_code_lines(source)
        variables = {}
        for var_name in get_variables(raw_code_lines):
            variables[var_name] = Variable(var_name, VariableType.NOT_SET)
        functional_literals = preparse_func_literals(raw_code_lines)
        code_lines = parse_vta_code(variables, functional_literals, raw_code_lines)
        vta_code = build_cpp_code(variables, code_lines, functional_literals)
        with open("program.cpp", "w") as program_file:
            program_file.write(vta_code)


if __name__ == '__main__':
    main()
