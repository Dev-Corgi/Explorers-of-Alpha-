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
