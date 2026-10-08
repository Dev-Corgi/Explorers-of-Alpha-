; Power stars scale: 1★ per 20 BP, ½★ per 10 BP
; Replaces vanilla SetStringPower (threshold table → linear).
; Half star uses the same [M:R1] tag as IQ / monster-summary (not markfont B128).

.nds
.arm

.open "arm9.bin", 0x02000000

.definelabel SetStringPower,           0x02024428
.definelabel GetMoveBasePowerFromId,   0x02013BE8
.definelabel StrCpyFromFile,           0x020258B8
.definelabel StrCat,                   0x020897AC
.definelabel MoveDescStartID,          0x000027A2
.definelabel MoveDescEndID,            0x000029D1
.definelabel NoDamageID,               0x000027A1
.definelabel NullString,               0x02099D50
.definelabel StarString,               0x02099D84
; Vanilla IQ / CreateMonsterSummary half-star tag "[M:R1]"
.definelabel HalfStarString,           0x020A3544

.org SetStringPower
.area 0xCC
    stmdb   sp!,{r3,r4,r5,r6,r7,lr}
    ldr     r2,=MoveDescStartID
    mov     r4,r0
    cmp     r1,r2
    bcc     empty_string
    ldr     r0,=MoveDescEndID
    cmp     r1,r0
    bcs     empty_string
    sub     r0,r1,r2
    bl      GetMoveBasePowerFromId
    cmp     r0,#0
    bne     has_power
    ldr     r1,=NoDamageID
    mov     r0,r4
    bl      StrCpyFromFile
    b       done

has_power:
    mov     r5,r0              ; remaining power for /10 loop
    mov     r7,#0
    strb    r7,[r4]            ; clear dest string
    mov     r6,#0              ; half_units = power // 10
div10:
    cmp     r5,#10
    blt     div10_done
    sub     r5,r5,#10
    add     r6,r6,#1
    b       div10
div10_done:
    movs    r5,r6,lsr #1       ; full stars
    and     r6,r6,#1           ; half flag
    ldr     r7,=StarString
full_loop:
    cmp     r5,#0
    beq     maybe_half
    mov     r0,r4
    mov     r1,r7
    bl      StrCat
    sub     r5,r5,#1
    b       full_loop
maybe_half:
    cmp     r6,#0
    beq     done
    mov     r0,r4
    ldr     r1,=HalfStarString
    bl      StrCat
done:
    mov     r0,r4
    ldmia   sp!,{r3,r4,r5,r6,r7,pc}
empty_string:
    ldr     r0,=NullString
    ldmia   sp!,{r3,r4,r5,r6,r7,pc}
    .pool
    .fill (SetStringPower+0xCC-.), 0x00
.endarea

.close
