"""
Prometheus Configuration
Configuration objects and presets for obfuscation
"""


class Config:
    """Configuration constants"""
    NAME = "Prometheus"
    NAME_UPPER = "PROMETHEUS"
    VERSION = "1.0.0"


class Presets:
    """Obfuscation presets"""
    
    _presets = {
        'Minify': {
            'LuaVersion': 'LuaU',
            'VarNamePrefix': '',
            'NameGenerator': 'MangledShuffled',
            'PrettyPrint': False,
            'Seed': 0,
            'Steps': []
        },
        'Weak': {
            'LuaVersion': 'LuaU',
            'VarNamePrefix': '',
            'NameGenerator': 'MangledShuffled',
            'PrettyPrint': False,
            'Seed': 0,
            'Steps': [
                {
                    'Name': 'Vmify',
                    'Settings': {}
                },
                {
                    'Name': 'ConstantArray',
                    'Settings': {
                        'Threshold': 1,
                        'StringsOnly': True
                    }
                }
            ]
        },
        'Medium': {
            'LuaVersion': 'LuaU',
            'VarNamePrefix': '',
            'NameGenerator': 'MangledShuffled',
            'PrettyPrint': False,
            'Seed': 0,
            'Steps': [
                {
                    'Name': 'EncryptStrings',
                    'Settings': {}
                },
                {
                    'Name': 'Vmify',
                    'Settings': {}
                },
                {
                    'Name': 'ConstantArray',
                    'Settings': {
                        'Threshold': 1,
                        'StringsOnly': False
                    }
                },
                {
                    'Name': 'WrapInFunction',
                    'Settings': {}
                }
            ]
        },
        'Strong': {
            'LuaVersion': 'LuaU',
            'VarNamePrefix': '',
            'NameGenerator': 'MangledShuffled',
            'PrettyPrint': False,
            'Seed': 0,
            'Steps': [
                {
                    'Name': 'EncryptStrings',
                    'Settings': {}
                },
                {
                    'Name': 'Vmify',
                    'Settings': {}
                },
                {
                    'Name': 'ConstantArray',
                    'Settings': {
                        'Threshold': 1,
                        'StringsOnly': False
                    }
                },
                {
                    'Name': 'AntiTamper',
                    'Settings': {}
                },
                {
                    'Name': 'ControlFlowFlattening',
                    'Settings': {}
                },
                {
                    'Name': 'WrapInFunction',
                    'Settings': {}
                }
            ]
        }
    }
    
    @classmethod
    def get(cls, name):
        """Get a preset by name"""
        return cls._presets.get(name)
    
    @classmethod
    def list(cls):
        """List all available presets"""
        return list(cls._presets.keys())
