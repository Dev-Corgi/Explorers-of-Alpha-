"""MFX1: extended fixed layouts/properties inside an ordinary SIR0 fixed.bin.

The pointer list remains native SIR0 data. Its terminator still ends the list;
an unreferenced content prefix preserves the properties for physical IDs256+.
This module is also bundled unchanged into the SkyTemple adapter wheel.
"""
import struct

from skytemple_files.common.types.file_types import FileType


def read_extension(blob):
    if bytes(blob[:4])!=b'SIR0' or bytes(blob[16:20])!=b'MFX1':return None
    if len(blob)<32:raise ValueError('Truncated MFX1 header')
    magic,version,first,count,alias,reserved=struct.unpack_from('<4sIHHHH',blob,16)
    if version!=1 or first!=256 or count!=8 or alias!=249 or reserved or len(blob)<32+count*12:
        raise ValueError('Unsupported MFX1 fixed-room extension')
    return dict(first=first,count=count,alias=alias,
                properties=[bytes(blob[32+i*12:44+i*12]) for i in range(count)])


def serialize_extended(model,extension):
    first,count,alias=(extension[k] for k in ('first','count','alias'))
    props=extension['properties']
    if (first,count,alias)!=(256,8,249) or len(model.fixed_floors)!=first+count or len(props)!=count or any(len(p)!=12 for p in props):
        raise ValueError('MFX1 room count or properties changed')
    prefix=struct.pack('<4sIHHHH',b'MFX1',1,first,count,alias,0)+b''.join(props)
    content,offsets,pointer=model.sir0_serialize_parts()
    content=bytearray(content)
    for offset in offsets:
        value=struct.unpack_from('<I',content,offset)[0]
        struct.pack_into('<I',content,offset,value+len(prefix))
    sir0=FileType.SIR0.wrap(prefix+content,[o+len(prefix) for o in offsets],pointer+len(prefix))
    return bytes(FileType.SIR0.serialize(sir0))
