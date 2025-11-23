#!/usr/bin/env python3
"""
Prometheus Lua Obfuscator - Python Implementation for LuaU
This Script is Part of the Prometheus Obfuscator
Main CLI entry point
"""

import argparse
import ast
import json
import os
import sys
from pathlib import Path
import copy

from src.logger import Logger, LogLevel
from src.config import Config, Presets
from src.pipeline import Pipeline


def file_exists(filepath):
    """Check if a file exists"""
    return Path(filepath).is_file()


def read_file(filepath):
    """Read file contents"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def load_config_file(filepath, logger):
    """Load a config file (JSON or Python literal)"""
    content = read_file(filepath)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        try:
            data = ast.literal_eval(content)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(f'Failed to parse config file: {exc}')
            raise
    if not isinstance(data, dict):
        logger.error('Config file must define a dictionary with pipeline options')
    return data


def write_file(filepath, content):
    """Write content to file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Prometheus - Lua Obfuscator for LuaU',
        prog='prometheus'
    )
    
    parser.add_argument(
        'input',
        help='Input Lua file to obfuscate'
    )
    
    parser.add_argument(
        '--preset', '-p',
        choices=['Minify', 'Weak', 'Medium', 'Strong'],
        default='Minify',
        help='Obfuscation preset to use (default: Minify)'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Path to custom config file'
    )
    
    parser.add_argument(
        '--out', '-o',
        help='Output file path (default: input.obfuscated.lua)'
    )
    
    parser.add_argument(
        '--nocolors',
        action='store_true',
        help='Disable colored output'
    )
    
    parser.add_argument(
        '--LuaU',
        action='store_true',
        help='Use LuaU syntax (default)'
    )
    
    parser.add_argument(
        '--Lua51',
        action='store_true',
        help='Use Lua 5.1 syntax'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Enable pretty printing'
    )
    
    args = parser.parse_args()
    
    # Initialize logger
    logger = Logger()
    logger.log_level = LogLevel.INFO
    logger.colors_enabled = not args.nocolors
    
    # Check input file exists
    if not file_exists(args.input):
        logger.error(f'The file "{args.input}" was not found!')
        sys.exit(1)
    
    # Determine config
    base_config = Presets.get(args.preset)
    config = None
    if args.config:
        if not file_exists(args.config):
            logger.error(f'The config file "{args.config}" was not found!')
            sys.exit(1)
        try:
            custom_config = load_config_file(args.config, logger)
        except Exception:
            sys.exit(1)
        if base_config:
            config = copy.deepcopy(base_config)
            config.update(custom_config)
        else:
            config = custom_config
    else:
        config = copy.deepcopy(base_config) if base_config else {}
    
    if not config:
        logger.warn('No config specified, falling back to Minify preset')
        config = copy.deepcopy(Presets.get('Minify'))
    
    # Override Lua version
    if args.Lua51:
        config['LuaVersion'] = 'Lua51'
    elif args.LuaU:
        config['LuaVersion'] = 'LuaU'
    
    # Override pretty print
    if args.pretty:
        config['PrettyPrint'] = True
    
    # Determine output file
    out_file = args.out
    if not out_file:
        if args.input.endswith('.lua'):
            out_file = args.input[:-4] + '.obfuscated.lua'
        else:
            out_file = args.input + '.obfuscated.lua'
    
    # Read source file
    try:
        source = read_file(args.input)
    except Exception as e:
        logger.error(f'Failed to read input file: {e}')
        sys.exit(1)
    
    # Create and run pipeline
    try:
        pipeline = Pipeline.from_config(config, logger)
        output = pipeline.apply(source, args.input)
        
        # Write output
        logger.info(f'Writing output to "{out_file}"')
        write_file(out_file, output)
        logger.info('Done!')
        
    except Exception as e:
        logger.error(f'Obfuscation failed: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
