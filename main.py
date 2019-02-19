import logging
import re
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
            raise TranslationError("Can not translate not setted variable type")


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
    'b': VariableType.NUMERIC,
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


@dataclass
class FunctionalLiteral:
    pass


@dataclass
class LocalVariable:
    name: str


def parse_call(variables, tokens):
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
            args.append(Rvalue(variables, ''.join(tokens[last_index:i])))
            last_index = i + 1
    args.append(Rvalue(variables, ''.join(tokens[last_index:-1])))
    return Call(tokens[0], args)


def parse_func_literal(variables, tokens):
    pass


class Rvalue:
    def __init__(self, variables, raw_rvalue, local_vars=None):
        self.raw_rvalue = raw_rvalue
        if local_vars is not None:
            if raw_rvalue in local_vars:
                self.value = LocalVariable(raw_rvalue)
                self.type = RvalueType.LOCAL_VARIABLE
                self.variable_type = local_vars[raw_rvalue]
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
            if tokens[0] in BUILT_IN_IDENTIFIERS and tokens[1] == "(":
                parsed_call = parse_call(variables, tokens)
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
    return set(map(lambda x: x[0], assignments))


def get_assignments(source):
    assignments = []
    for line in source:
        if not line.strip():
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


def parse(variables, raw_assignments):
    assignments = []
    for raw_assignment in raw_assignments:
        rvalue = Rvalue(variables, raw_assignment[1])
        variables[raw_assignment[0]].inc()
        lvalue_full_name = variables[raw_assignment[0]].name
        variables[raw_assignment[0]].type = rvalue.variable_type
        assignments.append(Assignment(lvalue_full_name, rvalue))
    return assignments


# def translate_assignment(assignment: Assignment):
#     if assignment.right_op.type == RvalueType.NUMERIC_LITERAL:
#         return """struct {} {{{{
#     const static long long value = {};
# }}}};""".format(assignment.left_op, assignment.right_op.value.value)
#     elif assignment.right_op.type == RvalueType.VARIABLE_VALUE:
#         return """struct {} {{{{
#     const static long long value = {}::value;
# }}}};""".format(assignment.left_op, assignment.right_op.value.name)
#     elif assignment.right_op.type == RvalueType.CALL:
#         if assignment.right_op.variable_type == VariableType.NUMERIC:
#             return """struct {} {{{{
#                 const static long long value = {}::value;
#             }}}};"""
#     else:
#         raise ParsingError("Unknown assignment rvalue type")


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


def translate_right_op(variables, right_op):
    if right_op.type == RvalueType.NUMERIC_LITERAL:
        return str(right_op.value.value)
    elif right_op.type == RvalueType.VARIABLE_VALUE:
        return "{}::{}".format(right_op.value.name, variables[purify_name(right_op.value.name)].type)
    elif right_op.type == RvalueType.CALL:
        identifier = right_op.value.identifier
        translated_args = []
        for arg in right_op.value.arguments:
            translated_args.append(translate_right_op(variables, arg))
        return "__{}<{}>::{}".format(identifier, ', '.join(translated_args), str(BUILT_IN_IDENTIFIERS[identifier]))
    else:
        raise ParsingError("Unknown rvalue type")


def translate_print_func(variables, right_op):
    if right_op.type != RvalueType.CALL:
        raise TranslationError("Can not translate print as non-call")
    # cout << arg1 << " " << arg2 << " " << arg3 << endl;
    args = []
    for arg in right_op.value.arguments:
        args.append(translate_right_op(variables, arg))
    return '    cout << ' + ' << " " << '.join(args) + ' << endl;'


NULL_TRANSLATION_FUNCS = {
    'print': translate_print_func
}


def build_vta_code(variables, assignments):
    body_code = []
    main_func_code = []

    with open("vta_header.cpp") as vta_header_file:
        body_code.append(vta_header_file.read())

    with open("vta_stdlib.cpp") as vta_stdlib_file:
        body_code.append(vta_stdlib_file.read())

    for assignment in assignments:
        if assignment.left_op == 'null':
            identifier = assignment.right_op.value.identifier
            if identifier not in NULL_TRANSLATION_FUNCS:
                raise TranslationError("Can not translate non-null function '{}'".format(identifier))
            main_func_code.append(NULL_TRANSLATION_FUNCS[identifier](variables, assignment.right_op))
        else:
            left_op = translate_left_op(assignment)
            right_op = translate_right_op(variables, assignment.right_op)
            body_code.append(left_op.format(right_op))

    with open("main_func.cpp") as main_func_file:
        main_func_template = main_func_file.read()
        body_code.append(main_func_template.format('\n'.join(main_func_code)))

    return '\n'.join(body_code)


def main():
    with open("main.vta") as source:
        raw_assignments = get_assignments(source)
        variables = {}
        for var_name in get_variables(raw_assignments):
            variables[var_name] = Variable(var_name, VariableType.NOT_SET)
        assignments = parse(variables, raw_assignments)
        vta_code = build_vta_code(variables, assignments)
        with open("program.cpp", "w") as program_file:
            program_file.write(vta_code)


if __name__ == '__main__':
    main()
