.nds
.arm
.include "offsetsUS.asm"
.include "generated.inc"

.open "overlay_0029.bin", ov_29
.org InspectTrapBeginSite
    bl InspectTrap_Begin
; ApplyTrapEffect has run. Force the caller's native removal decision true.
; Failed/avoided activation paths never reach this instruction.
.org InspectTrapConsumeSite
    mov r4, #1
.close

.open "overlay_0036.bin", ov_36
.org ov_36 + InspectTrapCodeAddress
; Keep the reservation size so following modules need not move.
.area 1024, 0

; Y input renderer only; the position-selection grid calls DrawTileGrid directly.
; r0 points to the controlled actor's position.
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
    b DrawTileGrid
    .pool
.endarea
.close
