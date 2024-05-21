from re import match
from lpm.token import (
    Token,
    TokenType,
    lookup_token_type
)

class Lexer:

    def __init__(self, source: str) -> None:
        self._source: str = source
        self._character: str = ''
        self._read_position: int = 0
        self._position: int = 0

        self._read_character()

    def next_token(self) -> Token:
        self._skip_whitespace()
        token_dict = {
            #"^=$": TokenType.ASSIGN,
            "^\+$": TokenType.PLUS,
            "^\($": TokenType.LPAREN,
            "^\)$": TokenType.RPAREN,
            "^{$": TokenType.LBRACE,
            "^}$": TokenType.RBRACE,
            "^,$": TokenType.COMMA,
            "^;$": TokenType.SEMICOLON,
            "^$": TokenType.EOF,
            "^<$": TokenType.LT,
            "^>$": TokenType.GT,
            "^-$": TokenType.SUBSTRACT,
            "^/$": TokenType.DIVIDE,
            "^\*$": TokenType.MULTIPLICATION,
            #"^!$": TokenType.DIFFERENT,
        }

        token = None

        for regex, token_type in token_dict.items():
            if match(regex, self._character):
                token = Token(token_type, self._character)
                break
        
        if match(r'^=$', self._character):
            if self._peek_character() == '=':
                token = self._make_two_character_token(TokenType.EQ)
            else:
                token = Token(TokenType.ASSIGN, self._character)
        elif match(r'^!$', self._character):
            if self._peek_character() == '=':
                token = self._make_two_character_token(TokenType.NOT_EQ)
            else:
                token = Token(TokenType.DIFFERENT, self._character)

        if token is None:
            token = Token(TokenType.ILLEGAL, self._character)

        if self._is_letter(self._character):
            literal = self._read_identifier()
            token_type = lookup_token_type(literal)
            return Token(token_type, literal)
        elif self._is_number(self._character):
            literal = self._read_number()
            return Token(TokenType.INT, literal)

        self._read_character()

        return token

    def _is_letter(self, character: str) -> bool:
        return bool(match(r'^[a-záéíóúA-ZÁÉÍÓÚñÑ_]$', character))

    def _is_number(self, character: str) -> bool:
        return bool(match(r'^\d$', character))

    def _make_two_character_token(self, token_type: TokenType) -> Token:
        prefix = self._character
        self._read_character()
        suffix = self._character

        return Token(token_type, f'{prefix}{suffix}')

    def _read_identifier(self) -> str:
        initial_position = self._position

        while self._is_letter(self._character) or self._is_number(self._character):
            self._read_character()
        
        return self._source[initial_position:self._position]

    def _read_number(self) -> str:
        initial_position = self._position

        while self._is_number(self._character):
            self._read_character()

        return self._source[initial_position:self._position]

    def _peek_character(self) -> str:
        if self._read_position >= len(self._source):
            return ''
        
        return self._source[self._read_position]

    def _skip_whitespace(self) -> None:
        while match(r'^\s$', self._character):
            self._read_character()

    def _read_character(self) -> None:
        if self._read_position >= len(self._source):
            self._character = ''
        else:
            self._character = self._source[self._read_position]

        self._position = self._read_position
        self._read_position += 1