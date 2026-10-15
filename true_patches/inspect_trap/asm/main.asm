.nds
.arm
.include "offsetsUS.asm"
.include "generated.inc"

.open "overlay_0029.bin", ov_29
.org InspectTrapBeginSite
    bl InspectTrap_Begin
.org InspectTrapGridTileSite
    bl InspectTrap_GridTile
.org InspectTrapEndSite
    bl InspectTrap_End
.close

.open "overlay_0036.bin", ov_36
.org ov_36 + InspectTrapCodeAddress
.area 1024, 0
.align 4
InspectTrap_State:
    .fill 16, 0

; Only the Y input renderer calls this wrapper; the location-selection grid
; calls DrawTileGrid directly and must never enable inspection.
; r0=actor position, r1=direction, r2=0, r3=grid mode.
InspectTrap_Begin:
    push {r0-r4, lr}
    bl InspectTrap_Restore
    ldrsh r1, [r0, #2]
    ldrsh r0, [r0]
    bl GetTile
    ldrb r1, [r0, #7]
    cmp r1, #0xff
    beq InspectTrap_BeginDone
    ldr r4, =InspectTrap_State
    strb r1, [r4, #1]
    ldrb r0, [r4]
    cmp r0, #0
    bne InspectTrap_BeginDone
    ; Save the complete main-screen blend configuration. The native engine
    ; uploads this shadow state each frame; writing BLDCNT directly is transient.
    ldr r0, =MainBlendState
    add r1, r4, #4
    mov r2, #10
InspectTrap_SaveBlend:
    ldrb r3, [r0], #1
    strb r3, [r1], #1
    subs r2, r2, #1
    bne InspectTrap_SaveBlend
    ldr r0, =MainBlendState
    mov r1, #1
    strb r1, [r4]
    strb r1, [r0, #2]       ; BG2 (grid): first blend target
    mov r1, #2
    strb r1, [r0, #3]       ; BG3 (floor): second blend target
    mov r1, #0x40           ; engine coefficients are in eighths: 8/16 each
    strh r1, [r0, #6]
    strh r1, [r0, #8]
InspectTrap_BeginDone:
    pop {r0-r4, lr}
    b DrawTileGrid

; Replaces ldrh r2,[r10],#6 inside DrawTileGrid's subtile loop.
; r5=dungeon, r6/r7=tile x/y, r8=subtile x, stack[0x1c]=subtile y.
; Preserve the vanilla grid pointer advance even when returning a preview tile.
InspectTrap_GridTile:
    ldrh r2, [r10], #6
    push {r0-r4, r9, r11, r12, lr}
    sub sp, sp, #4
    ldr r9, =InspectTrap_State
    ldrb r0, [r9]
    cmp r0, #0
    beq InspectTrap_TileDone
    mov r0, r6
    mov r1, r7
    bl GetTile
    ldrb r1, [r0, #7]
    ldrb r3, [r9, #1]
    cmp r1, r3
    bne InspectTrap_TileDone
    ldr r0, [r0, #0x10]     ; tile.object, never tile.monster
    cmp r0, #0
    beq InspectTrap_TileDone
    ldr r1, [r0]
    cmp r1, #2             ; ENTITY_TRAP, excludes items / hidden stairs
    bne InspectTrap_TileDone
    ldrb r1, [r0, #0x20]   ; entity.is_visible
    cmp r1, #0
    bne InspectTrap_TileDone
    ldr r0, [r0, #0xb4]
    cmp r0, #0
    beq InspectTrap_TileDone
    ldrb r0, [r0]          ; trap_id; native trap graphics contain 25 entries
    cmp r0, #25
    bhs InspectTrap_TileDone
    ; Nine 8x8 tiles per trap, in row-major order. Trap tilemap lives at
    ; dungeon+0x11ec8 (native tile selector uses dungeon+0x40c4+0xde04).
    add r0, r0, r0, lsl #3
    ldr r1, [sp, #0x44]    ; original stack[0x1c], plus our 40-byte frame
    add r1, r1, r1, lsl #1
    add r1, r1, r8
    add r9, r0, r1
    ldr r1, =0x11ec8
    add r0, r5, r1
    add r0, r0, r9, lsl #1
    ldrh r11, [r0]
    ; BG2 and BG3 use different character banks. Copy just this trap subtile
    ; into unused BG2 characters 0x310..0x3f0; retain palette and flip bits.
    ; Native BG2 graphics end at 0x6060 (0x5e20 + 0x240); our range is
    ; 0x6200..0x7e20, below the BG3 character bank at 0x06018000.
    mov r0, r11, lsl #22
    mov r0, r0, lsr #22
    ldr r1, =FloorCharacters
    add r0, r1, r0, lsl #5
    add r9, r9, #0x300
    add r9, r9, #0x10
    ldr r1, =GridCharacters
    add r1, r1, r9, lsl #5
    mov r3, #8
InspectTrap_CopyCharacter:
    ldr r4, [r0], #4
    str r4, [r1], #4
    subs r3, r3, #1
    bne InspectTrap_CopyCharacter
    mov r2, r11, lsr #10
    mov r2, r2, lsl #10
    orr r2, r2, r9
    str r2, [sp, #12]      ; replace saved r2; fallback returns the native grid
InspectTrap_TileDone:
    add sp, sp, #4
    pop {r0-r4, r9, r11, r12, pc}

; HideTileGrid has already cleared the entire BG2 tilemap before this hook.
; Replays strb r1,[r0,#0x251], then restores the original blend state once.
InspectTrap_End:
    strb r1, [r0, #0x251]
InspectTrap_Restore:
    push {r0-r4, lr}
    ldr r4, =InspectTrap_State
    ldrb r0, [r4]
    cmp r0, #0
    beq InspectTrap_EndDone
    mov r0, #0
    strb r0, [r4]
    add r0, r4, #4
    ldr r1, =MainBlendState
    mov r2, #10
InspectTrap_RestoreBlend:
    ldrb r3, [r0], #1
    strb r3, [r1], #1
    subs r2, r2, #1
    bne InspectTrap_RestoreBlend
InspectTrap_EndDone:
    pop {r0-r4, pc}
    .pool
.endarea
.close
