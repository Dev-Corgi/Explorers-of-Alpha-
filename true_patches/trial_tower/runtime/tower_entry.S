#include "tower_runtime_generated.h"
.syntax unified
.arm
.text
.macro entry name
 .global \name
 .type \name,%function
\name:
.endm
#include "tower_hooks.S"
