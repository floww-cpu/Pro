# :fire: Prometheus
[![Test](https://github.com/prometheus-lua/Prometheus/actions/workflows/Test.yml/badge.svg)](https://github.com/prometheus-lua/Prometheus/actions/workflows/Test.yml)

## Description
Prometheus is a Lua obfuscator written in Python for LuaU (Roblox's Lua variant).

This Project was inspired by the amazing [javascript-obfuscator](https://github.com/javascript-obfuscator/javascript-obfuscator).   
It can currently obfuscate Lua 5.1 and Roblox's LuaU.

## Installation
To install Prometheus, simply clone the Github Repository using:

```bash
git clone https://github.com/prometheus-lua/Prometheus.git
```

Alternatively you can download the Sources [here](https://github.com/prometheus-lua/Prometheus/archive/refs/heads/master.zip).

Prometheus requires Python 3.7 or higher to work.

## Usage
To quickly obfuscate a script:
```bash
python3 prometheus.py --preset Medium ./your_file.lua
```

Available presets:
- `Minify` - Basic minification (default)
- `Weak` - Light obfuscation
- `Medium` - Moderate obfuscation
- `Strong` - Heavy obfuscation

### Options

- `--preset <preset>` or `-p <preset>` - Choose obfuscation preset
- `--config <file>` or `-c <file>` - Use custom config file
- `--out <file>` or `-o <file>` - Specify output file (default: input.obfuscated.lua)
- `--nocolors` - Disable colored output
- `--LuaU` - Use LuaU syntax (default)
- `--Lua51` - Use Lua 5.1 syntax
- `--pretty` - Enable pretty printing

### Examples

Obfuscate with medium preset:
```bash
python3 prometheus.py --preset Medium script.lua
```

Specify output file:
```bash
python3 prometheus.py --preset Strong --out output.lua script.lua
```

Use Lua 5.1 syntax:
```bash
python3 prometheus.py --Lua51 --preset Medium script.lua
```

## Tests
Basic test files are available in the `tests/` directory.

## License
This Project is Licensed under the GNU Affero General Public License v3.0. For more details, please refer to [LICENSE](https://github.com/prometheus-lua/Prometheus/blob/master/LICENSE).
