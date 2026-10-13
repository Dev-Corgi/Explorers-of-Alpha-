/* Persistent bootstrap lives in ov36; the uncompressed payload owns a heap block.
 * Only ordinary battle code calls this loader (never IRQ handlers).
 */
#include "loader_generated.h"
typedef unsigned int u32;
typedef unsigned char u8;
typedef struct { u8 *ptr; u32 len; } File;
static File loaded;
static u8 *base;
static u32 busy;
volatile u32 ME_LoaderFault;
static void fatal(u32 reason) { ME_LoaderFault=reason; for(;;) __asm__ volatile("nop"); }
void ME_LoaderRelease(void) {
    u8 *p=loaded.ptr;
    base=0; loaded.ptr=0; loaded.len=0;
    if(p)((void(*)(void*))0x02001188)(p);
}
u32 ME_LoaderResolve(u32 offset) {
    if(!base) {
        u32 mode; __asm__ volatile("mrs %0,cpsr":"=r"(mode));
        if(busy || (mode&31)==18 || (mode&31)==17)fatal(1);
        busy=1;
        ((void(*)(File*,const char*,int))0x02008c3c)(&loaded,"/MEGA/runtime.bin",0);
        if(!loaded.ptr || loaded.len!=ME_FILE_SIZE || ((u32)loaded.ptr&3))fatal(2);
        u32 *h=(u32*)loaded.ptr;
        if(h[0]!=0x4d454752 || h[1]!=1 || h[2]!=ME_IMAGE_SIZE ||
           h[3]!=ME_IMAGE_OFFSET || h[4]!=ME_RELOC_COUNT || h[5]!=ME_FILE_SIZE ||
           h[6]!=ME_CHECKSUM || h[7]!=0)fatal(3);
        u32 checksum=2166136261u;
        for(u32 i=32;i<loaded.len;i++)checksum=(checksum^loaded.ptr[i])*16777619u;
        if(checksum!=ME_CHECKSUM)fatal(4);
        u8 *image=loaded.ptr+ME_IMAGE_OFFSET;
        u32 *relocs=h+8;
        for(u32 i=0;i<ME_RELOC_COUNT;i++) {
            u32 r=relocs[i*2];
            if((r&3) || r>ME_IMAGE_SIZE-4)fatal(5);
            u32 *p=(u32*)(image+r), value=*p;
            if(value!=relocs[i*2+1])fatal(6);
            *p=value-ME_LINK_BASE+(u32)image;
        }
        /* Clean modified data, drain write buffer, invalidate instruction cache.
         * The image allocation may have reused RAM containing old instructions.
         */
        u32 end=(u32)image+ME_IMAGE_SIZE, zero=0;
        for(u32 p=(u32)image&~31u;p<end;p+=32)
            __asm__ volatile("mcr p15,0,%0,c7,c10,1"::"r"(p):"memory");
        __asm__ volatile("mcr p15,0,%0,c7,c10,4\n mcr p15,0,%0,c7,c5,0\n mcr p15,0,%0,c7,c5,4"::"r"(zero):"memory");
        base=image; busy=0;
    }
    if(offset>=ME_IMAGE_SIZE || (offset&3))fatal(7);
    return (u32)base+offset;
}
