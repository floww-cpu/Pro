# Migration from Lua to Python

This document describes the migration of Prometheus from Lua to Python.

## Overview

Prometheus has been rewritten in Python 3 while maintaining its core functionality of obfuscating Lua and LuaU code. The new implementation is simpler but provides the essential obfuscation features.

## Changes

### Language
- **Before**: Pure Lua implementation
- **After**: Python 3.7+ implementation

### Architecture
- Tokenizer: Converts Lua/LuaU source code into tokens
- Parser: Creates a simple AST (Abstract Syntax Tree) from tokens
- Pipeline: Orchestrates obfuscation steps
- Unparser: Generates obfuscated code from the AST
- Steps: Individual obfuscation transformations

### Supported Steps
The following obfuscation steps are implemented:

1. **EncryptStrings**: Encrypts string literals
2. **Vmify**: Wraps code in a VM-like loader
3. **ConstantArray**: Extracts constants to an array
4. **WrapInFunction**: Wraps code in a function
5. **AntiTamper**: Adds tampering detection
6. **ControlFlowFlattening**: Flattens control flow
7. **NumbersToExpressions**: Converts numbers to expressions

### Presets
All original presets are maintained:
- **Minify**: Basic minification with variable renaming
- **Weak**: Light obfuscation
- **Medium**: Moderate obfuscation  
- **Strong**: Heavy obfuscation

### CLI
The command-line interface remains similar:

```bash
# Old (Lua)
lua ./cli.lua --preset Medium ./your_file.lua

# New (Python)
python3 prometheus.py --preset Medium ./your_file.lua
```

### Files Removed
All Lua implementation files have been removed:
- `src/**/*.lua` - All Lua source files
- `tests/*.lua` - Old test files (except test inputs)
- `doc/` - Old documentation
- `cli.lua`, `benchmark.lua`, `build.bat`, etc.

### Files Added
- `prometheus.py` - Main CLI entry point
- `src/__init__.py` - Package marker
- `src/logger.py` - Logging utilities
- `src/config.py` - Configuration and presets
- `src/pipeline.py` - Main obfuscation pipeline
- `src/prometheus/` - Core modules
  - `tokenizer.py` - Lexical analysis
  - `parser.py` - Syntax analysis
  - `unparser.py` - Code generation
  - `renamer.py` - Variable renaming
  - `namegen.py` - Name generation
  - `steps.py` - Obfuscation steps
  - `context.py` - Pipeline context

## Requirements

- Python 3.7 or higher
- No external dependencies required for basic functionality

## Usage

### Basic Usage
```bash
python3 prometheus.py input.lua
```

### With Preset
```bash
python3 prometheus.py --preset Medium input.lua
```

### Specify Output
```bash
python3 prometheus.py --out output.lua input.lua
```

### Pretty Print
```bash
python3 prometheus.py --pretty input.lua
```

## Known Limitations

1. The Python implementation is a simplified version focusing on core obfuscation
2. Some advanced features from the original Lua version may not be fully implemented
3. Pretty printing is basic and may not produce perfectly formatted code
4. Custom config files support JSON and Python literal formats

## Benefits

1. **Easier to maintain**: Python is more widely known than Lua
2. **Better tooling**: Python has excellent development tools
3. **Cleaner codebase**: Simplified architecture
4. **Cross-platform**: Works on any system with Python 3
5. **No dependencies**: Pure Python implementation

## Compatibility

The obfuscated output remains compatible with:
- Lua 5.1
- LuaU (Roblox Lua)

## Testing

Test files are included in the `tests/` directory:
- `tests/simple.lua` - Basic test file
- `tests/test_pipeline.py` - Unit tests

Run tests with:
```bash
python3 -m pytest tests/
```

## License

Maintains the original GNU Affero General Public License v3.0.
