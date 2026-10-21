/* Adapted from luminous_evolution's shop controller; standalone mega_evolve
 * code/data live in a separately allocated, shop-local ov16 cave.
 * ARM9 calls this only from the Spring-specific team selection path (mode 5).
 * No pointers to this overlay are retained after the shop closes. */
#include "phase6_generated.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef short s16;
#define FN(a, result, args) ((result (*) args)(a))
#define RD16(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define RD32(p,o) (*(u32 *)((u8 *)(p)+(o)))
static u32 mode; /* 0=evolution, 1=regression, 2=legacy form */
static u32 evolution_kind; /* Evolve action: 0=ordinary, 1=Mega, 2=Shiny */
volatile u32 ME_SpringCompletionAddon=0xffffffffu;
static u32 story;
static u32 submenu[16];
static u8 *state(void) { return *(u8 **)SPRING_STATE_PTR; }
/* The ground evolution flash outlives the shop controller. Its frame-180
 * callback can arrive after the controller has been freed. On the DS a
 * NULL+0xD8 write aliases ITCM and destroys CopyAndInterleave0's LSL. */
void ME_Spring_AnimationComplete(void) {
    u8 *s=state();
    if(s)RD32(s,0xD8)=4;
}
static u8 *member(int index) { return FN(0x020555A8,u8*,(int))(index); }
static int base(int species) {
    if (species >= 600) species -= 600;
    return species > 0 && species < 600 ? species : 0;
}
static int previous(int species) {
    return species > 0 && species < MD_COUNT ? previous_species[species] : 0;
}
static int form_group(int species) { return form_groups[base(species)]; }
static int stage(int species) {return species>0 && species<MD_COUNT?mega_stage[species]:0;}
static int choices(u8 *p,int wanted,u16 *out) {
    int species=RD16(p,4),n=0;
    if(species<=0 || species>=MD_COUNT || story)return 0;
    for(int i=route_offsets[species];i<route_offsets[species+1];i++) {
        const MERoute *r=&mega_routes[i];
        if(r->stage==wanted && p[1]>=r->level) {if(out)out[n]=r->target;n++;}
    }
    return n;
}
static int form_choices(int species,u16 *out) {
    if(stage(species) || species>=FORM_FIRST)return 0;
    int group=form_group(species),n=0;if(!group)return 0;
    for(int i=0;i<4;i++) {
        int target=form_targets[group][i];if(!target)break;
        if(species>=600 && form_secondary[base(species)])target+=600;
        if(target!=species && !stage(target)) {if(out)out[n]=target;n++;}
    }
    return n;
}
static int story_member(const u8 *p) { return p[2] == 0xD6 || p[2] == 0xD7; }
void ME_Spring_Prepare(void) {
    mode = 0; evolution_kind=0;
    story = !FN(0x0204CA94,int,(int))(5);
    /* First-visit menu is inserted after Teddiursa evolves. This is the same
     * unlock written by the existing graduation controller after that scene. */
    if (story) FN(0x0204CB2C,void,(int,int))(5,1);
}
void ME_Spring_Possibilities(u8 *p, u8 *out) {
    int species=RD16(p,4);
    if(species<=0 || species>=MD_COUNT) {
        for(int i=0;i<48;i++)out[10+i]=0;
        RD16(out,6)=4;RD16(out,8)=0;return;
    }
    if(route_offsets[species]!=route_offsets[species+1] && !story) {
        for(int i=0;i<48;i++)out[10+i]=0;
        int wanted=mega_routes[route_offsets[species]].stage;
        int n=choices(p,wanted,(u16*)(out+10));
        RD16(out,6)=n?1:2;RD16(out,8)=n?RD16(out,10):0;return;
    }
    if(stage(species)) {
        for(int i=0;i<48;i++)out[10+i]=0;
        RD16(out,6)=4;RD16(out,8)=0;return;
    }
    FN(0x02059B18,void,(u8*,u8*))(p,out);
    int group = form_group(RD16(p,4));
    int remaining = 0;
    for (int i=0;i<8;i++) {
        int target = RD16(out,10+i*2);
        if (target && (stage(target) || (group && form_group(target) == group))) RD16(out,10+i*2)=0;
        else if (target) remaining=target;
    }
    RD16(out,8)=remaining;
    if (!remaining) RD16(out,6)=(RD16(out,6)&~1u)|4u;
}
void ME_Spring_Eligibility(u8 *p, u8 *out) {
    ME_Spring_Possibilities(p,out);
    if (story && !story_member(p)) { RD16(out,8)=0; return; }
    if (!story && !RD16(out,8) &&
        (previous(RD16(p,4)) || form_choices(RD16(p,4),0) || choices(p,1,0) || choices(p,2,0)))
        RD16(out,8)=RD16(p,4); /* only the list/count predicate consumes this */
}
int ME_Spring_Count(void) {
    int count=0;
    for (int i=0;i<TEAM_COUNT;i++) {
        if (!FN(0x02055390,int,(int))(i)) continue;
        u8 out[60];
        ME_Spring_Eligibility(member(i),out);
        if (RD16(out,8)) count++;
    }
    return count;
}
void ME_Spring_Submenu(void) {
    u8 *s=state();
    mode=0;
    int species=RD16((u8 *)RD32(s,0x3C),4);
    evolution_kind=species>0 && species<MD_COUNT && route_offsets[species]!=route_offsets[species+1]?mega_routes[route_offsets[species]].stage:0;
    u8 out[60];
    ME_Spring_Possibilities((u8 *)RD32(s,0x3C),out);
    int count=0;
    if (RD16(out,8)) {
        submenu[count*2]=1077; submenu[count++*2+1]=3;
    }
    if (!story && previous(species)) {
        submenu[count*2]=STR_REGRESSION; submenu[count++*2+1]=10;
    }
    if (!story && form_choices(species,0)) {
        submenu[count*2]=STR_FORM; submenu[count++*2+1]=11;
    }
    submenu[count*2]=1078; submenu[count++*2+1]=8;
    submenu[count*2]=1079; submenu[count++*2+1]=1;
    submenu[count*2]=0; submenu[count*2+1]=1;
    /* width/height zero let CreateSimpleMenu size the four/five-row menu. */
    s[0xC3]=FN(0x0202B0EC,int,(void*,u32,void*,void*,int))
        ((void *)SUBMENU_WINDOW,SUBMENU_FLAGS,0,submenu,count);
}
int ME_Spring_Action(int action) {
    if (action!=10 && action!=11) return 0;
    u8 *s=state();
    int species=RD16((u8 *)RD32(s,0x3C),4);
    if (story) return 0;
    int pre=previous(species);
    if ((action==10 && !pre) || (action==11 && !form_choices(species,0))) return 0;
    mode=action-9;
    /* The ordinary target selector/confirmation/animation can be reused, but
     * its item slots must be cleared, and form targets must exclude self. */
    for (int i=0;i<48;i++) s[0xC+i]=0;
    if (mode==1) RD16(s,0xC)=pre;
    else form_choices(species,(u16*)(s+0xC));
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
int ME_Spring_Convert(s16 *index,int target) {
    u8 *p=member(*index);int old_stage=stage(RD16(p,4));
    u8 out[60];for(int i=0;i<60;i++)out[i]=0;
    if(!mode && !evolution_kind) {
        if(old_stage || target<=0 || target>=MD_COUNT || stage(target))return 0;
        if(target>=FORM_FIRST) {
            int n=choices(p,0,(u16*)out),found=0;
            for(int i=0;i<n;i++)if(RD16(out,i*2)==target)found=1;
            if(!found)return 0;
        }
        /* Ordinary selection already carries native item/stat conditions.
         * Do not re-evaluate them with an empty parameter block. Retain the
         * native Nincada -> Ninjask/Shedinja conversion and history updates. */
        return FN(0x0205A288,int,(s16*,int))(index,target);
    }
    int valid=0;
    if(mode==1)valid=target==previous(RD16(p,4));
    else if(mode==2) {int n=form_choices(RD16(p,4),(u16*)out);for(int i=0;i<n;i++)if(RD16(out,i*2)==target)valid=1;}
    else if(!mode && evolution_kind) {int n=choices(p,evolution_kind,(u16*)out);for(int i=0;i<n;i++)if(RD16(out,i*2)==target)valid=1;}
    if(!valid || !target)return 0;
    u8 first=p[6], second=p[7];
    FN(0x0205A340,int,(s16*,u8*,int))(index,p,target);
    p=member(*index);
    p[6]=first; p[7]=second; /* forms do not add evolution-history entries */
    if (!mode && evolution_kind==1 && RD16(p,4)==target &&
        ME_SpringCompletionAddon!=0xffffffffu)
        ((void(*)(void))ME_SpringCompletionAddon)();
    if (mode==1 && !old_stage) {
        if (p[7]) p[7]=0; else p[6]=0;
    }
    return 1;
}
void ME_Spring_RecordEvolution(void) {
    if (!mode && !evolution_kind) FN(0x0204FCDC,void,(void))();
}
void ME_Spring_Message(int window,u32 flags,int id,void *args) {
    if(!mode && evolution_kind) {
        if(id==1080 || id==1076)id=evolution_kind==1?STR_MEGA_CONFIRM:STR_SHINY_CONFIRM;
        if(id==1081)id=evolution_kind==1?STR_MEGA_SELECT:STR_SHINY_SELECT;
        if(id==1087)id=evolution_kind==1?STR_MEGA_SUCCESS:STR_SHINY_SUCCESS;
    } else if (mode && (id==1080 || id==1076))
        id=mode==1 ? STR_REG_CONFIRM : STR_FORM_CONFIRM;
    if (mode==2 && id==1081) id=STR_FORM_SELECT;
    if (mode && mode<3 && id==1087)
        id=mode==1 ? STR_REG_SUCCESS : STR_FORM_SUCCESS;
    FN(0x0202F1B4,void,(int,u32,int,void*))(window,flags,id,args);
}
void *ME_Spring_TargetLabel(void *out,int index) {
    extern void *ME_SpringNativeTargetLabel(void*,int);
    u8 *s=state();
    if (mode!=2 && (mode || evolution_kind!=1 || choices((u8*)RD32(s,0x3C),1,0)<=1))
        return ME_SpringNativeTargetLabel(out,index);
    int target=RD16(s,0xC+RD32(s,0x50+index*4)*2);
    int label_id=mode==2?form_labels[base(target)]:STR_BRANCH_MEGA;
    if(!mode && evolution_kind==1) {
        for(int i=0;i<route_offsets[MD_COUNT];i++)
            if(mega_routes[i].target==target)label_id=mega_routes[i].label;
    }
    const char *label=FN(0x020258C4,const char*,(int))(label_id);
    FN(0x020251F4,void,(void*,const void*,int))(out,label,0x400);
    return out;
}
