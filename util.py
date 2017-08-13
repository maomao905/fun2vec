import os
import json, yaml
from ansible.parsing import vault
from ansible.parsing.vault import VaultLib
import logging
from flask_script import Manager

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)


def read_secrets(key):
    return decrypt().get(key)

def decrypt():
    """
    Decrypt secrets.yml
    """
    file_path = 'secrets.yml'
    with open(file_path, 'rb') as f:
        data = f.read()
    vault_lib = VaultLib(os.environ['FUN2VEC_SECRET_PASSWORD'])
    if vault.is_encrypted(data):
        data = yaml.load(vault_lib.decrypt(data))
        if 'private_key' in data:
            data['private_key'] = data['private_key'].replace('\\n', '\n')
    else:
        data = yaml.load(data)
    return data

manager = Manager(usage='Perform util commands')
@manager.command
def encrypt():
    'Encrypt secrets.yml'
    file_path = 'secrets.yml'
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
    file_path = 'secrets.yml'
    data = decrypt()
    with open(file_path, 'w') as f:
        f.write(yaml.dump(data, default_flow_style=False))
    logger.info('Decrypted and dumped in {}'.format(file_path))
