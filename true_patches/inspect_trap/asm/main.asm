.nds
.arm
.include "offsetsUS.asm"
.include "generated.inc"

.open "overlay_0029.bin", ov_29
.org InspectTrapRSite
    bl InspectTrap_RAction
; ApplyTrapEffect has run. Force the caller's native removal decision true.
; Failed/avoided activation paths never reach this instruction.
.org InspectTrapConsumeSite
    mov r4, #1
.close

.open "overlay_0036.bin", ov_36
.org ov_36 + InspectTrapCodeAddress
; Keep the reservation size so following modules need not move.
.area 1024, 0

; R input action. r6 is the controlled actor at the original input site.
; The original R diagonal-mode toggle is intentionally skipped by the wrapper.
InspectTrap_RAction:
    push {r0-r5, r7-r12, lr}
    ldr r0, =ReadDungeonButtons
    ldrh r0, [r0]
    tst r0, #0x100
    beq InspectTrap_RDone
    ldr r0, =InspectTrapInputState
    ldrb r0, [r0, #2]
    cmp r0, #0
    bne InspectTrap_RDone
    add r0, r6, #4
    bl InspectTrap_Begin
    ; Sound-table entry 0x0B is the warp cue used by the game.
    mov r0, #0x0B
    bl PlayDungeonSound
    ; The normal no-input action writes 1 to MonsterInfo+0x4E. Do the same
    ; here so the engine advances exactly one turn after the R action.
    ldr r0, [r6, #0xB4]
    mov r1, #1
    strb r1, [r0, #0x4E]
InspectTrap_RDone:
    pop {r0-r5, r7-r12, lr}
    b 0x022F1ECC

; r0 points to the controlled actor's position (x/y halfwords).
InspectTrap_Begin:
    push {r0-r12, lr}
    ldrsh r4, [r0]
    ldrsh r5, [r0, #2]
    mov r8, #0
    mvn r6, #0
InspectTrap_Row:
    mvn r7, #0
InspectTrap_Column:
    cmp r6, #0
    cmpeq r7, #0
    beq InspectTrap_Next
    add r0, r4, r7
    add r1, r5, r6
    ; Native reveal-one-tile changes only hidden traps' entity.is_visible.
    ; GetTile handles map edges safely. No room-number filtering.
    bl RevealTrapAt
    orr r8, r8, r0
InspectTrap_Next:
    add r7, r7, #1
    cmp r7, #1
    ble InspectTrap_Column
    add r6, r6, #1
    cmp r6, #1
    ble InspectTrap_Row
    cmp r8, #0
    beq InspectTrap_Draw
    bl UpdateMinimap
    bl UpdateTrapsVisibility
InspectTrap_Draw:
    pop {r0-r12, lr}
    bx lr
    .pool
.endarea
.close
