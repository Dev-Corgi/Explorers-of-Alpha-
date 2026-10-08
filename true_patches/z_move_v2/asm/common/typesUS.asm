; Game type_id values (struct type_id_8 / GetMoveTypeForMonster), not 0-based.
TYPE_NONE                     equ 0
TYPE_NORMAL                   equ 1
TYPE_FIRE                     equ 2
TYPE_WATER                    equ 3
TYPE_GRASS                    equ 4
TYPE_ELECTRIC                 equ 5
TYPE_ICE                      equ 6
TYPE_FIGHTING                 equ 7
TYPE_POISON                   equ 8
TYPE_GROUND                   equ 9
TYPE_FLYING                   equ 10
TYPE_PSYCHIC                  equ 11
TYPE_BUG                      equ 12
TYPE_ROCK                     equ 13
TYPE_GHOST                    equ 14
TYPE_DRAGON                   equ 15
TYPE_DARK                     equ 16
TYPE_STEEL                    equ 17
TYPE_FAIRY                    equ 18

; Debug: 0 = use selected move slot type; else force this game type_id.
ZMOVE_DEBUG_FORCE_TYPE        equ 0
