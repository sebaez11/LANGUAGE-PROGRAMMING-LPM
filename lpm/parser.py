from lpm.ast import (
    Expression,
    ExpressionStatement,
    Program,
    Identifier,
    LetStatement,
    Statement,
    ReturnStatement,
    Integer,
    Prefix,
    Infix,
    Boolean,
    Block,
    If,
    Function,
    Call,
    StringLiteral,
)
from lpm.lexer import Lexer
from lpm.token import (
    Token,
    TokenType
)

from typing import (
    Optional,
    List,
    Callable,
    Dict,
)

from enum import IntEnum

PrefixParseFn = Callable[[], Optional[Expression]]
InfixParseFn = Callable[[Expression], Optional[Expression]]
PrefixParseFns = Dict[TokenType, PrefixParseFn]
InfixParseFns = Dict[TokenType, InfixParseFn]


class Precedence(IntEnum):
    LOWEST = 1
    EQUALS = 2
    LESSGREATER = 3
    SUM = 4
    PRODUCT = 5
    PREFIX = 6
    CALL = 7


PRECEDENCES: Dict[TokenType, Precedence] = {
    TokenType.EQ: Precedence.EQUALS,
    TokenType.NOT_EQ: Precedence.EQUALS,
    TokenType.LT: Precedence.LESSGREATER,
    TokenType.GT: Precedence.LESSGREATER,
    TokenType.PLUS: Precedence.SUM,
    TokenType.SUBSTRACT: Precedence.SUM,
    TokenType.DIVIDE: Precedence.PRODUCT,
    TokenType.MULTIPLICATION: Precedence.PRODUCT,
    TokenType.LPAREN: Precedence.CALL,
}


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer
        self._current_token: Optional[Token] = None
        self._peek_token: Optional[Token] = None
        self._errors: List[str] = []

        self._prefix_parse_fns: PrefixParseFns = self._register_prefix_fns()
        self._infix_parse_fns: InfixParseFns = self._register_infix_fns()

        self._advance_tokens()
        self._advance_tokens()

    def _current_precedence(self) -> Precedence:
        assert self._current_token is not None
        try:
            return PRECEDENCES[self._current_token.token_type]
        except KeyError:
            return Precedence.LOWEST

    @property
    def errors(self) -> List[str]:
        return self._errors

    def parse_program(self) -> Program:
        program: Program = Program(statements=[])

        assert self._current_token is not None
        while self._current_token.token_type != TokenType.EOF:
            statement = self._parse_statement()
            if statement is not None:
                program.statements.append(statement)

            self._advance_tokens()

        return program

    def _advance_tokens(self) -> None:
        self._current_token = self._peek_token
        self._peek_token = self._lexer.next_token()

    def _expected_token(self, token_type: TokenType) -> bool:
        assert self._peek_token is not None
        if self._peek_token.token_type == token_type:
            self._advance_tokens()

            return True
        
        self._expected_token_error(token_type)
        return False

    def _expected_token_error(self, token_type: TokenType) -> None:
        assert self._peek_token is not None
        error = f'Se esperaba que el siguiente token fuera {token_type}' + \
                f' pero se obtuvo {self._peek_token.token_type}'

        self._errors.append(error)

    def _parse_block(self) -> Block:
        assert self._current_token is not None
        block_statement = Block(token=self._current_token,
                                statements=[])

        self._advance_tokens()

        while not self._current_token.token_type == TokenType.RBRACE \
                and not self._current_token.token_type == TokenType.EOF:
            statement = self._parse_statement()

            if statement:
                block_statement.statements.append(statement)

            self._advance_tokens()

        return block_statement

    def _parse_boolean(self) -> Boolean:
        assert self._current_token is not None

        return Boolean(token=self._current_token,
                       value=self._current_token.token_type == TokenType.TRUE)

    def _parse_call(self, function: Expression) -> Call:
        assert self._current_token is not None
        call = Call(self._current_token, function)
        call.arguments = self._parse_call_arguments()

        return call

    def _parse_call_arguments(self) -> Optional[List[Expression]]:
        arguments: List[Expression] = []

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.RPAREN:
            self._advance_tokens()

            return arguments

        self._advance_tokens()
        if expression := self._parse_expression(Precedence.LOWEST):
            arguments.append(expression)

        while self._peek_token.token_type == TokenType.COMMA:
            self._advance_tokens()
            self._advance_tokens()

            if expression := self._parse_expression(Precedence.LOWEST):
                arguments.append(expression)

        if not self._expected_token(TokenType.RPAREN):
            return None

        return arguments

    def _parse_expression(self, precedence: Precedence) -> Optional[Expression]:
        assert self._current_token is not None
        try:
            prefix_parse_fn = self._prefix_parse_fns[self._current_token.token_type]
        except KeyError:
            message = f'No se encontró ninguna función para parsear {self._current_token.literal}'
            self._errors.append(message)

            return None
        
        left_expression = prefix_parse_fn()

        assert self._peek_token is not None
        while not self._peek_token.token_type == TokenType.SEMICOLON and \
                precedence < self._peek_precedence():
            try:
                infix_parse_fn = self._infix_parse_fns[self._peek_token.token_type]

                self._advance_tokens()

                assert left_expression is not None
                left_expression = infix_parse_fn(left_expression)
            except KeyError:
                return left_expression

        return left_expression

    def _parse_expression_statement(self) -> Optional[ExpressionStatement]:
        assert self._current_token is not None
        expression_statement = ExpressionStatement(token=self._current_token)

        expression_statement.expression = self._parse_expression(Precedence.LOWEST)

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return expression_statement

    def _parse_grouped_expression(self) -> Optional[Expression]:
        self._advance_tokens()

        expression = self._parse_expression(Precedence.LOWEST)

        if not self._expected_token(TokenType.RPAREN):
            return None

        return expression

    def _parse_function(self) -> Optional[Function]:
        assert self._current_token is not None
        function = Function(token=self._current_token)

        if not self._expected_token(TokenType.LPAREN):
            return None

        function.parameters = self._parse_function_parameters()

        if not self._expected_token(TokenType.LBRACE):
            return None

        function.body = self._parse_block()

        return function


    def _parse_function_parameters(self) -> List[Identifier]:
        params: List[Identifier] = []

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.RPAREN:
            self._advance_tokens()

            return params

        self._advance_tokens()

        assert self._current_token is not None
        identifier = Identifier(token=self._current_token,
                                value=self._current_token.literal)
        params.append(identifier)

        while self._peek_token.token_type == TokenType.COMMA:
            self._advance_tokens()
            self._advance_tokens()

            identifier = Identifier(token=self._current_token,
                                    value=self._current_token.literal)
            params.append(identifier)

        if not self._expected_token(TokenType.RPAREN):
            return []

        return params

    def _parse_identifier(self) -> Identifier:
        assert self._current_token is not None

        return Identifier(token=self._current_token, value=self._current_token.literal)

    def _parse_if(self) -> Optional[If]:
        assert self._current_token is not None
        if_expression = If(token=self._current_token)

        if not self._expected_token(TokenType.LPAREN):
            return None

        self._advance_tokens()

        if_expression.condition = self._parse_expression(Precedence.LOWEST)

        if not self._expected_token(TokenType.RPAREN):
            return None

        if not self._expected_token(TokenType.LBRACE):
            return None

        if_expression.consequence = self._parse_block()

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.ELSE:
            self._advance_tokens()

            if not self._expected_token(TokenType.LBRACE):
                return None

            if_expression.alternative = self._parse_block()

        return if_expression

    def _parse_infix_expression(self, left: Expression) -> Infix:
        assert self._current_token is not None
        infix = Infix(token=self._current_token,
                      operator=self._current_token.literal,
                      left=left)

        precedence = self._current_precedence()

        self._advance_tokens()

        infix.right = self._parse_expression(precedence)

        return infix

    def _parse_integer(self) -> Optional[Integer]:
        assert self._current_token is not None
        integer = Integer(token=self._current_token)

        try:
            integer.value = int(self._current_token.literal)
        except ValueError:
            message = f'No se ha podido parsear {self._current_token.literal}' + \
                        'como entero.'
            self._errors.append(message)

            return None

        return integer

    def _parse_let_statement(self) -> Optional[LetStatement]:
        assert self._current_token is not None
        let_statement = LetStatement(token=self._current_token)

        if not self._expected_token(TokenType.IDENT):
            return None

        let_statement.name = self._parse_identifier()

        if not self._expected_token(TokenType.ASSIGN):
            return None

        self._advance_tokens()

        let_statement.value = self._parse_expression(Precedence.LOWEST)

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return let_statement

    def _parse_prefix_expression(self) -> Prefix:
        assert self._current_token is not None
        prefix_expression = Prefix(token=self._current_token, operator=self._current_token.literal)

        self._advance_tokens()

        prefix_expression.right = self._parse_expression(Precedence.PREFIX)

        return prefix_expression

    def _parse_return_statement(self) -> Optional[ReturnStatement]:
        assert self._current_token is not None
        return_statement = ReturnStatement(token=self._current_token)
        
        self._advance_tokens()

        return_statement.return_value = self._parse_expression(Precedence.LOWEST)

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return return_statement

    def _parse_statement(self) -> Optional[Statement]:
        assert self._current_token is not None
        if self._current_token.token_type == TokenType.LET:
            return self._parse_let_statement()
        elif self._current_token.token_type == TokenType.RETURN:
            return self._parse_return_statement()
        else:
            return self._parse_expression_statement()

    def _parse_string_literal(self) -> Expression:
        assert self._current_token is not None
        return StringLiteral(token=self._current_token, value=self._current_token.literal)

    def _peek_precedence(self) -> Precedence:
        assert self._peek_token is not None
        try:
            return PRECEDENCES[self._peek_token.token_type]
        except KeyError:
            return Precedence.LOWEST

    def _register_infix_fns(self) -> InfixParseFns:
        return {
            TokenType.PLUS: self._parse_infix_expression,
            TokenType.SUBSTRACT: self._parse_infix_expression,
            TokenType.DIVIDE: self._parse_infix_expression,
            TokenType.MULTIPLICATION: self._parse_infix_expression,
            TokenType.EQ: self._parse_infix_expression,
            TokenType.NOT_EQ: self._parse_infix_expression,
            TokenType.LT: self._parse_infix_expression,
            TokenType.GT: self._parse_infix_expression,
            TokenType.LPAREN: self._parse_call,
        }

    def _register_prefix_fns(self) -> PrefixParseFns:
        return {
            TokenType.IDENT: self._parse_identifier,
            TokenType.INT: self._parse_integer,
            TokenType.SUBSTRACT: self._parse_prefix_expression,
            TokenType.DIFFERENT: self._parse_prefix_expression,
            TokenType.FALSE: self._parse_boolean,
            TokenType.TRUE: self._parse_boolean,
            TokenType.LPAREN: self._parse_grouped_expression,
            TokenType.IF: self._parse_if,
            TokenType.FUNCTION: self._parse_function,
            TokenType.STRING: self._parse_string_literal,
        }