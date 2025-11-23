"""
Prometheus Unparser
Converts AST back into Lua/LuaU source code
"""

from .tokenizer import TokenType


class Unparser:
    """Unparser to generate code from AST"""
    
    def __init__(self, lua_version='LuaU', pretty_print=False):
        self.lua_version = lua_version
        self.pretty_print = pretty_print
    
    def unparse(self, ast):
        """Generate Lua/LuaU code from AST"""
        parts = []
        previous = None
        
        for token in ast.tokens:
            if token.type == TokenType.EOF:
                continue
            
            text = self._format_token(token)
            if previous is not None and self._needs_space(previous, token):
                parts.append(' ')
            parts.append(text)
            previous = token
        
        code = ''.join(parts)
        if self.pretty_print:
            code = self._pretty_print(code)
        return code
    
    def _format_token(self, token):
        """Format token into text"""
        if token.type == TokenType.STRING:
            escaped = token.value.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        return token.value
    
    def _needs_space(self, prev, curr):
        """Determine if a space is required between two tokens"""
        identifier_like = {TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.NUMBER}
        if prev.type in identifier_like and curr.type in identifier_like:
            return True
        if prev.type in identifier_like and curr.value == '(' and curr.type == TokenType.SYMBOL:
            return False
        if prev.type == TokenType.STRING and curr.type in identifier_like:
            return True
        if curr.type == TokenType.STRING and prev.type in identifier_like:
            return True
        if prev.value in (')', ']', '}') and curr.type in identifier_like:
            return True
        if prev.type in identifier_like and curr.value in ('(', '['):
            return False
        if prev.value in ('.', ':', '::'):
            return False
        if curr.value in ('.', ':', '::'):
            return False
        if prev.value in ('..', '...') or curr.value in ('..', '...'):
            return False
        return False
    
    def _pretty_print(self, code):
        """Simple pretty printer that indents control structures"""
        indent = 0
        formatted = []
        tokens = []
        current = ''
        for ch in code:
            if ch in '(){}[];,' or ch.isspace():
                if current:
                    tokens.append(current)
                    current = ''
                if ch.strip():
                    tokens.append(ch)
            else:
                current += ch
        if current:
            tokens.append(current)
        
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok in ('then', 'do', '{'):
                formatted.append('    ' * indent + tok)
                formatted.append('\n')
                indent += 1
            elif tok == 'function':
                formatted.append('    ' * indent + tok + ' ')
            elif tok in ('end', '}', 'until'):
                indent = max(0, indent - 1)
                formatted.append('    ' * indent + tok)
                formatted.append('\n')
            else:
                formatted.append('    ' * indent + tok)
                formatted.append('\n')
            i += 1
        
        return ''.join(formatted)
