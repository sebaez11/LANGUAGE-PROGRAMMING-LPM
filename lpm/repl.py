from typing import List
from lpm.ast import Program

from lpm.lexer import Lexer
from lpm.object import Environment
from lpm.parser import Parser
from lpm.evaluator import evaluate
from lpm.token import (
    Token,
    TokenType,
)

EOF_TOKEN: Token = Token(TokenType.EOF, '')

def _print_parse_errors(errors: List[str]):
    for error in errors:
        print(error)

def start_repl() -> None:
    scanned: List[str] = []

    while (source := input('>> ')) != 'salir()':
        scanned.append(source)
        lexer: Lexer = Lexer(' '.join(scanned))
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()
        env: Environment = Environment()

        if len(parser.errors) > 0:
            _print_parse_errors(parser.errors)
            continue

        evaluated = evaluate(program, env)

        if evaluated is not None:
            print(evaluated.inspect())