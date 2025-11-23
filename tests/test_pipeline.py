"""Tests for the Python Prometheus pipeline"""

import unittest

from src.pipeline import Pipeline
from src.config import Presets
from src.logger import Logger, LogLevel


def build_logger():
    logger = Logger()
    logger.log_level = LogLevel.WARN
    logger.colors_enabled = False
    return logger


class PipelineTests(unittest.TestCase):
    """Unit tests for the pipeline"""

    def test_minify_preset_renames_locals(self):
        code = """local function greet(name)
        local message = "Hello, " .. name
        print(message)
end
"""
        config = Presets.get('Minify').copy()
        pipeline = Pipeline.from_config(config, build_logger())
        result = pipeline.apply(code, filename='test.lua')
        self.assertNotIn('message', result)
        self.assertNotIn('greet', result)
        self.assertIn('print', result)

    def test_encrypt_strings_inserts_helper(self):
        code = 'return "Hello"'
        config = Presets.get('Minify').copy()
        config['Steps'] = [{'Name': 'EncryptStrings', 'Settings': {}}]
        pipeline = Pipeline.from_config(config, build_logger())
        result = pipeline.apply(code, filename='test.lua')
        self.assertIn('__PROM_STR', result)
        self.assertNotIn('"Hello"', result)

    def test_vmify_step_generates_data_table(self):
        code = "print('ok')"
        config = Presets.get('Minify').copy()
        config['Steps'] = [{'Name': 'Vmify', 'Settings': {}}]
        pipeline = Pipeline.from_config(config, build_logger())
        result = pipeline.apply(code, filename='test.lua')
        self.assertIn('__PROM_DATA', result)
        self.assertNotIn('print', result)


if __name__ == '__main__':
    unittest.main()
