/* Phase 1: numeric Speed ranks and weather family/strength services.
 * No persistent species/ability assignments are changed here.
 */
#include "generated.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed short s16;
#define FN(a,t) ((t)(a))
#define U16(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define U32(p,o) (*(u32 *)((u8 *)(p)+(o)))
#ifdef ME_PHASE3
#include "phase3_generated.h"
const BaseProfile *ME_FindProfile(int);
int ME_AbilityActive(u8*,int);
int ME_SpeedBonus(u8*);
void ME_FlushFaintCopies(u32);
void ME_CancelFaintCopies(u8*);
int ME_ChangeStat(u8*,u8*,int,int);
int ME_MegaSolActive(u8*);
#endif
#define BYTE(p,o) (*((u8 *)(p)+(o)))
#ifdef ME_PHASE4
#include "phase4_generated.h"
const MEForm *ME_FindForm(int);
static void ME_QuickActor(u8*);
void ME_QuickReady(void);
#endif
enum { COUNT=20, SOURCES=60, SNAPSHOT=1024, MAGIC=0x3147454d,
#ifdef ME_PHASE2
 SCHEMA=2
#else
 SCHEMA=1
#endif
 };
typedef struct { u32 entity, monster; u8 rank, pad[3]; } Rank;
typedef struct { u32 entity, monster, order; u16 ability; u8 weather, strong;
#ifdef ME_PHASE2
 u8 grade,pad[3];
#endif
 } Source;
typedef struct { u32 magic, dungeon, floor, order; Rank ranks[COUNT]; Source sources[SOURCES]; } State;
static State state;
int ME_ForcedWeather(void);
int ME_WeatherStrength(u8*);
static u8 *dungeon(void) { return *(u8 **)DUNGEON_PTR; }
static void zero(void *p,u32 n) { u8 *b=p; while(n--) *b++=0; }
static int clamp(int x,int lo,int hi) { return x<lo?lo:x>hi?hi:x; }
static int divide(int a,int b) { return FN(SIGNED_DIVIDE,int (*)(int,int))(a,b); }
#ifdef ME_PHASE4
#include "phase4.c"
#endif
static u8 *monster(u8 *e) { return e && U32(e,0)==1 ? (u8 *)U32(e,0xb4) : 0; }
static int alive(u8 *e) { u8 *m=monster(e); return m && (s16)U16(m,0x10)>0; }
static int has(u8 *e,int ability) {
#ifdef ME_PHASE3
    return ME_AbilityActive(e,ability);
#else
    return FN(ABILITY_ACTIVE,int (*)(u8*,int))(e,ability);
#endif
}
static u8 *entity(int i) { u8 *d=dungeon(); return d?(u8 *)U32(d,0x12b78+i*4):0; }
static int slot(u8 *e) { for(int i=0;i<COUNT;i++) if(e && entity(i)==e) return i; return -1; }
#ifdef ME_PHASE5
#include "phase5.c"
#endif
#ifdef ME_PHASE2
#include "phase2.c"
#endif
static void ensure(void) {
    u8 *d=dungeon();
    u32 floor=d?U16(d,0x748):0;
    if(state.magic!=MAGIC || state.dungeon!=(u32)d || state.floor!=floor) {
        if(state.magic==MAGIC) {
            int owned=0; for(int i=0;i<SOURCES;i++) if(state.sources[i].entity) owned=1;
            if(owned) *(u8*)LEGACY_STRONG_WEATHER=0;
        }
 #ifdef ME_PHASE2
        reset_abilities();
#endif
        zero(&state,sizeof(state)); state.magic=MAGIC; state.dungeon=(u32)d; state.floor=floor;
        for(int i=0;i<COUNT;i++) state.ranks[i].rank=10;
    }
}
static Rank *rank(u8 *e) {
    ensure(); int i=slot(e); u8 *m=monster(e);
    if(i<0 || !m) return 0;
    Rank *r=&state.ranks[i];
    if(r->entity!=(u32)e || r->monster!=(u32)m) {
        r->entity=(u32)e; r->monster=(u32)m; r->rank=10;
    }
    return r;
}
int ME_GetStoredSpeed(u8 *e) { Rank *r=rank(e); return r?clamp(r->rank,4,16):10; }
int ME_SetStoredSpeed(u8 *e,int value) {
    Rank *r=rank(e); if(!r) return 0; int old=r->rank;
    r->rank=(u8)clamp(value,4,16); return old!=r->rank;
}
/* flags: 1 block opponent drops, 2 block self drops, 4 Simple, 8 enhanced Simple. */
int ME_ChangeSpeed(u8 *actor,u8 *target,int delta,int flags) {
    if(!alive(target)) return 0;
#ifdef ME_PHASE2
    if(ME_AbilityGrade(target,15)==1) flags|=3;
    if(ME_AbilityGrade(target,97)==1) flags|=8;
#endif
    if(delta<0 && ((actor!=target && ((flags&1)||has(target,15))) || (actor==target && (flags&2)))) return 0;
    if((flags&8) ? delta>0 : ((flags&4)||has(target,97))) delta*=2;
    return ME_SetStoredSpeed(target,ME_GetStoredSpeed(target)+delta);
}
void ME_ResetMonster(u8 *m) {
    ensure();
#ifdef ME_PHASE3
    ME_CancelFaintCopies(m);
#endif
#ifdef ME_PHASE2
#ifdef ME_PHASE3
    if(ability_memory)
#endif
    for(int i=0;i<COUNT;i++) if(banks[i].monster==(u32)m) zero(&banks[i],sizeof(AbilityBank));
#endif
    for(int i=0;i<COUNT;i++) if(state.ranks[i].monster==(u32)m) {
        state.ranks[i].rank=10; state.ranks[i].entity=0; state.ranks[i].monster=0;
    }
    for(int i=0;i<SOURCES;i++) if(state.sources[i].monster==(u32)m) zero(&state.sources[i],sizeof(Source));
}
int ME_ResetSpeed(u8 *e) { return ME_SetStoredSpeed(e,10); }
int ME_GetSpeed(u8 *e,int base,u8 *opponent,int bonus) {
    int stage=ME_GetStoredSpeed(e);
#ifdef ME_PHASE3
    bonus+=ME_SpeedBonus(e);
#endif
    /* Preserve balance_change's numeric Gale Wings effect, removing its accidental
     * movement-speed application at the legacy hook site. */
    u8 *m=monster(e);
    if(m && has(e,142) && (s16)U16(m,0x10)>=clamp((s16)U16(m,0x12)+(s16)U16(m,0x16),1,32767)) bonus+=2;
    if(opponent && has(opponent,103)) stage=10,bonus=0;
    int delta=clamp(stage+bonus,4,16)-10;
    int value=delta>=0?divide(base*(2+delta),2):divide(base*2,2-delta);
    return clamp(value,1,32767);
}
static int family(int weather) { return weather==7?5:weather; }
extern int ME_OriginalApparentWeather(u8 *);
int ME_ApparentWeather(u8 *e) { return family(ME_OriginalApparentWeather(e)); }
static int valid_source(Source *s) {
    u8 *e=(u8 *)s->entity;
    return s->strong && slot(e)>=0 && alive(e) && (u32)monster(e)==s->monster &&
        (!s->ability || has(e,s->ability))
#ifdef ME_PHASE2
        && (!s->grade || ME_AbilityGrade(e,s->ability)==s->grade-1)
#endif
        ;
}
static Source *source(u8 *e,int ability) {
    Source *empty=0;
    for(int i=0;i<SOURCES;i++) {
        Source *s=&state.sources[i];
        if(s->entity==(u32)e && s->monster==(u32)monster(e) && s->ability==ability) return s;
        if(!empty && (!s->entity || slot((u8*)s->entity)<0 || monster((u8*)s->entity)!=(u8*)s->monster)) empty=s;
    }
    return empty;
}
/* Weather-setting ability services register sources; no grade/assignments here. */
int ME_SetWeatherSource(u8 *e,int weather,int strong,int ability) {
    ensure(); int i=slot(e); if(i<0 || !alive(e)) return 0;
    #ifdef ME_PHASE2
    if(!known(ability) || (ability && ME_AbilityGrade(e,ability)<0)) return 0;
#else
    if(ability<0 || ability>254) return 0;
#endif
    weather=family(weather);
    if(weather!=0 && weather!=1 && weather!=2 && weather!=4 && weather!=5) return 0;
    if(!strong && ME_ForcedWeather()>=0) return 0;
    /* Native selector's force flag replays the weather visual.  Refresh the
     * source/timer without replaying it when the visible family and strength
     * already match; a new strong source still gets its first announcement. */
    int prior_weather=ME_ApparentWeather(e);
    int prior_strong=ME_WeatherStrength(e);
    int replay=prior_weather!=weather || prior_strong!=!!strong;
    Source *s=source(e,ability); if(!s) return 0;
    s->entity=(u32)e; s->monster=(u32)monster(e);
    s->ability=(u16)ability; s->weather=(u8)weather; s->strong=(u8)!!strong;
    s->order=++state.order;
#ifdef ME_PHASE2
    s->grade=ability?(u8)(ME_AbilityGrade(e,ability)+1):0;
#endif
    u8 *d=dungeon(); if(d) {
        U16(d,0xcd3a+weather*2)=(u16)(strong?1:3000); BYTE(d,0xe)=1;
        FN(0x023354c4,int (*)(int,int))(0,replay);
#ifdef ME_PHASE3
        if(strong&&replay&&ME_ApparentWeather(e)==weather&&ME_WeatherStrength(e)) {
            int message=ability==A_DESOLATE_LAND?19754:
                        ability==A_PRIMORDIAL_SEA?19755:
                        ability==A_DELTA_STREAM?19756:0;
            if(ability==A_DELTA_STREAM) {
                /* Tailwind's existing screen-wide wind animation, not a new
                 * effect file.  Play it only after the strong source wins. */
                int token=FN(0x022bdeb4,int(*)(int))(471);
                FN(0x022e35e4,int(*)(u8*,int,int,int,int,int,int,int))(
                    e,471,1,token&255,2,0,-1,0);
            }
            if(message)FN(0x0234b2a4,void(*)(u8*,int))(e,message);
        }
#endif
    }
    return 1;
}
void ME_ClearWeatherSource(u8 *e) {
    ensure(); for(int i=0;i<SOURCES;i++) if(state.sources[i].entity==(u32)e) zero(&state.sources[i],sizeof(Source));
    if(dungeon()) FN(0x023354c4,int (*)(int,int))(0,1);
}
static void native_sources(void) {
    for(int i=0;i<COUNT;i++) {
        u8 *e=entity(i); if(!alive(e)) continue;
        for(int a=252;a<=254;a++) {
            if(!has(e,a)) continue;
            Source *s=source(e,a); if(!s) continue;
            if(s->entity==(u32)e && s->monster==(u32)monster(e) && s->ability==a
#ifdef ME_PHASE2
                && s->grade==ME_AbilityGrade(e,a)+1
#endif
                ) continue;
            s->entity=(u32)e; s->monster=(u32)monster(e); s->ability=(u16)a;
     #ifdef ME_PHASE2
            s->grade=(u8)(ME_AbilityGrade(e,a)+1);
#endif
            s->weather=(u8)(a==252?4:a==253?1:0); s->strong=1; s->order=++state.order;
        }
    }
}
int ME_ForcedWeather(void) {
    ensure(); native_sources(); Source *best=0;
    for(int i=0;i<SOURCES;i++) if(valid_source(&state.sources[i]) && (!best || state.sources[i].order>best->order)) best=&state.sources[i];
    /* Alpha flag 1=heavy rain, 2=harsh sun, 3=wind; 4/5 extend it to sand/snow.
     * The original fire/water immunity paths continue to recognize only 1/2. */
    u8 legacy=*(u8 *)LEGACY_STRONG_WEATHER;
    if(best) {
        *(u8 *)LEGACY_STRONG_WEATHER=(u8)(best->weather==4?1:best->weather==1?2:best->weather==2?4:best->weather==5?5:3);
        return best->weather;
    }
    int any=0; for(int i=0;i<SOURCES;i++) if(state.sources[i].entity) any=1;
    if(any || legacy>=4) *(u8 *)LEGACY_STRONG_WEATHER=0;
    else if(legacy) return legacy==1?4:legacy==2?1:0; /* pre-existing story weather */
    return -1;
}
int ME_WeatherStrength(u8 *e) {
    int forced=ME_ForcedWeather();
    return forced>=0 && ME_ApparentWeather(e)==forced ? 1:0;
}
int ME_WeatherDefense(u8 *m,int value,int defense) {
    if(!defense) return value;
    u8 *e=0; for(int i=0;i<COUNT;i++) if(monster(entity(i))==m) { e=entity(i); break; }
    if(!e) return value;
    int weather=ME_ApparentWeather(e); int a=BYTE(m,0x5e),b=BYTE(m,0x5f);
    int supported=weather==2?(a==9||a==13||a==17||b==9||b==13||b==17):weather==5?(a==6||b==6):0;
    if(!supported) return value;
    return clamp(ME_WeatherStrength(e)?divide(value*3,2):divide(value*6,5),0,32767);
}
/* fx64 multiplier load used only for the matching sun/fire or rain/water boost. */
u32 *ME_WeatherPower(u8 *e) {
    /* Round 6/5 upward at the last fractional bit: floor(integer*6/5)
     * must not lose one point when that integer is divisible by five. */
    static const u32 ordinary[2]={0x33333334,0x13333},strong[2]={0,0x18000};
#ifdef ME_PHASE3
    if(ME_MegaSolActive(e))return (u32 *)ordinary;
#endif
    return (u32 *)(ME_WeatherStrength(e)?strong:ordinary);
}
extern int ME_OriginalWeatherMessage(int);
int ME_WeatherMessage(int weather) {
    int strong=*(u8*)LEGACY_STRONG_WEATHER;
    if(strong==4) return 19751-0xa00;
    if(strong==5) return 19752-0xa00;
    return ME_OriginalWeatherMessage(weather);
}
int ME_WeatherFailure(void) {
    int strong=*(u8*)LEGACY_STRONG_WEATHER;
    return strong>=4?19753:0xa45+strong;
}
/* Versioned component codec for the later persistent/quick-save integration.
 * Uses roster slots/species, never persists raw entity pointers. */
static u32 checksum(u8 *p) {
    u32 value=2166136261u;
    for(int i=0;i<SNAPSHOT;i++) if(i<12 || i>=16) value=(value^p[i])*16777619u;
    return value;
}
int ME_ExportState(u8 *out,int size) {
    if(size<SNAPSHOT) return 0;
    ensure(); zero(out,SNAPSHOT);
    U32(out,0)=MAGIC; U16(out,4)=SCHEMA; U16(out,6)=SNAPSHOT; U32(out,8)=state.floor;
    for(int i=0;i<COUNT;i++) {
        u8 *e=entity(i),*m=monster(e); if(!m) continue;
        u8 *p=out+16+i*4; U16(p,0)=U16(m,2); BYTE(p,2)=(u8)ME_GetStoredSpeed(e); BYTE(p,3)=1;
    }
    for(int i=0;i<SOURCES;i++) {
        Source *s=&state.sources[i]; int owner=slot((u8*)s->entity);
        if(owner<0 || !alive((u8*)s->entity) || (u32)monster((u8*)s->entity)!=s->monster) continue;
        u8 *p=out+96+i*12; BYTE(p,0)=(u8)owner; BYTE(p,1)=1; U16(p,2)=s->ability;
        BYTE(p,4)=s->weather; BYTE(p,5)=s->strong;
#ifdef ME_PHASE2
        BYTE(p,6)=s->grade;
#endif
        U32(p,8)=s->order;
    }
    U32(out,12)=checksum(out);
    return SNAPSHOT;
}
int ME_ImportState(u8 *in,int size) {
    if(size!=SNAPSHOT || U32(in,0)!=MAGIC || (U16(in,4)!=SCHEMA
#ifdef ME_PHASE2
       && U16(in,4)!=1
#endif
       ) || U16(in,6)!=SNAPSHOT || U32(in,12)!=checksum(in)) return 0;
    ensure(); if(U32(in,8)!=state.floor) return 0;
    /* Validate the whole payload before mutating any live state. */
    for(int i=0;i<COUNT;i++) if(BYTE(in,16+i*4+3) && (BYTE(in,16+i*4+2)<4 || BYTE(in,16+i*4+2)>16)) return 0;
    for(int i=0;i<SOURCES;i++) {
        u8 *p=in+96+i*12; int w=BYTE(p,4);
        if(BYTE(p,1) && (BYTE(p,0)>=COUNT || (U16(p,2)>254
#ifdef ME_PHASE2
            && !known(U16(p,2))
#endif
             )
#ifdef ME_PHASE2
            || BYTE(p,6)>2
#endif
            || BYTE(p,5)>1 || (w!=0&&w!=1&&w!=2&&w!=4&&w!=5))) return 0;
    }
    zero(state.sources,sizeof(state.sources)); state.order=0;
    for(int i=0;i<COUNT;i++) {
        u8 *e=entity(i),*m=monster(e),*p=in+16+i*4;
        if(!m || !BYTE(p,3) || U16(p,0)!=U16(m,2)) continue;
        Rank *r=rank(e); r->rank=BYTE(p,2);
    }
    for(int i=0;i<SOURCES;i++) {
        u8 *p=in+96+i*12; if(!BYTE(p,1)) continue;
        int owner=BYTE(p,0); u8 *e=entity(owner),*m=monster(e);
        if(!m || U16(in,16+owner*4)!=U16(m,2)) continue;
        Source *s=&state.sources[i]; s->entity=(u32)e; s->monster=(u32)m;
 #ifdef ME_PHASE2
        s->grade=BYTE(p,6);
#endif
        s->ability=U16(p,2); s->weather=BYTE(p,4); s->strong=BYTE(p,5); s->order=U32(p,8);
        if(s->order>state.order) state.order=s->order;
    }
    return 1;
}

#ifdef ME_PHASE3
#include "phase3.c"
#ifdef ME_PHASE4
#include "phase4_quick.c"
#endif
#endif
