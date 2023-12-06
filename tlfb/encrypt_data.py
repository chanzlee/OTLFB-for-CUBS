import json
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from tlfb.settings import SECRET_KEY


def get_encrypted_session(session):
    session_data = {
        "markers": session["markers"],
        "subid": session["subid"],
        "timepoint": session["timepoint"],
        "pid": session["pid"],
        "offset": session["offset"],
        "cohort": session["cohort"],
        "study_cannabis": session["study_cannabis"],
        "days": session["days"],
        "prescription": session["prescription"],
        "study_removed": session["study_removed"],
    }
    encrypted_data = encrypt(json.dumps(session_data))
    return "-".join([str(byte) for byte in encrypted_data])


def get_decrypted_session(encrypted_data):
    encrypted_data = [int(byte) for byte in encrypted_data.split("-")]
    decrypted_string = decrypt(bytes(encrypted_data))
    return json.loads(decrypted_string)


def encrypt(message, key=SECRET_KEY):
    key = get_sha(key)
    message = message.encode()
    padded_message = pad(message)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(padded_message)


def decrypt(encrypted_text, key=SECRET_KEY):
    key = get_sha(key)
    iv = encrypted_text[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    original_text = cipher.decrypt(encrypted_text[AES.block_size:])
    return (original_text.rstrip(b"\0")).decode()


def pad(message):
    return message + b"\0" * (AES.block_size - len(message) % AES.block_size)


def get_sha(text):
    hasher = SHA256.new(text.encode("utf-8"))
    return hasher.digest()[:16]
