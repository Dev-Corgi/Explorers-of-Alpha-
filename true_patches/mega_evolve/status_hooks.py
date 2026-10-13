"""Ordinary status-entry ABI audit shared with enhanced-effect work.

All entries take actor/target in r0/r1. A tail continuation keeps additional
register/stack arguments untouched, including Burn's check-only stack flag.
Statuses 0..6: sleep/poison/bad poison/burn/paralysis/confusion/frostbite;
7: yawn; 8..11: infatuation/taunt/encore/sealed move.
"""
ENTRIES=(
    ('Sleep',0x023118d8,0xe92d40f8),
    ('Poison',0x02312664,0xe92d4ff8),
    ('BadPoison',0x0231293c,0xe92d4ff8),
    ('Burn',0x02312338,0xe92d4ff8),
    ('Paralysis',0x02314544,0xe92d4ff0),
    ('Confusion',0x02314f38,0xe92d40f8),
    ('Frostbite',0x02312bf8,0xe92d40f8),
    ('Yawn',0x02311e70,0xea000000),
    ('Infatuation',0x023121ac,0xe92d41f8),
    ('Taunt',0x023163a8,0xe92d4078),
    ('Encore',0x02316720,0xe92d40f8),
    ('Seal',0x02314abc,0xe92d43f0),
)


def assembly(defines):
    result=[]
    for status,(name,site,expected) in enumerate(ENTRIES):
        head=defines[f'STATUS_HEAD_{status}'];target=defines[f'STATUS_TARGET_{status}']
        prefix='' if head>>24==0xea else f' .word 0x{head:X}\n'
        result.append(f'''entry ME_Status{name}Hook
 push {{r0-r3,r12,lr}}
 mov r2,#{status}
 bl ME_StatusBlocked
 cmp r0,#0
 pop {{r0-r3,r12,lr}}
 movne r0,#0
 bxne lr
{prefix} ldr pc,=0x{target:X}
''')
    return '\n'.join(result)+'.ltorg\n'
