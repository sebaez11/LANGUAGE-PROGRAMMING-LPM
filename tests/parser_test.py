from unittest import TestCase

from lpm.lexer import Lexer
from lpm.parser import Parser
from lpm.ast import (
    Expression,
    ExpressionStatement,
    Identifier,
    Integer,
    Program,
    LetStatement,
    ReturnStatement,
    Prefix,
    Infix,
    Boolean,
    Block,
    If,
    Function,
    Call,
    StringLiteral,
)

from typing import (
    cast,
    List,
    Any,
    Type,
    Tuple,
)

class ParserTest(TestCase):
    def test_parse_program(self) -> None:
        source: str = 'variable x = 5;'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self.assertIsNotNone(program)
        self.assertIsInstance(program, Program)

    def test_let_statements(self) -> None:
        source: str = '''
            variable x = 5;
            variable y = 10;
            variable foo = 20;
            variable bar = verdadero;
        '''
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self.assertEqual(len(program.statements), 4)

        expected_identifiers_and_values: List[Tuple[str, Any]] = [
            ('x', 5),
            ('y', 10),
            ('foo', 20),
            ('bar', True),
        ]

        for statement, (expected_identifier, expected_value)in zip(
            program.statements, expected_identifiers_and_values):
            self.assertEqual(statement.token_literal(), 'variable')
            self.assertIsInstance(statement, LetStatement)

            let_statement = cast(LetStatement, statement)

            assert let_statement.name is not None
            self._test_identifier(let_statement.name, expected_identifier)

            assert let_statement.value is not None
            self._test_literal_expression(let_statement.value, expected_value)

    def test_names_in_let_statements(self) -> None:
        source: str = '''
            variable x = 5;
            variable y = 10;
            variable foo = 20;
        '''
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        names: List[str] = []
        for statement in program.statements:
            statement = cast(LetStatement, statement)
            assert statement.name is not None
            names.append(statement.name.value)

        expected_names: List[str] = ['x', 'y', 'foo']

        self.assertEquals(names, expected_names)

    def test_parse_errors(self) -> None:
        source: str = 'variable x 5;'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self.assertEquals(len(parser.errors), 1)

    def test_return_statement(self) -> None:
        source: str = '''
            regresa 5;
            regresa foo;
            regresa verdadero;
            regresa falso;
        '''
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self.assertEquals(len(program.statements), 4)

        expected_return_values: List[Any] = [
            5,
            'foo',
            True,
            False,
        ]

        for statement, expected_return_value in zip(program.statements, expected_return_values):
            self.assertEquals(statement.token_literal(), 'regresa')
            self.assertIsInstance(statement, ReturnStatement)

            return_statement = cast(ReturnStatement, statement)

            assert return_statement.return_value is not None
            self._test_literal_expression(return_statement.return_value,
                                          expected_return_value)

    def test_identifier_expression(self) -> None:
        source: str = 'foobar;'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self._test_program_statements(parser, program)

        expression_statement = cast(ExpressionStatement, program.statements[0])

        assert expression_statement.expression is not None
        self._test_literal_expression(expression_statement.expression, 'foobar')

    def test_integer_expressions(self) -> None:
        source: str = '5;'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self._test_program_statements(parser, program)

        expression_statement = cast(ExpressionStatement, program.statements[0])

        assert expression_statement.expression is not None
        self._test_literal_expression(expression_statement.expression, 5)

    def test_prefix_expression(self) -> None:
        source: str = '!5; -15; !verdadero; !falso;'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self._test_program_statements(parser, program, expected_statement_count=4)

        for statement, (expected_operator, expected_value) in zip(
                program.statements, [('!', 5), ('-', 15), ('!', True), ('!', False)]
        ):
            statement = cast(ExpressionStatement, statement)
            self.assertIsInstance(statement.expression, Prefix)

            prefix = cast(Prefix, statement.expression)
            self.assertEquals(prefix.operator, expected_operator)

            assert prefix.right is not None
            self._test_literal_expression(prefix.right, expected_value)

    def test_infix_expressions(self) -> None:
        source: str = '''
            5 + 5;
            5 - 5;
            5 * 5;
            5 / 5;
            5 > 5;
            5 < 5;
            5 == 5;
            5 != 5;
            verdadero == verdadero;
            verdadero != falso;
            falso == falso;
        '''
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self._test_program_statements(parser, program, expected_statement_count=11)

        expected_operators_and_values: List[Tuple[Any, str, Any]] = [
            (5, '+', 5),
            (5, '-', 5),
            (5, '*', 5),
            (5, '/', 5),
            (5, '>', 5),
            (5, '<', 5),
            (5, '==', 5),
            (5, '!=', 5),
            (True, '==', True),
            (True, '!=', False),
            (False, '==', False),
        ]

        for statement, (expected_left, expected_operator, expected_right) in zip(
                program.statements, expected_operators_and_values):
            statement = cast(ExpressionStatement, statement)
            assert statement.expression is not None
            self.assertIsInstance(statement.expression, Infix)
            self._test_infix_expression(statement.expression,
                                        expected_left,
                                        expected_operator,
                                        expected_right)

    def test_boolean_expression(self) -> None:
        source: str = 'verdadero; falso;'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self._test_program_statements(parser, program, expected_statement_count=2)

        expected_values: List[bool] = [True, False]

        for statement, expected_value in zip(program.statements, expected_values):
            expression_statement = cast(ExpressionStatement, statement)

            assert expression_statement.expression is not None
            self._test_literal_expression(expression_statement.expression, expected_value)

    def _test_boolean(self, expression: Expression, expected_value: bool) -> None:
        self.assertIsInstance(expression, Boolean)

        boolean = cast(Boolean, expression)
        self.assertEquals(boolean.value, expected_value)
        self.assertEquals(boolean.token.literal, 'verdadero' if expected_value else 'falso')

    def test_operator_precedence(self) -> None:
        test_sources: List[Tuple[str, str, int]] = [
            ('-a * b;', '((-a) * b)', 1),
            ('!-a;', '(!(-a))', 1),
            ('a + b + c;', '((a + b) + c)', 1),
            ('a + b - c;', '((a + b) - c)', 1),
            ('a * b * c;', '((a * b) * c)', 1),
            ('a + b / c;', '(a + (b / c))', 1),
            ('a * b / c;', '((a * b) / c)', 1),
            ('a + b * c + d / e - f;', '(((a + (b * c)) + (d / e)) - f)', 1),
            ('5 > 4 == 3 < 4;', '((5 > 4) == (3 < 4))', 1),
            ('3 - 4 * 5 == 3 * 1 + 4 * 5;', '((3 - (4 * 5)) == ((3 * 1) + (4 * 5)))', 1),
            ('3 + 4; -5 * 5;', '(3 + 4)((-5) * 5)', 2),
            ('verdadero;', 'verdadero', 1),
            ('falso;', 'falso', 1),
            ('3 > 5 == verdadero;', '((3 > 5) == verdadero)', 1),
            ('3 < 5 == falso;', '((3 < 5) == falso)', 1),
            ('1 + (2 + 3) + 4;', '((1 + (2 + 3)) + 4)', 1),
            ('(5 + 5) * 2;', '((5 + 5) * 2)', 1),
            ('2 / (5 + 5);', '(2 / (5 + 5))', 1),
            ('-(5 + 5);', '(-(5 + 5))', 1),
            ('a + suma(b * c) + d;', '((a + suma((b * c))) + d)', 1),
            ('suma(a, b, 1, 2 * 3, 4 + 5, suma(6, 7 * 8));',
             'suma(a, b, 1, (2 * 3), (4 + 5), suma(6, (7 * 8)))', 1),
            ('suma(a + b + c * d / f + g);', 'suma((((a + b) + ((c * d) / f)) + g))', 1),
        ]

        for source, expected_result, expected_statement_count in test_sources:
            lexer: Lexer = Lexer(source)
            parser: Parser = Parser(lexer)

            program: Program = parser.parse_program()

            self._test_program_statements(parser, program, expected_statement_count)
            self.assertEquals(str(program), expected_result)

    def test_call_expression(self) -> None:
        source: str = 'suma(1, 2 * 3, 4 + 5);'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self._test_program_statements(parser, program)

        call = cast(Call, cast(ExpressionStatement,
                               program.statements[0]).expression)
        self.assertIsInstance(call, Call)
        self._test_identifier(call.function, 'suma')

        # Test arguments
        assert call.arguments is not None
        self.assertEquals(len(call.arguments), 3)
        self._test_literal_expression(call.arguments[0], 1)
        self._test_infix_expression(call.arguments[1], 2, '*', 3)
        self._test_infix_expression(call.arguments[2], 4, '+', 5)

    def test_if_expression(self) -> None:
        source: str = 'si (x < y) { z }'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self._test_program_statements(parser, program)

        # Test correct node type
        if_expression = cast(If, cast(ExpressionStatement, program.statements[0]).expression)
        self.assertIsInstance(if_expression, If)

        # Test condition
        assert if_expression.condition is not None
        self._test_infix_expression(if_expression.condition, 'x', '<', 'y')

        # Test consequence
        assert if_expression.consequence is not None
        self.assertIsInstance(if_expression.consequence, Block)
        self.assertEquals(len(if_expression.consequence.statements), 1)

        consequence_statement = cast(ExpressionStatement,
                                     if_expression.consequence.statements[0])
        assert consequence_statement.expression is not None
        self._test_identifier(consequence_statement.expression, 'z')

        # Test alternative
        self.assertIsNone(if_expression.alternative)

    def test_if_else_expression(self) -> None:
        source: str = 'si (x != y) { x } si_no { y }'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self._test_program_statements(parser, program)

        # Test correct node type
        if_expression = cast(If, cast(ExpressionStatement, program.statements[0]).expression)
        self.assertIsInstance(if_expression, If)

        # Test condition
        assert if_expression.condition is not None
        self._test_infix_expression(if_expression.condition, 'x', '!=', 'y')

        # Test consequence
        assert if_expression.consequence is not None
        self.assertIsInstance(if_expression.consequence, Block)
        self.assertEquals(len(if_expression.consequence.statements), 1)

        consequence_statement = cast(ExpressionStatement, if_expression.consequence.statements[0])
        assert consequence_statement.expression is not None
        self._test_identifier(consequence_statement.expression, 'x')

        # Test alternative
        assert if_expression.alternative is not None
        self.assertIsInstance(if_expression.alternative, Block)
        self.assertEquals(len(if_expression.alternative.statements), 1)

        alternative_statement = cast(ExpressionStatement, if_expression.alternative.statements[0])
        assert alternative_statement.expression is not None
        self._test_identifier(alternative_statement.expression, 'y')

    def test_function_literal(self) -> None:
        source: str = 'procedimiento(x, y) { x + y}'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        self._test_program_statements(parser, program)

        # Test correct node type
        function_literal = cast(Function, cast(ExpressionStatement,
                                               program.statements[0]).expression)
        self.assertIsInstance(function_literal, Function)

        # Test params
        self.assertEquals(len(function_literal.parameters), 2)
        self._test_literal_expression(function_literal.parameters[0], 'x')
        self._test_literal_expression(function_literal.parameters[1], 'y')

        # Test body
        assert function_literal.body is not None
        self.assertEquals(len(function_literal.body.statements), 1)

        body = cast(ExpressionStatement, function_literal.body.statements[0])
        assert body.expression is not None
        self._test_infix_expression(body.expression, 'x', '+', 'y')

    def test_function_parameters(self) -> None:
        tests = [
            {'input': 'procedimiento() {};',
             'expected_params': []},
            {'input': 'procedimiento(x) {};',
             'expected_params': ['x']},
            {'input': 'procedimiento(x, y, z) {};',
             'expected_params': ['x', 'y', 'z']},
        ]

        for test in tests:
            lexer: Lexer = Lexer(test['input']) # type: ignore
            parser: Parser = Parser(lexer)

            program: Program = parser.parse_program()

            function = cast(Function, cast(ExpressionStatement,
                                           program.statements[0]).expression)

            self.assertEquals(len(function.parameters), len(test['expected_params']))

            for idx, param in enumerate(test['expected_params']):
                self._test_literal_expression(function.parameters[idx], param)

    def _test_infix_expression(self, expression: Expression, expected_left: Any, expected_operator: str, expected_right: Any):
        infix = cast(Infix, expression)

        assert infix.left is not None
        self._test_literal_expression(infix.left, expected_left)

        self.assertEquals(infix.operator, expected_operator)

        assert infix.right is not None
        self._test_literal_expression(infix.right, expected_right)

    def _test_program_statements(self, parser: Parser, program: Program, expected_statement_count: int = 1) -> None:
        if parser.errors:
            print(parser.errors)
        
        self.assertEquals(len(parser.errors), 0)
        self.assertEquals(len(program.statements), expected_statement_count)
        self.assertIsInstance(program.statements[0], ExpressionStatement)

    def _test_literal_expression(self, expression: Expression, expected_value: Any) -> None:
        value_type: Type = type(expected_value)

        if value_type == str:
            self._test_identifier(expression, expected_value)
        elif value_type == int:
            self._test_integer(expression, expected_value)
        elif value_type == bool:
            self._test_boolean(expression, expected_value)
        else:
            self.fail(f'Unhandled type of expression. Got={value_type}')

    def _test_identifier(self, expression: Expression, expected_value: str) -> None:
        self.assertIsInstance(expression, Identifier)

        identifier = cast(Identifier, expression)
        self.assertEquals(identifier.value, expected_value)
        self.assertEquals(identifier.token.literal, expected_value)

    def _test_integer(self, expression: Expression, expected_value: int) -> None:
        self.assertIsInstance(expression, Integer)

        integer = cast(Integer, expression)
        self.assertEquals(integer.value, expected_value)
        self.assertEquals(integer.token.literal, str(expected_value))

    def test_string_literal_expression(self) -> None:
        source: str = '"hello world!"'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        expression_statement = cast(ExpressionStatement, program.statements[0])
        string_literal = cast(StringLiteral, expression_statement.expression)

        self.assertIsInstance(string_literal, StringLiteral)
        self.assertEquals(string_literal.value, 'hello world!')