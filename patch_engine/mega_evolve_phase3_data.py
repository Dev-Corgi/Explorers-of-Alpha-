"""Prepare ordinary species byte projections and assigned ability text.

The 16-bit runtime profiles remain authoritative. This does not create forms
or enable phase3; callers must pass the completed runtime phase explicitly.
"""
from __future__ import annotations
from .korean_codec import parse_str_file,build_str_file,decode_english


def prepare_data(rom, initial_strings=None):
    from skytemple_files.data.md.handler import MdHandler
    from true_patches.mega_evolve.phase3 import load
    from true_patches.mega_evolve.phase3_strings import load_strings
    data=load(); text=load_strings()
    md=MdHandler.deserialize(rom.getFileByName('BALANCE/monster.md'))
    effects={row['id']:row['legacy_effect_id'] for row in data['abilities']}
    edits=[]
    for species,pair in sorted(data['base_profiles'].items(),key=lambda item:int(item[0])):
        index=int(species);entry=md.entries[index]
        before=[entry.ability_primary,entry.ability_secondary]
        after=[effects[identity] for identity in pair]
        if any(not 0<=identity<255 for identity in after):
            raise ValueError('phase3 invalid byte projection')
        entry.ability_primary,entry.ability_secondary=after
        edits.append({'species':index,'before':before,'after':after,'profile':pair})
    strings=list(initial_strings) if initial_strings is not None else parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    # Validate every new index before producing either modified file.
    for row in text['entries']:
        index=row['index']
        previous=decode_english(strings[index]) if index<len(strings) else ''
        if row['new'] and previous.strip() not in ('','[M:D1]'):
            raise RuntimeError(f'mega_evolve ability string index {index} is occupied')
    for row in text['entries']:
        index=row['index']
        if index>=len(strings):strings.extend([b'']*(index+1-len(strings)))
        strings[index]=row['en'].encode('cp1252')
    return {'BALANCE/monster.md':bytes(MdHandler.serialize(md)),
            'MESSAGE/text_e.str':build_str_file(strings)},edits


def installed_translations(text):
    """Require the complete extended-name block and exact per-entry English.

    Legacy names may already equal these names on a phase2 ROM. The new block
    identifies an installed phase3 table and prevents accidental retranslation.
    """
    from true_patches.mega_evolve.phase3_strings import load_strings
    entries=load_strings()['entries']
    if not all(row['index']<len(text) and text[row['index']]==row['en']
               for row in entries if row['new']):return {}
    result={str(row['index']):{'en':row['en'],'ko':row['ko']}
            for row in entries if row['index']<len(text) and text[row['index']]==row['en']}
    from true_patches.mega_evolve.new_species import load
    for row in load():
        if row['name_index']<len(text) and text[row['name_index']]==row['en']:
            result[str(row['name_index'])]={'en':row['en'],'ko':row['ko']}
    from true_patches.mega_evolve.phase6 import load as phase6
    for row in phase6()['strings']:
        if row['index']<len(text) and text[row['index']]==row['en']:
            result[str(row['index'])]={'en':row['en'],'ko':row['ko']}
    return result
