"""Name generator utilities for Prometheus"""

from typing import Iterator, List, Set
import random


class NameGenerator:
    """Generates obfuscated variable names"""

    DEFAULT_ALPHABET = list('lI1O0')

    def __init__(self, prefix: str = '', reserved: Set[str] | None = None, seed: int | None = None):
        self.prefix = prefix
        self.reserved = set(reserved or [])
        self.counter = 0
        self.rng = random.Random(seed)
        self.alphabet = self.DEFAULT_ALPHABET.copy()
        self.rng.shuffle(self.alphabet)

    def next_name(self) -> str:
        """Generate the next obfuscated name"""
        while True:
            name = self._encode(self.counter)
            self.counter += 1
            candidate = f"{self.prefix}{name}"
            if candidate not in self.reserved:
                self.reserved.add(candidate)
                return candidate

    def _encode(self, value: int) -> str:
        base = len(self.alphabet)
        if base == 0:
            raise ValueError('Alphabet cannot be empty')
        number = value
        chars: List[str] = []
        while True:
            number, remainder = divmod(number, base)
            chars.append(self.alphabet[remainder])
            if number == 0:
                break
            number -= 1
        return ''.join(chars)


def create_generator(name: str, prefix: str = '', reserved: Set[str] | None = None, seed: int | None = None) -> NameGenerator:
    """Factory for name generators"""
    generator = NameGenerator(prefix=prefix, reserved=reserved, seed=seed)
    if name.lower() in ('mangled', 'mangledshuffled', 'mangled_shuffled'):
        return generator
    return generator
