/* All code/data live in the dynamically allocated, shop-local ov16 cave.
 * ARM9 calls this only from the Spring-specific team selection path (mode 5).
 * No pointers to this overlay are retained after the shop closes. */
#include "generated.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef short s16;
#define FN(a, result, args) ((result (*) args)(a))
#define RD16(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define RD32(p,o) (*(u32 *)((u8 *)(p)+(o)))
static u32 mode; /* 0=evolution, 1=regression, 2=form */
static u32 story;
static u32 submenu[12];
static u8 *state(void) { return *(u8 **)SPRING_STATE_PTR; }
static u8 *member(int index) { return FN(0x020555A8,u8*,(int))(index); }
static int base(int species) {
    if (species >= 600) species -= 600;
    return species > 0 && species < 600 ? species : 0;
}
static int previous(int species) {
    return species > 0 && species < MD_COUNT ? previous_species[species] : 0;
}
static int form_group(int species) { return form_groups[base(species)]; }
static int story_member(const u8 *p) { return p[2] == 0xD6 || p[2] == 0xD7; }
void Spring_Prepare(void) {
    mode = 0;
    story = !FN(0x0204CA94,int,(int))(5);
    /* First-visit menu is inserted after Teddiursa evolves. This is the same
     * unlock written by the existing graduation controller after that scene. */
    if (story) FN(0x0204CB2C,void,(int,int))(5,1);
}
void Spring_Possibilities(u8 *p, u8 *out) {
    FN(0x02059B18,void,(u8*,u8*))(p,out);
    int group = form_group(RD16(p,4));
    if (!group) return;
    int remaining = 0;
    for (int i=0;i<8;i++) {
        int target = RD16(out,10+i*2);
        if (target && form_group(target) == group) RD16(out,10+i*2)=0;
        else if (target) remaining=target;
    }
    RD16(out,8)=remaining;
    if (!remaining) RD16(out,6)=(RD16(out,6)&~1u)|4u;
}
void Spring_Eligibility(u8 *p, u8 *out) {
    Spring_Possibilities(p,out);
    if (story && !story_member(p)) { RD16(out,8)=0; return; }
    if (!story && !RD16(out,8) &&
        (previous(RD16(p,4)) || form_group(RD16(p,4))))
        RD16(out,8)=RD16(p,4); /* only the list/count predicate consumes this */
}
int Spring_Count(void) {
    int count=0;
    for (int i=0;i<TEAM_COUNT;i++) {
        if (!FN(0x02055390,int,(int))(i)) continue;
        u8 out[60];
        Spring_Eligibility(member(i),out);
        if (RD16(out,8)) count++;
    }
    return count;
}
void Spring_Submenu(void) {
    u8 *s=state();
    mode=0;
    int species=RD16((u8 *)RD32(s,0x3C),4);
    u8 out[60];
    Spring_Possibilities((u8 *)RD32(s,0x3C),out);
    int count=0;
    if (RD16(out,8)) {
        submenu[count*2]=1077; submenu[count++*2+1]=3;
    }
    if (!story && previous(species)) {
        submenu[count*2]=STR_REGRESSION; submenu[count++*2+1]=10;
    }
    if (!story && form_group(species)) {
        submenu[count*2]=STR_FORM; submenu[count++*2+1]=11;
    }
    submenu[count*2]=1078; submenu[count++*2+1]=8;
    submenu[count*2]=1079; submenu[count++*2+1]=1;
    submenu[count*2]=0; submenu[count*2+1]=1;
    /* width/height zero let CreateSimpleMenu size the four/five-row menu. */
    s[0xC3]=FN(0x0202B0EC,int,(void*,u32,void*,void*,int))
        ((void *)SUBMENU_WINDOW,SUBMENU_FLAGS,0,submenu,count);
}
int Spring_Action(int action) {
    if (action!=10 && action!=11) return 0;
    u8 *s=state();
    int species=RD16((u8 *)RD32(s,0x3C),4);
    if (story) return 0;
    int group=form_group(species), pre=previous(species);
    if ((action==10 && !pre) || (action==11 && !group)) return 0;
    mode=action==10 ? 1 : 2;
    /* The ordinary target selector/confirmation/animation can be reused, but
     * its item slots must be cleared, and form targets must exclude self. */
    for (int i=0;i<48;i++) s[0xC+i]=0;
    int n=0;
    if (mode==1) RD16(s,0xC)=pre;
    else for (int i=0;i<4;i++) {
        int target=form_targets[group][i];
        if (!target) break;
        if (species>=600 && form_secondary[base(species)]) target+=600;
        if (base(target)!=base(species)) RD16(s,0xC+n++*2)=target;
    }
    RD16(s,8)=1;
    RD32(s,0x40)=0;
    FN(0x0238CAE8,void,(void))();
    FN(0x0203A51C,void,(void))();
    FN(0x0203C874,void,(void))();
    /* Match normal Evolve's delayed transition: the roster/portrait must close
     * before target selection. Keep the native confirmation/cancel flow. */
    RD32(s,0x78)=10;
    RD32(s,0x74)=22;
    FN(0x0238A140,void,(int))(24);
    return 1;
}
int Spring_Convert(s16 *index,int target) {
    if (!mode) {
        /* This wrapper retains the original Nincada -> Ninjask/Shedinja case.
         * The resident species writer below retains the old XP and doping. */
        return FN(0x0205A288,int,(s16*,int))(index,target);
    }
    u8 *p=member(*index);
    u8 first=p[6], second=p[7];
    FN(0x0205A340,int,(s16*,u8*,int))(index,p,target);
    p=member(*index);
    p[6]=first; p[7]=second; /* forms do not add evolution-history entries */
    if (mode==1) {
        if (p[7]) p[7]=0; else p[6]=0;
    }
    return 1;
}
void Spring_RecordEvolution(void) {
    if (!mode) FN(0x0204FCDC,void,(void))();
}
void Spring_Message(int window,u32 flags,int id,void *args) {
    if (mode && (id==1080 || id==1076))
        id=mode==1 ? STR_REG_CONFIRM : STR_FORM_CONFIRM;
    if (mode==2 && id==1081) id=STR_FORM_SELECT;
    if (mode && id==1087)
        id=mode==1 ? STR_REG_SUCCESS : STR_FORM_SUCCESS;
    FN(0x0202F1B4,void,(int,u32,int,void*))(window,flags,id,args);
}
void *Spring_TargetLabel(void *out,int index) {
    if (mode!=2) return FN(ORIGINAL_TARGET_LABEL,void*,(void*,int))(out,index);
    u8 *s=state();
    int target=RD16(s,0xC+RD32(s,0x50+index*4)*2);
    const char *label=FN(0x020258C4,const char*,(int))(form_labels[base(target)]);
    FN(0x020251F4,void,(void*,const void*,int))(out,label,0x400);
    return out;
}
