"""Obfuscation steps"""

from __future__ import annotations

import textwrap
from typing import List

from .parser import Module
from .tokenizer import Token, TokenType


class BaseStep:
    """Base class for pipeline steps"""

    NAME = "Base"

    def __init__(self, settings: dict | None = None):
        self.settings = settings or {}

    def apply(self, module: Module, context):
        raise NotImplementedError

    def _code_to_tokens(self, code: str, context) -> List[Token]:
        return context.tokens_from_code(code)

    def _indent(self, code: str, indent: str = '    ') -> str:
        return textwrap.indent(code, indent)


class EncryptStringsStep(BaseStep):
    NAME = "EncryptStrings"

    def apply(self, module: Module, context):
        body_tokens = module.tokens[:-1]
        eof = module.tokens[-1]
        rng = context.random
        threshold = int(self.settings.get('MinLength', 1))
        transformed = False
        new_tokens: List[Token] = []

        for token in body_tokens:
            if token.type == TokenType.STRING and len(token.value) >= threshold:
                key = rng.randint(5, 40)
                encoded = [(ord(char) + key + idx) % 256 for idx, char in enumerate(token.value, start=1)]
                table_literal = '{' + ','.join(str(value) for value in encoded) + '}'
                expr = f"__PROM_STR({table_literal}, {key})"
                new_tokens.extend(self._code_to_tokens(expr, context))
                transformed = True
            else:
                new_tokens.append(token)

        if transformed:
            helper_code = (
                "local function __PROM_STR(bytes, key)\n"
                "    local out = {}\n"
                "    for i = 1, #bytes do\n"
                "        local value = (bytes[i] - key - i) % 256\n"
                "        out[i] = string.char(value)\n"
                "    end\n"
                "    return table.concat(out)\n"
                "end\n"
            )
            helper_tokens = self._code_to_tokens(helper_code, context)
            module.tokens = helper_tokens + new_tokens + [eof]
        else:
            module.tokens = body_tokens + [eof]
        return module


class ConstantArrayStep(BaseStep):
    NAME = "ConstantArray"

    def apply(self, module: Module, context):
        threshold = int(self.settings.get('Threshold') or self.settings.get('Treshold') or 2)
        strings_only = bool(self.settings.get('StringsOnly', True))
        body_tokens = module.tokens[:-1]
        eof = module.tokens[-1]

        counts = {}
        for token in body_tokens:
            if token.type == TokenType.STRING:
                key = (TokenType.STRING, token.value)
            elif not strings_only and token.type == TokenType.NUMBER:
                key = (TokenType.NUMBER, token.value)
            else:
                continue
            counts[key] = counts.get(key, 0) + 1

        replacements = {key: idx + 1 for idx, (key, count) in enumerate(counts.items()) if count >= threshold}
        if not replacements:
            module.tokens = body_tokens + [eof]
            return module

        array_entries = []
        for key, index in replacements.items():
            token_type, value = key
            if token_type == TokenType.STRING:
                array_entries.append(f'[{index}] = "{value.replace("\\", "\\\\").replace("\"", "\\\"")}"')
            else:
                array_entries.append(f'[{index}] = {value}')
        array_code = f"local __PROM_CONST = {{{', '.join(array_entries)}}}\n"
        array_tokens = self._code_to_tokens(array_code, context)

        new_tokens: List[Token] = []
        for token in body_tokens:
            replacement_key = None
            if token.type == TokenType.STRING:
                replacement_key = (TokenType.STRING, token.value)
            elif not strings_only and token.type == TokenType.NUMBER:
                replacement_key = (TokenType.NUMBER, token.value)

            if replacement_key and replacement_key in replacements:
                expr = f"__PROM_CONST[{replacements[replacement_key]}]"
                new_tokens.extend(self._code_to_tokens(expr, context))
            else:
                new_tokens.append(token)

        module.tokens = array_tokens + new_tokens + [eof]
        return module


class WrapInFunctionStep(BaseStep):
    NAME = "WrapInFunction"

    def apply(self, module: Module, context):
        source = context.render(module)
        wrapped = (
            "return (function()\n"
            f"{self._indent(source)}\n"
            "end)()\n"
        )
        return context.module_from_source(wrapped)


class VmifyStep(BaseStep):
    NAME = "Vmify"

    def apply(self, module: Module, context):
        source = context.render(module)
        data = ','.join(str(byte) for byte in source.encode('utf-8'))
        vm_code = (
            "local __PROM_DATA = {" + data + "}\n"
            "local __PROM_LOAD = loadstring or load\n"
            "local __PROM_BUFFER = {}\n"
            "for i = 1, #__PROM_DATA do\n"
            "    __PROM_BUFFER[i] = string.char(__PROM_DATA[i])\n"
            "end\n"
            "local __PROM_SOURCE = table.concat(__PROM_BUFFER)\n"
            "return __PROM_LOAD(__PROM_SOURCE)()\n"
        )
        return context.module_from_source(vm_code)


class AntiTamperStep(BaseStep):
    NAME = "AntiTamper"

    def apply(self, module: Module, context):
        rng = context.random
        sentinel = rng.randint(10_000, 99_999)
        check_code = (
            f"local __PROM_SENTINEL = {sentinel}\n"
            "local function __PROM_TAMPER(value)\n"
            "    if value ~= __PROM_SENTINEL then\n"
            "        error('Tampering detected', 0)\n"
            "    end\n"
            "end\n"
            f"__PROM_TAMPER(({sentinel} ~ {sentinel}) ~ 0)\n"
        )
        helper_tokens = self._code_to_tokens(check_code, context)
        body_tokens = module.tokens[:-1]
        eof = module.tokens[-1]
        module.tokens = helper_tokens + body_tokens + [eof]
        return module


class ControlFlowFlatteningStep(BaseStep):
    NAME = "ControlFlowFlattening"

    def apply(self, module: Module, context):
        source = context.render(module)
        flattened = (
            "local function __PROM_FLOW()\n"
            "    local __PROM_STATE = 0\n"
            "    while true do\n"
            "        if __PROM_STATE == 0 then\n"
            f"{self._indent(source, '            ')}\n"
            "            __PROM_STATE = -1\n"
            "        else\n"
            "            break\n"
            "        end\n"
            "    end\n"
            "end\n"
            "__PROM_FLOW()\n"
        )
        return context.module_from_source(flattened)


class NumbersToExpressionsStep(BaseStep):
    NAME = "NumbersToExpressions"

    def apply(self, module: Module, context):
        body_tokens = module.tokens[:-1]
        eof = module.tokens[-1]
        rng = context.random
        new_tokens: List[Token] = []
        for token in body_tokens:
            if token.type == TokenType.NUMBER:
                value = token.value
                parsed = self._parse_number(value)
                if parsed is not None and abs(parsed) > 3:
                    a = rng.randint(1, abs(parsed) - 1)
                    b = parsed - a if parsed >= 0 else -(abs(parsed) - a)
                    expr = f"({a}+{b})"
                    new_tokens.extend(self._code_to_tokens(expr, context))
                else:
                    new_tokens.append(token)
            else:
                new_tokens.append(token)
        module.tokens = new_tokens + [eof]
        return module

    def _parse_number(self, value: str) -> int | None:
        try:
            if value.lower().startswith('0x'):
                return int(value, 16)
            if any(ch in value for ch in '.eE'):
                return None
            return int(value)
        except ValueError:
            return None


STEP_REGISTRY = {
    EncryptStringsStep.NAME: EncryptStringsStep,
    ConstantArrayStep.NAME: ConstantArrayStep,
    WrapInFunctionStep.NAME: WrapInFunctionStep,
    VmifyStep.NAME: VmifyStep,
    AntiTamperStep.NAME: AntiTamperStep,
    ControlFlowFlatteningStep.NAME: ControlFlowFlatteningStep,
    NumbersToExpressionsStep.NAME: NumbersToExpressionsStep,
}
