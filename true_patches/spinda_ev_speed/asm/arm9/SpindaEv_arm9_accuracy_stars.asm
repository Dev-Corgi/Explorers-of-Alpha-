; Move-info Accuracy stars: 1 full star per 10 Accuracy, leftover → half star.
; Replaces vanilla SetStringAccuracy (threshold table / Always Hit at >=101).
; Reads SkyTemple Accuracy (waza +0x0B), the same byte MoveHitCheck uses.
; Accuracy 125 is 12 full + half. Always Hit is not used for a numeric value.

.org SetStringAccuracy
.area 0xC8
    stmdb   sp!,{r3,r4,r5,r6,r7,lr}
    ldr     r2,=MoveDescStartID
    mov     r4,r0
    cmp     r1,r2
    bcc     AccStars_Empty
    ldr     r0,=MoveDescEndID
    cmp     r1,r0
    bcs     AccStars_Empty
    sub     r0,r1,r2
    mov     r1,#0x0B
    mov     r2,#1
    bl      GetMoveField
    mov     r5,r0
    mov     r7,#0
    strb    r7,[r4]
    mov     r6,#0
AccStars_Div10:
    cmp     r5,#10
    blt     AccStars_Div10Done
    sub     r5,r5,#10
    add     r6,r6,#1
    b       AccStars_Div10
AccStars_Div10Done:
    mov     r7,r5
    ldr     r5,=StarString
AccStars_Full:
    cmp     r6,#0
    beq     AccStars_MaybeHalf
    mov     r0,r4
    mov     r1,r5
    bl      Strcat
    sub     r6,r6,#1
    b       AccStars_Full
AccStars_MaybeHalf:
    cmp     r7,#0
    beq     AccStars_Done
    mov     r0,r4
    ldr     r1,=HalfStarString
    bl      Strcat
AccStars_Done:
    mov     r0,r4
    ldmia   sp!,{r3,r4,r5,r6,r7,pc}
AccStars_Empty:
    ldr     r0,=NullString
    ldmia   sp!,{r3,r4,r5,r6,r7,pc}
    .pool
    .fill (SetStringAccuracy+0xC8-.), 0x00
.endarea
