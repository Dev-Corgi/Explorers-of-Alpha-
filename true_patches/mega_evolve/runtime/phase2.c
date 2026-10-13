/* Included by phase1.c: three identities and independent grades.
 * A profile is dungeon-local; persistent species profiles are supplied in phase4.
 */
#include "abilities_generated.h"
typedef struct { u32 entity,monster; u16 species; u8 seen[2],configured,pad[3]; u32 permanent[3],current[3]; } AbilityBank;
static u16 bank_species(u8 *m) {
#ifdef ME_PHASE3
    /* +2 is the original MD identity used by SetMonsterTypeAndAbility.
     * Native Illusion/Transform change +4, the apparent species. */
    return U16(m,2);
#else
    return U16(m,4);
#endif
}
typedef struct { u16 ability; u8 owner,event; u32 target; } Once;
typedef struct { u32 token,actor; u16 move; u8 used,pad; Once once[64];
#ifdef ME_PHASE3
    struct {u32 ability,entity,monster;u16 distance;u8 source_slot,own_slot;} copies[COUNT];
#endif
} Action;
#ifdef ME_PHASE3
typedef struct {AbilityBank bank[COUNT];Action action[4];u32 next;int level;} AbilityMemory;
static AbilityMemory *ability_memory;
#define banks (ability_memory->bank)
#define actions (ability_memory->action)
#define next_action (ability_memory->next)
#define depth (ability_memory->level)
#else
static AbilityBank banks[COUNT];
static Action actions[4];
static u32 next_action;
static int depth;
#endif
static void ensure(void);
static u8 project(u32);
static void reset_abilities(void) {
#ifdef ME_PHASE3
    if(!ability_memory) {
        ability_memory=FN(0x02001170,void*(*)(int,int))(sizeof(AbilityMemory),0);
        if(ability_memory)zero(ability_memory,sizeof(*ability_memory));
    }
    if(!ability_memory)return;
    /* A same-dungeon floor transition restores temporary native projections
     * before discarding banks. Otherwise non-target wild species would seed
     * their next floor from the swapped bytes and keep the borrowed trait. */
    if(state.magic==MAGIC&&state.dungeon==(u32)dungeon())for(int i=0;i<COUNT;i++) {
        AbilityBank *b=&banks[i];u8 *e=entity(i),*m=monster(e);
        if(m&&b->entity==(u32)e&&b->monster==(u32)m&&b->species==bank_species(m))
            for(int j=0;j<2;j++)BYTE(m,0x60+j)=project(b->permanent[j]);
    }
#endif
    zero(banks,sizeof(banks));zero(actions,sizeof(actions));depth=0;
}
static int known(int a) { return a>=0 && (a<=254 || (a>=256 && a<462)); }
static int canonical(int a) { return a>0 && a<255 ? ability_import[a] : a; }
static int effect(int a) { return a>=256 && a<462?ability_effect[a]:a; }
static int packed_valid(u32 a) { return !(a&0xfffe0000u) && known(a&65535) && (a&65535 || !a); }
static u8 project(u32 a) { int id=effect(a&65535); return id>0 && id<255?(u8)id:0; }
static void publish(AbilityBank *b) {
    u8 *m=(u8*)b->monster;
    for(int i=0;i<2;i++) BYTE(m,0x60+i)=b->seen[i]=project(b->current[i]);
    if(dungeon()) BYTE(dungeon(),0xe)=1;
}
static AbilityBank *bank(u8 *e) {
    ensure();
#ifdef ME_PHASE3
    if(!ability_memory)return 0;
#endif
    int i=slot(e); u8 *m=monster(e); if(i<0 || !m) return 0;
    AbilityBank *b=&banks[i];
    if(b->entity!=(u32)e || b->monster!=(u32)m || b->species!=bank_species(m)) {
        zero(b,sizeof(*b)); b->entity=(u32)e;b->monster=(u32)m;b->species=bank_species(m);
        for(int j=0;j<2;j++) {
            b->seen[j]=BYTE(m,0x60+j);b->current[j]=b->permanent[j]=(u32)canonical(b->seen[j]);
        }
#ifdef ME_PHASE3
        const BaseProfile *profile=ME_FindProfile(b->species);
        if(profile) {
            b->configured=1;
            for(int j=0;j<2;j++) b->current[j]=b->permanent[j]=profile->ability[j];
            publish(b);
        }
#endif
    } else {
        /* Native byte writes become temporary ordinary traits. They never change
         * the configured profile, form ID or original species. */
        for(int j=0;j<2;j++) if(b->seen[j]!=BYTE(m,0x60+j)) {
            b->seen[j]=BYTE(m,0x60+j);b->current[j]=(u32)canonical(b->seen[j]);
        }
    }
    return b;
}
static int permitted(u8 *e,int identity) {
    if(!monster(e)) return 0;
    if(FN(0x023467e4,int(*)(u8*,int))(e,39)) return 0;
    /* Existing Gastro Acid and bug_fixes adjacency Gas predicate. Gas calls the
     * shared query for ID160 and explicitly excludes Gas itself: no recursion. */
    return FN(0x02301cdc,int(*)(u8*,int))(e,effect(identity));
}
u32 ME_GetAbility(u8 *e,int index,int active_only) {
    AbilityBank *b=bank(e);if(!b || index<0 || index>=3) return 0;
    u32 a=b->current[index];
    return active_only && !permitted(e,a&65535)?0:a;
}
int ME_AbilityGrade(u8 *e,int identity) {
    if(!known(identity) || !identity) return -1;
    AbilityBank *b=bank(e);
    if(!b) {
        /* Non-array entities retain their original two-byte behavior. */
        u8 *m=monster(e); if(!m || identity>=255 || !permitted(e,identity)) return -1;
        return BYTE(m,0x60)==identity || BYTE(m,0x61)==identity?0:-1;
    }
    int grade=-1;
    for(int i=0;i<3;i++) {
        u32 a=b->current[i]; int id=a&65535;
        if(id && (id==canonical(identity) || (identity<255 && effect(id)==identity)) && permitted(e,id)) {
            int g=(a>>16)&1;if(g>grade) grade=g;
        }
    }
    return grade;
}
int ME_AbilityActive(u8 *e,int identity) { return ME_AbilityGrade(e,identity)>=0; }
int ME_SetAbilityProfile(u8 *e,u32 *profile,int count) {
    if(count<0 || count>3 || (count && !profile)) return 0;
    for(int i=0;i<count;i++) if(!packed_valid(profile[i])) return 0;
    AbilityBank *b=bank(e);if(!b)return 0;
    for(int i=0;i<3;i++) b->permanent[i]=b->current[i]=i<count?((u32)canonical(profile[i]&65535)|(profile[i]&65536)):0;
    b->configured=1;publish(b);return 1;
}
int ME_RestoreAbilities(u8 *e) {
    AbilityBank *b=bank(e);if(!b) return 0;
    for(int i=0;i<3;i++) b->current[i]=b->permanent[i];
    publish(b);return 1;
}
void ME_RestoreMonsterAbilities(u8 *m) {
    for(int i=0;i<COUNT;i++) if(monster(entity(i))==m) {ME_RestoreAbilities(entity(i));return;}
}
int ME_CopyAbilities(u8 *holder,u8 *source) {
    AbilityBank *a=bank(holder),*b=bank(source);if(!a||!b)return 0;
    for(int i=0;i<3;i++) a->current[i]=b->current[i];
    publish(a);return 1;
}
int ME_SwapAbilities(u8 *a,u8 *b) {
    AbilityBank *x=bank(a),*y=bank(b);if(!x||!y)return 0;
    for(int i=0;i<3;i++) {u32 v=x->current[i];x->current[i]=y->current[i];y->current[i]=v;}
    publish(x);publish(y);return 1;
}
int ME_Trace(u8 *source,u8 *holder) {
    AbilityBank *a=bank(holder),*b=bank(source); if(!a||!b || ME_AbilityGrade(holder,40)<0)return 0;
    int trace=-1;for(int i=0;i<3;i++) if(effect(a->current[i]&65535)==40){trace=i;break;}
    u32 candidates[3];int count=0;
    for(int i=0;i<3;i++) {
        u32 v=b->current[i];int id=v&65535;if(!id || !permitted(source,id))continue;
        int duplicate=0;for(int j=0;j<count;j++) if((int)(candidates[j]&65535)==id) {duplicate=1;if(v>candidates[j])candidates[j]=v;}
        if(!duplicate)candidates[count++]=v;
    }
    if(trace<0 || !count)return 0;
    int chosen=count==1?0:FN(0x022eaa98,int(*)(int))(count);
    if(chosen<0 || chosen>=count)return 0;
    u32 v=candidates[chosen];if(ME_AbilityGrade(holder,40)==1)v|=65536;
    a->current[trace]=v;publish(a);return 1;
}
int ME_AbilitiesEqual(u8 *ma,u8 *mb) {
    AbilityBank *a=0,*b=0;
    for(int i=0;i<COUNT;i++) {u8 *e=entity(i);if(monster(e)==ma)a=bank(e);if(monster(e)==mb)b=bank(e);}
    if(!a||!b)return BYTE(ma,0x60)==BYTE(mb,0x60)&&BYTE(ma,0x61)==BYTE(mb,0x61);
    for(int i=0;i<3;i++)if(a->current[i]!=b->current[i])return 0;
    return 1;
}
/* Explicit action brackets, used by effect dispatchers in phases3/7. Nested
 * actions keep their own ledger. An exhausted ledger rejects new claims. */
u32 ME_BeginAction(u8 *actor,int move) {
    ensure();
#ifdef ME_PHASE3
    if(!ability_memory)return 0;
#endif
    if(depth>=4 || !monster(actor) || move<0 || move>65535)return 0;
    Action *a=&actions[depth++];zero(a,sizeof(*a));
    if(!++next_action)++next_action;
    a->token=next_action;a->actor=(u32)actor;a->move=(u16)move;return a->token;
}
int ME_EndAction(u32 token) {
    ensure();
#ifdef ME_PHASE3
    if(!ability_memory)return 0;
#endif
    if(!depth || actions[depth-1].token!=token)return 0;
#ifdef ME_PHASE3
    ME_FlushFaintCopies(token);
#endif
    zero(&actions[--depth],sizeof(Action));return 1;
}
int ME_ClaimEffect(u8 *owner,int identity,int event,u8 *target) {
    ensure();int index=slot(owner);
#ifdef ME_PHASE3
    if(!ability_memory)return 0;
#endif
    if(!depth || index<0 || event<0 || event>255 || ME_AbilityGrade(owner,identity)<0)return 0;
    Action *a=&actions[depth-1];int id=canonical(identity);
    for(int i=0;i<a->used;i++) {
        Once *o=&a->once[i];
        if(o->owner==index && o->ability==id && o->event==event && o->target==(u32)target)return 0;
    }
    if(a->used>=64)return 0;
    Once *o=&a->once[a->used++];o->owner=(u8)index;o->ability=(u16)id;o->event=(u8)event;o->target=(u32)target;return 1;
}
