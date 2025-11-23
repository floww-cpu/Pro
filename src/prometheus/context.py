"""Pipeline context helpers"""

from __future__ import annotations

from typing import Any

from .parser import Parser, Module
from .tokenizer import Tokenizer
from .unparser import Unparser


class PipelineContext:
    """Context shared between obfuscation steps"""

    def __init__(self, config: dict[str, Any], logger, tokenizer: Tokenizer, parser: Parser, unparser: Unparser, rng):
        self.config = config
        self.logger = logger
        self.tokenizer = tokenizer
        self.parser = parser
        self.unparser = unparser
        self.random = rng

    def render(self, module: Module) -> str:
        """Convert module to source code"""
        return self.unparser.unparse(module)

    def module_from_source(self, source: str) -> Module:
        """Create a module from plain source code"""
        tokens = self.tokenizer.tokenize(source)
        return self.parser.parse(tokens)

    def tokens_from_code(self, code: str):
        """Tokenize code snippet (without EOF)"""
        tokens = self.tokenizer.tokenize(code)
        return tokens[:-1]
