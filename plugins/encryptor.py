import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def get_key(config):
    return bytes.fromhex(config['ENCRYPTION_KEY'])

def load(config):
    try:
        with open(config['VAULT_FILE'], 'rb') as f:
            nonce, tag, text = [f.read(x) for x in (12, 16, -1)]
        cipher = AES.new(get_key(config), AES.MODE_GCM, nonce=nonce)
        return json.loads(cipher.decrypt_and_verify(text, tag))
    except: return {}

def save(config, data):
    cipher = AES.new(get_key(config), AES.MODE_GCM)
    text, tag = cipher.encrypt_and_digest(json.dumps(data).encode())
    with open(config['VAULT_FILE'], 'wb') as f:
        [f.write(x) for x in (cipher.nonce, tag, text)]

def write(config, args):
    try:
        title, body = args.split(' :: ', 1)
        data = load(config)
        data[title] = body
        save(config, data)
        return "Note saved encrypted."
    except: return "Usage: note Title :: Body"

def read(config, title):
    data = load(config)
    return data.get(title, "Not found.")

def list_notes(config, args=None):
    return ", ".join(load(config).keys()) or "Empty vault."

def register(config):
    return {'note': write, 'vault_read': read, 'vault_list': list_notes}