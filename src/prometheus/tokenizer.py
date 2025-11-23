"""
Prometheus Tokenizer
Tokenizes Lua/LuaU source code into tokens
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class TokenType(Enum):
    """Token types for Lua/LuaU"""
    EOF = 'EOF'
    KEYWORD = 'KEYWORD'
    IDENTIFIER = 'IDENTIFIER'
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    OPERATOR = 'OPERATOR'
    SYMBOL = 'SYMBOL'


@dataclass
class Token:
    """Represents a single token"""
    type: TokenType
    value: str
    line: int
    column: int

    def copy_with(self, value: str):
        return Token(self.type, value, self.line, self.column)


class Tokenizer:
    """Tokenizer for Lua/LuaU code"""

    KEYWORDS = {
        'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for',
        'function', 'if', 'in', 'local', 'nil', 'not', 'or', 'repeat',
        'return', 'then', 'true', 'until', 'while'
    }

    LUAU_KEYWORDS = {'continue', 'type', 'export'}

    MULTI_CHAR_OPERATORS = (
        '..<', '::', '==', '~=', '<=', '>=', '..', '//', '...'
    )

    SINGLE_CHAR_OPERATORS = set('+-*/%^#=<>')

    SYMBOLS = set('(){}[];,.:')

    def __init__(self, lua_version: str = 'LuaU'):
        self.lua_version = lua_version
        self.keywords = set(self.KEYWORDS)
        if lua_version == 'LuaU':
            self.keywords.update(self.LUAU_KEYWORDS)

    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        i = 0
        line = 1
        column = 1
        length = len(source)

        while i < length:
            ch = source[i]

            # Whitespace
            if ch in ' \t\r':
                i, column = self._consume_whitespace(source, i, column)
                continue
            if ch == '\n':
                i += 1
                line += 1
                column = 1
                continue

            # Comments
            if ch == '-' and self._peek(source, i + 1) == '-':
                i, line, column = self._consume_comment(source, i, line, column)
                continue

            # Long strings
            if ch == '[':
                long_string = self._consume_long_string(source, i, line, column)
                if long_string is not None:
                    value, consumed, new_lines, tail_len = long_string
                    tokens.append(Token(TokenType.STRING, value, line, column))
                    line += new_lines
                    if new_lines:
                        column = tail_len + 1
                    else:
                        column += consumed
                    i += consumed
                    continue

            # Strings
            if ch in ('"', "'"):
                value, consumed, new_lines, line_len = self._consume_string(source, i)
                tokens.append(Token(TokenType.STRING, value, line, column))
                line += new_lines
                if new_lines:
                    column = line_len + 1
                else:
                    column += consumed
                i += consumed
                continue

            # Numbers
            if ch.isdigit() or (ch == '.' and self._peek(source, i + 1).isdigit()):
                value, consumed = self._consume_number(source, i)
                tokens.append(Token(TokenType.NUMBER, value, line, column))
                i += consumed
                column += consumed
                continue

            # Identifiers/keywords
            if ch.isalpha() or ch == '_':
                value, consumed = self._consume_identifier(source, i)
                token_type = TokenType.KEYWORD if value in self.keywords else TokenType.IDENTIFIER
                tokens.append(Token(token_type, value, line, column))
                i += consumed
                column += consumed
                continue

            # Multi character operators
            matched = False
            for op in sorted(self.MULTI_CHAR_OPERATORS, key=len, reverse=True):
                if source.startswith(op, i):
                    tokens.append(Token(TokenType.OPERATOR, op, line, column))
                    i += len(op)
                    column += len(op)
                    matched = True
                    break
            if matched:
                continue

            # Single char operators and symbols
            if ch in self.SINGLE_CHAR_OPERATORS:
                tokens.append(Token(TokenType.OPERATOR, ch, line, column))
                i += 1
                column += 1
                continue
            if ch in self.SYMBOLS:
                tokens.append(Token(TokenType.SYMBOL, ch, line, column))
                i += 1
                column += 1
                continue

            # Unknown char
            i += 1
            column += 1

        tokens.append(Token(TokenType.EOF, '', line, column))
        return tokens

    def _peek(self, source: str, index: int) -> str:
        if 0 <= index < len(source):
            return source[index]
        return '\0'

    def _consume_whitespace(self, source: str, index: int, column: int):
        while index < len(source) and source[index] in ' \t\r':
            index += 1
            column += 1
        return index, column

    def _consume_comment(self, source: str, index: int, line: int, column: int):
        index += 2  # skip --
        column += 2
        if source.startswith('[', index):
            long_string = self._consume_long_string(source, index, line, column)
            if long_string is not None:
                _, consumed, new_lines, tail_len = long_string
                line += new_lines
                if new_lines:
                    column = tail_len + 1
                else:
                    column += consumed
                return index + consumed, line, column
        while index < len(source) and source[index] != '\n':
            index += 1
            column += 1
        return index, line, column

    def _consume_long_string(self, source: str, index: int, line: int, column: int):
        equals = 0
        i = index + 1
        while i < len(source) and source[i] == '=':
            equals += 1
            i += 1
        if i >= len(source) or source[i] != '[':
            return None
        i += 1
        start = i
        end_token = ']' + ('=' * equals) + ']'
        end_pos = source.find(end_token, i)
        if end_pos == -1:
            return None
        value = source[start:end_pos]
        consumed = end_pos + len(end_token) - index
        new_lines = value.count('\n')
        if new_lines:
            tail_length = len(value.rsplit('\n', 1)[-1])
        else:
            tail_length = consumed
        return value, consumed, new_lines, tail_length

    def _consume_string(self, source: str, index: int):
        quote = source[index]
        i = index + 1
        value = []
        new_lines = 0
        last_line_length = 0
        current_line_length = 0
        while i < len(source):
            ch = source[i]
            if ch == quote:
                break
            if ch == '\\' and i + 1 < len(source):
                value.append(ch)
                i += 1
                ch = source[i]
            if ch == '\n':
                new_lines += 1
                last_line_length = current_line_length
                current_line_length = 0
            else:
                current_line_length += 1
            value.append(ch)
            i += 1
        i += 1  # closing quote
        consumed = i - index
        return ''.join(value), consumed, new_lines, current_line_length

    def _consume_number(self, source: str, index: int):
        i = index
        if source.startswith(('0x', '0X'), i):
            i += 2
            while i < len(source) and (source[i].isdigit() or source[i].lower() in 'abcdef'):
                i += 1
        else:
            while i < len(source) and (source[i].isdigit() or source[i] == '.'):
                i += 1
            if i < len(source) and source[i] in ('e', 'E'):
                i += 1
                if i < len(source) and source[i] in ('+', '-'):
                    i += 1
                while i < len(source) and source[i].isdigit():
                    i += 1
        return source[index:i], i - index

    def _consume_identifier(self, source: str, index: int):
        i = index
        while i < len(source) and (source[i].isalnum() or source[i] == '_'):
            i += 1
        return source[index:i], i - index
