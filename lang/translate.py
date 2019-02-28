import io
import re
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum

from lang.utils import read_next_token

VARIABLE_TEMPLATE = re.compile(r"[a-zA-Z][a-zA-Z0-9]*")
NUMERIC_LITERAL_TEMPLATE = re.compile(r"-?\d+")



class VariableTypeEnum(Enum):
    VALUE_NOT_SET = -3
    FUNCTION_NOT_SET = -2
    TYPE = 0
    NUMERIC = 1
    NULL = 2


class VariableType:
    VALUE_NOT_SET = VariableTypeEnum.VALUE_NOT_SET
    FUNCTION_NOT_SET = VariableTypeEnum.FUNCTION_NOT_SET
    TYPE = VariableTypeEnum.TYPE
    NUMERIC = VariableTypeEnum.NUMERIC
    NULL = VariableTypeEnum.NULL

    def __init__(self, return_type, args):
        self.return_type = return_type
        self.args = args

    def __str__(self):
        return "VariableType(return_type={}, args={})".format(self.return_type, self.args)


def translate_variable_type(var_type):
    if var_type == VariableType.TYPE:
        return "type"
    elif var_type == VariableType.NUMERIC:
        return "value"
    elif var_type == VariableType.NULL:
        return ""
    else:
        raise TranslationError("Can not translate type '{}'".format(var_type))


TEMPLATE_ARG_TYPES = {
    VariableType.TYPE: "typename",
    VariableType.NUMERIC: "long long",
}


BUILT_IN_IDENTIFIERS = {
    'nan': VariableType.NUMERIC,
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
    'count': VariableType.NUMERIC,
    'contains': VariableType.NUMERIC,
    'get': VariableType.NUMERIC,
    'map': VariableType.TYPE,
    'pow': VariableType.NUMERIC,
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


def parse_signature(tokens):
    call_args = get_call_args(tokens)
    args = {}
    for call_arg in call_args:
        args[call_arg[0]] = get_func_lit_type(call_arg)
    return args


def get_func_lit_type(args):
    if len(args) == 3:
        arg = args[2]
        if arg not in FUNC_LIT_TYPES_STR:
            raise ParsingError("Unknown function literal type: '{}'".format(arg))
        return FUNC_LIT_TYPES_STR[arg]
    else:
        return VariableType(FUNC_LIT_TYPES_STR[args[2]], parse_signature(args[2:]))


class FunctionalLiteral:
    def __init__(self, name, raw_expr, functional_literals, variables):
        self.name = name
        self.raw_expr = raw_expr
        tokens = get_tokens(raw_expr)
        self.func_lit_type = get_func_lit_type(["", "", tokens[0]])
        if tokens[1] != "(":
            raise ParsingError("Bad function literal syntax. '(' expected after literal type")
        if ")" not in tokens:
            raise ParsingError("Bad function literal syntax. ')' expected somewhere")

        signature_end = tokens.index('-')
        call_args = get_call_args(tokens[:signature_end])

        args = {}
        for call_arg in call_args:
            args[call_arg[0]] = get_func_lit_type(call_arg)

        self.args = args
        rvalue_start_index = tokens.index('>')
        rvalue_tokens = tokens[rvalue_start_index + 1:]
        self.rvalue = Rvalue(variables, ''.join(rvalue_tokens), functional_literals, args, stdin)

    def __str__(self):
        return "FunctionalLiteral(name={}, args={}, rvalue={})".format(self.name, self.args, self.rvalue)


@dataclass
class LocalVariable:
    name: str
    type: VariableType


class LocalVariableType(Enum):
    VALUE = 0
    FUNCTION = 1

    @staticmethod
    def get_by(var_type):
        if var_type == LocalVariableType.FUNCTION:
            return VariableType.FUNCTION_NOT_SET
        elif var_type == LocalVariableType.VALUE:
            return VariableType.VALUE_NOT_SET
        else:
            raise ParsingError("Can not resolve type '{}' into local variable type".format(var_type))


def get_call_args(tokens):
    if tokens[1] != "(":
        raise ParsingError("Call must have '(' after the call name")
    if tokens[-1] != ")":
        raise ParsingError("Call must have ')' at the end")
    if tokens[1:] == ['(', ')']:
        return []
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
            args.append(tokens[last_index:i])
            last_index = i + 1
    args.append(tokens[last_index:-1])
    return args


def parse_call(variables, tokens, functional_literals, local_vars, stdin):
    args = []
    for call_arg in get_call_args(tokens):
        rvalue = Rvalue(variables, ''.join(call_arg), functional_literals, local_vars, stdin)
        args.append(rvalue)
    return Call(tokens[0], args)


class Rvalue:
    def __init__(self, variables, raw_rvalue, func_lit_types, local_vars, stdin):
        self.local_vars = local_vars
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
            if tokens[0] in local_vars:
                parsed_call = parse_call(variables, tokens, func_lit_types, local_vars, stdin)
                self.type = RvalueType.CALL
                self.variable_type = local_vars[tokens[0]]
                self.value = parsed_call

            elif tokens[0] in func_lit_types and tokens[1] == "(":
                parsed_call = parse_call(variables, tokens, func_lit_types, local_vars, stdin)
                self.type = RvalueType.CALL
                self.value = parsed_call
                self.variable_type = func_lit_types[tokens[0]]
            elif tokens[0] in BUILT_IN_IDENTIFIERS and tokens[1] == "(":
                parsed_call = parse_call(variables, tokens, func_lit_types, local_vars, stdin)
                if parsed_call.identifier == 'read':
                    self.type = RvalueType.NUMERIC_LITERAL
                    numeric_literal = read_next_token(stdin)
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
        return "Rvalue(type={}, value={}, variable_type={}, local_vars={})".format(
            self.type, self.value, self.variable_type, self.local_vars
        )


def get_variables(assignments):
    variables = {}
    for left_op, right_op in assignments:
        if '(' not in left_op and ')' not in left_op:
            if '->' in right_op:
                variables[left_op] = LocalVariableType.FUNCTION
            else:
                variables[left_op] = LocalVariableType.VALUE
    return variables


def get_code_lines(source):
    assignments = []
    for line in source.split('\n'):
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
    elif c1.isnumeric() and c2.isnumeric():
        return True
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


class FuncLitSpecArgType(Enum):
    RVALUE = 0
    FREE_VARIABLE = 1


class FuncLitSpecArg:
    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __str__(self):
        return "FuncLitSpecArg(value={}, type={})".format(self.value, self.type)


@dataclass
class FreeVariable:
    name: str
    variable_type: VariableType


class FunctionalLiteralSpecialization:
    def __init__(self, variables, func_lit_types, related_func_lit: FunctionalLiteral, raw_left, raw_right):
        self.related_func_lit = related_func_lit
        self.raw_left = raw_left
        self.raw_right = raw_right
        self.local_vars = {}
        tokens = get_tokens(raw_left)
        parameters = []
        for call_arg in get_call_args(tokens):
            call_arg = ''.join(call_arg)
            if call_arg in related_func_lit.args:
                variable_type = related_func_lit.args[call_arg]
                free_variable = FreeVariable(call_arg, variable_type)
                parameters.append(FuncLitSpecArg(free_variable, FuncLitSpecArgType.FREE_VARIABLE))
                self.local_vars[call_arg] = variable_type
            else:
                rvalue = Rvalue(variables, call_arg, func_lit_types, self.local_vars, stdin)
                parameters.append(FuncLitSpecArg(rvalue, FuncLitSpecArgType.RVALUE))

        self.parameters = parameters
        self.rvalue = Rvalue(variables, raw_right, func_lit_types, self.local_vars, stdin)
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


def parse_vta_code(variables, func_lit_types, raw_code_lines, stdin):
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
            rvalue = Rvalue(variables, raw_code_line[1], func_lit_types, {}, stdin)
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
        if right_op.variable_type == VariableType.FUNCTION_NOT_SET:
            return "_" + purify_name(right_op.value.name)
        return "{}::{}".format(
            right_op.value.name,
            translate_variable_type(variables[purify_name(right_op.value.name)].type)
        )
    elif right_op.type == RvalueType.CALL:
        identifier = right_op.value.identifier
        arguments = right_op.value.arguments
        translated_args = []
        for arg in arguments:
            translated_args.append(translate_right_op(variables, functional_literals, arg))

        if identifier in BUILT_IN_IDENTIFIERS:
            result_type = BUILT_IN_IDENTIFIERS[identifier]

            if result_type == VariableType.TYPE:
                suffix = "::type"
                prefix = "typename "
            else:
                suffix = "::" + translate_variable_type(result_type)
                prefix = ""
            return "{}__{}<{}>{}".format(prefix, identifier, ', '.join(translated_args), suffix)
        elif identifier in right_op.local_vars:
            result_type = right_op.local_vars[identifier]
            if result_type == VariableType.TYPE:
                suffix = "::type"
                prefix = "typename "
            else:
                if isinstance(result_type, VariableType):
                    suffix = "::" + translate_variable_type(result_type.return_type)
                else:
                    suffix = "::" + translate_variable_type(result_type)
                prefix = ""
            if translated_args:
                return "{}{}<{}>{}".format(prefix, identifier, ', '.join(translated_args), suffix)
            else:
                return "{}{}{}".format(prefix, identifier, suffix)

        elif identifier in functional_literals:
            result_type = functional_literals[identifier]
            if result_type == VariableType.TYPE:
                suffix = "::type"
                prefix = "typename "
            else:
                suffix = "::" + translate_variable_type(result_type)
                prefix = ""
            if translated_args:
                return "{}_{}<{}>{}".format(prefix, identifier, ', '.join(translated_args), suffix)
            else:
                return "{}_{}{}".format(prefix, identifier, suffix)
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
    return '    __print<' + ', '.join(args) + '>();'


NULL_TRANSLATION_FUNCS = {
    'print': translate_print_func
}


def translate_signature(args, add_typename=False):
    pars = ", ".join(["{} {}".format(translate_template_arg_type(type), name) for name, type in args.items()])
    if not pars:
        return ""
    if add_typename:
        return "template<{}> typename".format(pars)
    return "template<{}>".format(pars)


def translate_template_arg_type(arg_type):
    if arg_type in TEMPLATE_ARG_TYPES:
        return TEMPLATE_ARG_TYPES[arg_type]
    return translate_signature(arg_type.args, True)


def translate_functional_literal(variables, functional_literals, func_lit: FunctionalLiteral):
    result = [translate_signature(func_lit.args)]
    if func_lit.func_lit_type == VariableType.NUMERIC:
        result.append("""struct _{} {{
    const static long long value = {};
}};\n""".format(func_lit.name, translate_right_op(variables, functional_literals, func_lit.rvalue)))
    else:
        result.append("""struct _{} {{
    using type = {};
}};\n""".format(func_lit.name, translate_right_op(variables, functional_literals, func_lit.rvalue)))
    return '\n'.join(result)


def translate_func_lit_spec(variables, func_lit_types, func_lit_spec: FunctionalLiteralSpecialization):
    tplt_args = ', '.join(
        "{} {}".format(translate_template_arg_type(type), name) for name, type in func_lit_spec.local_vars.items()
    )
    parameters = []
    for parameter in func_lit_spec.parameters:
        if parameter.type == FuncLitSpecArgType.FREE_VARIABLE:
            parameters.append(parameter.value.name)
        else:
            parameters.append(translate_right_op(variables, func_lit_types, parameter.value))
    translated_pars = ', '.join(parameters)
    translated_rvalue = translate_right_op(variables, func_lit_types, func_lit_spec.rvalue)
    if func_lit_spec.rvalue.variable_type == VariableType.NUMERIC:
        return """template<{}>
struct _{}<{}> {{
    const static long long value = {};
}};\n""".format(tplt_args, func_lit_spec.name, translated_pars, translated_rvalue)
    else:
        return """template<{}>
struct _{}<{}> {{
    using type = {};
}};\n""".format(tplt_args, func_lit_spec.name, translated_pars, translated_rvalue)


def build_cpp_code(variables, code_lines, functional_literals):
    body_code = []
    main_func_code = []

    with open("lang/vta_header.cpp") as vta_header_file:
        body_code.append(vta_header_file.read())

    with open("lang/vta_stdlib.cpp") as vta_stdlib_file:
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

    with open("lang/main_func.cpp") as main_func_file:
        main_func_template = main_func_file.read()
        body_code.append(main_func_template.format('\n'.join(main_func_code)))

    return '\n'.join(body_code)


def translate(source, stdin):
    raw_code_lines = get_code_lines(source)
    variables = {}
    for var_name, var_type in get_variables(raw_code_lines).items():
        variables[var_name] = Variable(var_name, LocalVariableType.get_by(var_type))
    functional_literals = preparse_func_literals(raw_code_lines)
    code_lines = parse_vta_code(variables, functional_literals, raw_code_lines, stdin)
    return build_cpp_code(variables, code_lines, functional_literals)
