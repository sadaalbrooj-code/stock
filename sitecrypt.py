#!/usr/bin/env python3
"""Encryption helper for the static stock site.
data:       python3 sitecrypt.py data KEY_B64 data.json data.enc
adduser:    python3 sitecrypt.py adduser KEY_B64 users.json USERNAME PASSWORD
removeuser: python3 sitecrypt.py removeuser users.json USERNAME
newkey:     python3 sitecrypt.py newkey
data.enc = base64(iv[12] + AES-256-GCM(key, json bytes)).
users.json = {"<sha256(lower(username))>": {"s": salt_b64, "w": base64(iv + AES-GCM(PBKDF2-SHA256(password, salt, 310000), key))}}
"""
import sys, os, json, base64, hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ITER = 310000
b64 = lambda b: base64.b64encode(b).decode()
uid = lambda u: hashlib.sha256(u.strip().lower().encode()).hexdigest()
def enc(key, raw):
    iv = os.urandom(12); return iv + AESGCM(key).encrypt(iv, raw, None)
def main(a):
    if a[0] == 'newkey':
        print(b64(os.urandom(32))); return
    if a[0] == 'removeuser':
        u = json.load(open(a[1])); u.pop(uid(a[2]), None); json.dump(u, open(a[1], 'w'), indent=0); print('removed'); return
    key = base64.b64decode(a[1]); assert len(key) == 32
    if a[0] == 'data':
        raw = open(a[2], 'rb').read(); json.loads(raw)
        open(a[3], 'w').write(b64(enc(key, raw))); print('encrypted', len(raw), 'bytes')
    elif a[0] == 'adduser':
        users = json.load(open(a[2])) if os.path.exists(a[2]) else {}
        salt = os.urandom(16)
        kek = hashlib.pbkdf2_hmac('sha256', a[4].encode(), salt, ITER, 32)
        users[uid(a[3])] = {'s': b64(salt), 'w': b64(enc(kek, key))}
        json.dump(users, open(a[2], 'w'), indent=0); print('added', a[3])
main(sys.argv[1:])
