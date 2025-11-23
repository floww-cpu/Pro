"""
Prometheus Pipeline
Main obfuscation pipeline that coordinates parsing, transformation, and unparsing
"""

import time
import random
from src.prometheus.tokenizer import Tokenizer
from src.prometheus.parser import Parser
from src.prometheus.unparser import Unparser
from src.prometheus.namegen import create_generator
from src.prometheus.renamer import VariableRenamer
from src.prometheus.context import PipelineContext
from src.prometheus.steps import STEP_REGISTRY


class Pipeline:
    """Obfuscation pipeline"""
    
    def __init__(self, config, logger):
        """Initialize pipeline with config"""
        self.config = config
        self.logger = logger
        self.lua_version = config.get('LuaVersion', 'LuaU')
        self.pretty_print = config.get('PrettyPrint', False)
        self.var_name_prefix = config.get('VarNamePrefix', '')
        self.seed = config.get('Seed', 0)
        self.steps = []
        
        # Initialize tokenizer, parser, and unparser
        self.tokenizer = Tokenizer(self.lua_version)
        self.parser = Parser(self.lua_version)
        self.unparser = Unparser(self.lua_version, self.pretty_print)
    
    @classmethod
    def from_config(cls, config, logger):
        """Create pipeline from config dict"""
        pipeline = cls(config, logger)
        
        # Add steps from config
        steps = config.get('Steps', [])
        for step_config in steps:
            step_name = step_config.get('Name')
            step_settings = step_config.get('Settings', {})
            step_class = STEP_REGISTRY.get(step_name)
            if step_class:
                pipeline.steps.append(step_class(step_settings))
            else:
                logger.warn(f'Unknown step "{step_name}", skipping')
        
        return pipeline
    
    def apply(self, code, filename='Anonymous Script'):
        """Apply obfuscation pipeline to code"""
        start_time = time.time()
        self.logger.info(f"Applying Obfuscation Pipeline to {filename} ...")
        
        # Seed random generator
        seed = self.seed if self.seed > 0 else int(time.time())
        rng = random.Random(seed)
        
        source_len = len(code)
        
        # Tokenize
        self.logger.info("Tokenizing ...")
        tokens = self.tokenizer.tokenize(code)
        
        # Parse
        self.logger.info("Parsing ...")
        parse_start = time.time()
        ast = self.parser.parse(tokens)
        parse_time = time.time() - parse_start
        self.logger.info(f"Parsing Done in {parse_time:.2f} seconds")
        
        # Create pipeline context
        context = PipelineContext(
            self.config,
            self.logger,
            self.tokenizer,
            self.parser,
            self.unparser,
            rng
        )
        
        # Apply obfuscation steps
        for step in self.steps:
            step_start = time.time()
            step_name = step.NAME
            self.logger.info(f'Applying Step "{step_name}" ...')
            ast = step.apply(ast, context)
            step_time = time.time() - step_start
            self.logger.info(f'Step "{step_name}" Done in {step_time:.2f} seconds')
        
        # Rename variables
        self.rename_variables(ast, seed)
        
        # Unparse (generate code)
        code = self.unparse(ast)
        
        total_time = time.time() - start_time
        self.logger.info(f"Obfuscation Done in {total_time:.2f} seconds")
        
        size_percent = (len(code) / source_len) * 100
        self.logger.info(f"Generated Code size is {size_percent:.2f}% of the Source Code size")
        
        return code
    
    def rename_variables(self, ast, seed):
        """Rename variables in AST"""
        start_time = time.time()
        self.logger.info("Renaming Variables ...")
        
        # Create name generator
        generator_name = self.config.get('NameGenerator', 'MangledShuffled')
        generator = create_generator(
            generator_name,
            prefix=self.var_name_prefix,
            reserved=set(self.tokenizer.keywords),
            seed=seed
        )
        
        # Apply variable renaming
        renamer = VariableRenamer(ast.tokens, generator, self.tokenizer.keywords)
        ast.tokens = renamer.rename()
        
        rename_time = time.time() - start_time
        self.logger.info(f"Renaming Done in {rename_time:.2f} seconds")
    
    def unparse(self, ast):
        """Generate code from AST"""
        start_time = time.time()
        self.logger.info("Generating Code ...")
        
        code = self.unparser.unparse(ast)
        
        unparse_time = time.time() - start_time
        self.logger.info(f"Code Generation Done in {unparse_time:.2f} seconds")
        
        return code
