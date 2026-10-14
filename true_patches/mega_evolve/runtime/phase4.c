/* Explicit permanent-form trailer, loaded alongside native monster.md. */
const MEForm *ME_FindForm(int species) {
    if(species<ME_FORM_FIRST || species>=ME_FORM_FIRST+ME_FORM_COUNT)return 0;
    u8 *md=*(u8 **)0x020b09b4;
    if(!md || U32(md,-4)!=ME_FORM_FIRST+ME_FORM_COUNT)return 0;
    u8 *tail=md+(ME_FORM_FIRST+ME_FORM_COUNT)*68;
    if(U32(tail,0)!=0x3446454d || U32(tail,4)!=1 ||
       U32(tail,8)!=ME_FORM_FIRST || U32(tail,12)!=ME_FORM_COUNT)return 0;
    const MEForm *f=(const MEForm *)(tail+16)+(species-ME_FORM_FIRST);
    return f->species==species?f:0;
}
int ME_FormStage(int species) {
    const MEForm *f=ME_FindForm(species);return f?f->stage:0;
}
int ME_FormOrigin(int species) {
    const MEForm *f=ME_FindForm(species);return f?f->origin:species;
}
int ME_FormParent(int species) {
    const MEForm *f=ME_FindForm(species);return f?f->parent:0;
}
int ME_FormCalcStat(int species,int level,int stat,int doping) {
    const MEForm *f=ME_FindForm(species);
    if(!f || stat<0 || stat>=6)return -1;
    int value=clamp((int)f->stats[stat]+doping,0,32767);
    value=divide(value*2*clamp(level,0,100),100);
    value+=stat==0?clamp(level,0,100)+10:5;
    return clamp(value,0,32767);
}
#include "new_species_generated.h"
static const MENewSpecies *new_species(int species) {
    const MEForm *f=ME_FindForm(species);
    if(f && f->stage)species=f->origin;
    for(int i=0;i<4;i++)if(me_new_species[i].species==species)return &me_new_species[i];
    return 0;
}
int ME_NewNameSpecies(int species) {
    const MENewSpecies *s=new_species(species);
    return s?(int)s->name|((int)s->gender<<16):0;
}
int ME_LearnSpecies(int species) {
    const MENewSpecies *s=new_species(species);
    return s?s->learn:ME_FormOrigin(species);
}
int ME_PortraitSpecies(int species) {
    const MENewSpecies *s=new_species(species);
    return s?s->portrait:ME_FormOrigin(species);
}
int ME_NewEvolutionCandidates(u8 *p,u8 *out) {
    for(int i=0;i<4;i++)if(me_new_species[i].parent==U16(p,4)) {
        zero(out+10,48);U16(out,8)=0;
        if(BYTE(p,1)>=20) {
            U16(out,6)=1;U16(out,8)=me_new_species[i].species;
            U16(out,10)=me_new_species[i].species;
        } else U16(out,6)=2;
        return 1;
    }
    return 0;
}
