"""Offline proof that signing changed only PE signature metadata, never code/data.

Authenticode trust/timestamps are verified separately with Windows SignTool.
"""
import argparse, struct
from pathlib import Path


def pe_fields(data):
    def u16(at): return struct.unpack_from('<H', data, at)[0]
    def u32(at): return struct.unpack_from('<I', data, at)[0]
    try:
        if data[:2] != b'MZ': raise ValueError('Missing DOS header')
        pe = u32(0x3c)
        if pe < 0x40 or data[pe:pe+4] != b'PE\0\0': raise ValueError('Missing PE header')
        opt = pe + 24
        size = u16(pe + 20)
        magic = u16(opt)
        directories, count = (96, 92) if magic == 0x10b else (112, 108) if magic == 0x20b else (0, 0)
        if not directories or size < directories + 40 or opt + size > len(data) or u32(opt+count) < 5:
            raise ValueError('Missing PE security directory')
        security = opt + directories + 32
        return opt + 64, security, u32(security), u32(security+4)
    except struct.error as exc:
        raise ValueError('Truncated PE headers') from exc


def signing_only(original, signed):
    checksum, security, old_offset, old_size = pe_fields(original)
    new_checksum, new_security, offset, size = pe_fields(signed)
    if (checksum, security) != (new_checksum, new_security) or old_offset or old_size:
        raise ValueError('Only originally unsigned PE files may receive a signature')
    aligned = (len(original) + 7) & ~7
    if offset != aligned or size < 8 or size % 8 or offset + size != len(signed):
        raise ValueError('Certificate table must be appended at the aligned original EOF')
    if signed[len(original):offset] != bytes(offset-len(original)):
        raise ValueError('Nonzero alignment padding')
    position = offset
    while position < len(signed):
        length, revision, kind = struct.unpack_from('<IHH', signed, position)
        if length < 8 or revision != 0x200 or kind != 2 or position+length > len(signed):
            raise ValueError('Invalid WIN_CERTIFICATE')
        end = position + ((length+7) & ~7)
        if end > len(signed) or any(signed[position+length:end]):
            raise ValueError('Invalid certificate padding')
        position = end
    before, after = bytearray(original), bytearray(signed[:len(original)])
    for at, length in ((checksum, 4), (security, 8)):
        before[at:at+length] = bytes(length)
        after[at:at+length] = bytes(length)
    if before != after: raise ValueError('PE code/data changed beyond signing metadata')


def package_files(root):
    if not root.is_dir():
        raise ValueError('Package directory missing or not a directory: '+str(root))
    files = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    if not files:
        raise ValueError('Package directory is empty: '+str(root))
    return files


def compare(source, target):
    a, b = package_files(source), package_files(target)
    if a.keys() != b.keys(): raise ValueError('Package file list changed')
    changes = []
    for relative, path in a.items():
        original, signed = path.read_bytes(), b[relative].read_bytes()
        if original != signed:
            if path.suffix.lower() not in ('.exe', '.dll', '.pyd'): raise ValueError('Non-PE file changed: '+relative)
            signing_only(original, signed)
            changes.append(relative)
    return changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    args = parser.parse_args()
    try:
        changes = compare(args.source, args.target)
    except (ValueError, OSError) as exc:
        parser.exit(1, 'Signing comparison failed: '+str(exc)+'\n')
    print('Signing-only package comparison passed: '+str(len(changes))+' PE files; all other bytes unchanged.')
