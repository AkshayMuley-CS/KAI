import json, hashlib, datetime

def log(config, data):
    path = config['CHAIN_FILE']
    chain = []
    if path.exists():
        chain = json.loads(path.read_text())
    
    prev = chain[-1]['hash'] if chain else "0"
    block = {
        "index": len(chain),
        "time": str(datetime.datetime.now()),
        "data": str(data),
        "prev": prev
    }
    block['hash'] = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
    chain.append(block)
    path.write_text(json.dumps(chain, indent=2))
    return "Logged to chain."

def view(config, args=None):
    path = config['CHAIN_FILE']
    return path.read_text() if path.exists() else "Empty chain."

def register(config):
    return {'chain_view': view, 'log': log}