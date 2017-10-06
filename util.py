import os
import json, yaml
from ansible.parsing import vault
from ansible.parsing.vault import VaultLib
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
    return decrypt().get(key)

def decrypt():
    """
    Decrypt secrets.yml
    """
    file_path = os.path.join('config', 'secrets.yml')
    with open(file_path, 'rb') as f:
        data = f.read()
    vault_lib = VaultLib(os.environ['FUN2VEC_SECRET_PASSWORD'])
    if vault.is_encrypted(data):
        try:
            data = yaml.load(vault_lib.decrypt(data, filename=None))
        except Exception as e:
            import pdb; pdb.set_trace()
        if 'private_key' in data:
            data['private_key'] = data['private_key'].replace('\\n', '\n')
    else:
        data = yaml.load(data)
    return data

manager = Manager(usage='Perform util commands')
@manager.command
def encrypt():
    'Encrypt secrets.yml'
    file_path = os.path.join('config', 'secrets.yml')
    with open(file_path, 'r') as f:
        data = yaml.load(f)
    if vault.is_encrypted(data):
        return
    vault_lib = VaultLib(os.environ['FUN2VEC_SECRET_PASSWORD'])
    with open(file_path,'wb') as f:
        f.write(vault_lib.encrypt(data))
        logger.info('{} encrypted'.format(file_path))

@manager.command
def decrypt_dump():
    'Decrypt and Dump secrets.yml'
    file_path = os.path.join('config', 'secrets.yml')
    data = decrypt()
    with open(file_path, 'w') as f:
        f.write(yaml.dump(data, default_flow_style=False))
    logger.info('Decrypted and dumped in {}'.format(file_path))

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
