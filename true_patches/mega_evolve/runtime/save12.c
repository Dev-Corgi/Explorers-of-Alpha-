/* Versioned roster stream, retaining the EVS1 main block and doping tail.
 * Only the roster serializer uses 12-bit species. Other native streams keep
 * their existing width. Resident ARM9 code also works outside dungeons.
 */
#include "save12_generated.h"
typedef unsigned char u8;
typedef unsigned int u32;
enum { SIZE=0x7F6B, MARK=0x7F58, MAGIC=0x3231454D,
       OLD_BITS=202510, NEW_BITS=203069, MEMBERS=559 };
#define FN(a,t) ((t)(a))
typedef struct { u32 write_width,read_width,migration_pending,schema; } State;
#define state ((State *)SAVE12_STATE)
static u32 get(const u8 *p) {
    return p[0]|((u32)p[1]<<8)|((u32)p[2]<<16)|((u32)p[3]<<24);
}
static void put(u8 *p,u32 n) {
    for(int i=0;i<4;i++,n>>=8) p[i]=(u8)n;
}
void ME_Save12WriteSpecies(void *stream,const u8 *species,int ignored) {
    (void)ignored;
    FN(0x020509C0,void (*)(void *,const u8 *,int))
        (stream,species,state->write_width==12?12:11);
}
void ME_Save12ReadSpecies(void *stream,u8 *species,int ignored) {
    (void)ignored;
    FN(0x02050A40,void (*)(void *,u8 *,int))
        (stream,species,state->read_width==12?12:11);
}
int ME_Save12WriteRoster(u8 *buffer,u32 size) {
    u32 before=state->write_width;
    state->write_width=size==SIZE?12:11;
    int result=FN(SAVE12_WRITE_ROSTER,int (*)(u8 *,u32))(buffer,size);
    if(size==SIZE) {
        put(buffer+MARK,MAGIC); put(buffer+MARK+4,1);
        put(buffer+MARK+8,12); put(buffer+MARK+12,MEMBERS);
    }
    state->write_width=before;
    return result;
}
int ME_Save12ReadRoster(u8 *buffer,u32 size) {
    u32 width=11,before=state->read_width;
    if(size==SIZE && get(buffer+MARK)) {
        if(get(buffer+MARK)!=MAGIC) return -1;
        if(get(buffer+MARK+4)!=1 || get(buffer+MARK+8)!=12 ||
           get(buffer+MARK+12)!=MEMBERS) return -1;
        width=12;
    }
    state->read_width=width;
    int result=FN(SAVE12_READ_ROSTER,int (*)(u8 *,u32))(buffer,size);
    state->read_width=before;
    if(size==SIZE) {
        state->migration_pending=width==11;
        state->schema=width==12?1:0;
    }
    return result;
}
