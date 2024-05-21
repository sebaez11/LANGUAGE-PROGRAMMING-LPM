from enum import (
    auto,
    Enum,
    unique,
)
from typing import (
    NamedTuple,
    Dict,
)

@unique
class TokenType(Enum):
    ASSIGN = auto()
    COMMA = auto()
    DIFFERENT = auto()
    DIVIDE = auto()
    ELSE = auto()
    EOF = auto()
    EQ = auto()
    FALSE = auto()
    FUNCTION = auto()
    GT = auto()
    IDENT = auto()
    IF = auto()
    ILLEGAL = auto()
    INT = auto()
    LBRACE = auto()
    LET = auto()
    LPAREN = auto()
    LT = auto()
    MULTIPLICATION = auto()
    NOT_EQ = auto()
    PLUS = auto()
    RBRACE = auto()
    RETURN = auto()
    RPAREN = auto()
    SEMICOLON = auto()
    SUBSTRACT = auto()
    TRUE = auto()

class Token(NamedTuple):
    token_type: TokenType
    literal: str

    def __str__(self) -> str:
        return f'Type: {self.token_type} Literal: {self.literal}'


def lookup_token_type(literal: str) -> TokenType:
    keywords: Dict[str, TokenType] = {
        'variable': TokenType.LET,
        'procedimiento': TokenType.FUNCTION,
        'si': TokenType.IF,
        'falso': TokenType.FALSE,
        'regresa': TokenType.RETURN,
        'si_no': TokenType.ELSE,
        'verdadero': TokenType.TRUE,
    }

    return keywords.get(literal, TokenType.IDENT)