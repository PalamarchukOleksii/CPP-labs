"""
```
python finalize_the_file.py --hash <crc32 of the file> --filepath <path to file>
```

"""

import argparse
from pathlib import Path

def xor_encdec(_text, _key):

    def _enc(text, key):
        key = str(hex(key))
        encrypted_text = ""
        for i in range(len(text)):
            encrypted_text += chr(ord(text[i]) ^ ord(key[i % len(key)]))
        return encrypted_text

    _text = _enc(_text, _key * 1)
    _text = _enc(_text, _key * 2)
    _text = _enc(_text, _key * 3)
    _text = _enc(_text, _key * 4)
    _text = _enc(_text, _key * 5)
    return _text

MSG = b'\x10X@B\x7fX\x07TG\x02FEFT\x12\x04\x01\rA\x11Fk\r\n\x11VF\x01BVY\x0b\x0fD\x0f@\nQ\x0b\x02\x13?>\x15\x13\n\x190W\x05BT\x0e\x0fP\x0eSG\rS\x0b\x05@F\r\x01OY[\x13\x1f\tUSB\x14PBXC\n\x1fX\x15T\tMGX\x188EMBA\x16W\x03WZXT^T\x03\x10YB\x0fSU\x17?\x06YTG^EWR\x10K[\x02M\x1c\x06STFF\n\x1a\x11ZQ\x17\x11VR\x03N=[@N\x1e'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--hash", type=int, required=True)
    args = parser.parse_args()
    hash = int(args.hash)
    o = xor_encdec(MSG.decode(), hash)
    filepath = Path(args.filepath)
    n = o.split('`')[1]
    assert len(n) < 20 and n.isascii(), "wrong hash"
    assert filepath.exists(), filepath
    filepath_new = filepath.parent / n
    filepath.rename(filepath_new)
    print(o)