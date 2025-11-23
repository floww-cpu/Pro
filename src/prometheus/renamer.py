"""Variable renaming utilities"""

from __future__ import annotations

from typing import Dict, List, Optional

from .tokenizer import Token, TokenType
from .namegen import NameGenerator


class VariableRenamer:
    """Renames local variables while respecting Lua scoping rules"""

    def __init__(self, tokens: List[Token], generator: NameGenerator, keywords: set[str]):
        self.tokens = tokens
        self.generator = generator
        self.keywords = keywords
        self.scope_stack: List[Dict[str, str]] = [dict()]
        self.block_stack: List[str] = []
        self.pending_for_scopes: List[bool] = []

    def rename(self) -> List[Token]:
        i = 0
        while i < len(self.tokens):
            token = self.tokens[i]
            if token.type == TokenType.EOF:
                break
            if token.type == TokenType.KEYWORD:
                handler = getattr(self, f"_handle_{token.value}", None)
                if handler:
                    i = handler(i)
                    continue
            if token.type == TokenType.IDENTIFIER:
                self._replace_identifier(i)
            i += 1
        return self.tokens

    # -----------------
    # Scope management
    # -----------------

    def _push_scope(self, block_type: str):
        self.scope_stack.append({})
        self.block_stack.append(block_type)

    def _pop_scope(self):
        if self.block_stack:
            self.block_stack.pop()
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def _pop_until(self, *block_types: str):
        while self.block_stack:
            block = self.block_stack[-1]
            self._pop_scope()
            if block in block_types:
                break

    def _declare(self, name: str) -> str:
        if name == '_' or name.startswith('...'):
            return name
        if name.startswith('__PROM_'):
            self.scope_stack[-1][name] = name
            return name
        new_name = self.generator.next_name()
        self.scope_stack[-1][name] = new_name
        return new_name

    def _resolve(self, name: str) -> Optional[str]:
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    # -----------------
    # Helpers
    # -----------------

    def _previous_token(self, index: int) -> Optional[Token]:
        if index <= 0:
            return None
        return self.tokens[index - 1]

    def _next_token(self, index: int) -> Optional[Token]:
        if index + 1 >= len(self.tokens):
            return None
        return self.tokens[index + 1]

    def _is_property_access(self, index: int) -> bool:
        prev_token = self._previous_token(index)
        next_token = self._next_token(index)
        if prev_token and prev_token.value in ('.', ':', '::'):
            return True
        if next_token and next_token.value == '::':
            return True
        return False

    def _skip_type_annotation(self, index: int) -> int:
        i = index
        if i < len(self.tokens) and self.tokens[i].value == ':':
            i += 1
            depth = 0
            while i < len(self.tokens):
                token = self.tokens[i]
                if depth == 0 and token.value in (',', '=', ')', ';'):  # end of annotation
                    break
                if token.value in ('<', '(', '['):
                    depth += 1
                elif token.value in ('>', ')', ']'):
                    if depth > 0:
                        depth -= 1
                    else:
                        break
                i += 1
        return i

    def _replace_identifier(self, index: int):
        if self._is_property_access(index):
            return
        name = self.tokens[index].value
        replacement = self._resolve(name)
        if replacement:
            self.tokens[index] = self.tokens[index].copy_with(replacement)

    # -----------------
    # Keyword handlers
    # -----------------

    def _handle_local(self, index: int) -> int:
        i = index + 1
        if i < len(self.tokens) and self.tokens[i].type == TokenType.KEYWORD and self.tokens[i].value == 'function':
            # local function definition
            name_index = i + 1
            if name_index < len(self.tokens) and self.tokens[name_index].type == TokenType.IDENTIFIER:
                new_name = self._declare(self.tokens[name_index].value)
                self.tokens[name_index] = self.tokens[name_index].copy_with(new_name)
            return index + 1  # continue with function handler

        while i < len(self.tokens):
            token = self.tokens[i]
            if token.type == TokenType.IDENTIFIER:
                new_name = self._declare(token.value)
                self.tokens[i] = token.copy_with(new_name)
                i = self._skip_type_annotation(i + 1)
                if i < len(self.tokens) and self.tokens[i].value == ',':
                    i += 1
                    continue
                break
            if token.value == ',':
                i += 1
                continue
            break
        return i

    def _handle_function(self, index: int) -> int:
        self._push_scope('function')
        i = index + 1
        # Skip function name (supports foo.bar:baz)
        while i < len(self.tokens) and self.tokens[i].value != '(':
            i += 1
        if i >= len(self.tokens):
            return i
        i += 1  # skip '('
        while i < len(self.tokens) and self.tokens[i].value != ')':
            token = self.tokens[i]
            if token.type == TokenType.IDENTIFIER and token.value != '...':
                new_name = self._declare(token.value)
                self.tokens[i] = token.copy_with(new_name)
                i = self._skip_type_annotation(i + 1)
                continue
            if token.value in (',', '...'):
                i += 1
                continue
            i += 1
        return i

    def _handle_for(self, index: int) -> int:
        self._push_scope('for')
        self.pending_for_scopes.append(True)
        i = index + 1
        while i < len(self.tokens):
            token = self.tokens[i]
            if token.type == TokenType.IDENTIFIER:
                new_name = self._declare(token.value)
                self.tokens[i] = token.copy_with(new_name)
                i = self._skip_type_annotation(i + 1)
                continue
            if token.value == ',':
                i += 1
                continue
            if token.value in ('=', 'in'):
                break
            i += 1
        return i

    def _handle_do(self, index: int) -> int:
        if self.pending_for_scopes and self.pending_for_scopes[-1]:
            self.pending_for_scopes.pop()
            return index + 1
        self._push_scope('do')
        return index + 1

    def _handle_then(self, index: int) -> int:
        self._push_scope('then')
        return index + 1

    def _handle_else(self, index: int) -> int:
        self._pop_until('then', 'elseif')
        self._push_scope('else')
        return index + 1

    def _handle_elseif(self, index: int) -> int:
        self._pop_until('then', 'elseif')
        self._push_scope('elseif')
        return index + 1

    def _handle_end(self, index: int) -> int:
        self._pop_scope()
        return index + 1

    def _handle_repeat(self, index: int) -> int:
        self._push_scope('repeat')
        return index + 1

    def _handle_until(self, index: int) -> int:
        self._pop_until('repeat')
        return index + 1
