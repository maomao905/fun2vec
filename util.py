import os
import json, yaml
import logging
import logging.config
from flask_script import Manager
from pygments.lexer import RegexLexer
import re
from pygments.token import Token, String, Number
from pygments.style import Style

def load_config(name):
    with open(os.path.join('config', name + '_config.yml'), 'r') as f:
        config = yaml.load(f)
        return config

logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

def read_sql(file_path):
    with open(file_path, 'r') as f:
        sql = f.read()
    return sql

def read_secrets(key):
    FILE_SECRETS = os.path.join('config', 'secrets.yml')
    with open(FILE_SECRETS, 'r') as f:
        data = yaml.load(f)
    return data.get(key)

def ljust_ja(text, length):
    text_length = 0
    for char in text:
        if ord(char) <= 255:
            text_length += 1
        else:
            text_length += 2

    return text + (length - text_length) * ' '

class CustomLexer(RegexLexer):
    flags = re.IGNORECASE
    tokens = {
        'root': [
            (r'^[^\W]+',    String),
            (r'0\.[0-9]+$', Number)
        ]
    }

def get_color_style(sim):
    SIM_COLORS = {
        'low':          '#b22222',
        'normal':       '#00bfff',
        'high':         '#ansiteal',
        'extreme_high': '#ansiturquoise'
    }
    sim_color = None
    if sim >= 0.9:
        sim_color = SIM_COLORS['extreme_high']
    elif sim >= 0.8:
        sim_color = SIM_COLORS['high']
    elif sim >= 0.7:
        sim_color = SIM_COLORS['normal']
    else:
        sim_color = SIM_COLORS['low']

    class ColorStyle(Style):
        styles = {
            Token.String: '#ff8c00',
            Token.Number: sim_color
        }
    return ColorStyle
