"""
Prometheus Parser
Converts token streams into a simple AST structure
"""

from dataclasses import dataclass
from typing import List
from .tokenizer import Token


@dataclass
class Module:
    """Simple AST representation holding tokens"""
    tokens: List[Token]


class Parser:
    """Parser for Lua/LuaU tokens"""
    
    def __init__(self, lua_version='LuaU'):
        self.lua_version = lua_version
    
    def parse(self, tokens: List[Token]) -> Module:
        """Parse tokens into a Module"""
        return Module(tokens=list(tokens))
