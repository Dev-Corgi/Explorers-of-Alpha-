/* Lossless chunking bypasses PKDPX's compressed16-bit length limit. */
int ME_ResidentDecode(u8 *out,int length,u8 *input) {
    u32 total=*(u32*)(input+4),count=*(u32*)(input+8),written=0;
    if(!total || total>0x200000 || !count || count>64 || (length && (u32)length!=total))return 0;
    input+=12;
    for(u32 i=0;i<count;i++) {
        u32 size=*(u32*)input;input+=4;
        if(size<20 || size>65535 || *(u32*)input!=0x50444b50)return 0;
        u32 raw=*(u32*)(input+16);
        if(!raw || raw>32768 || raw>total-written)return 0;
        int n=((int(*)(u8*,int,u8*))0x0201f5cc)(out+written,raw,input);
        if(n!=(int)raw)return 0;
        written+=raw;input+=(size+3)&~3u;
    }
    return written==total?(int)written:0;
}
int ME_ResidentSpriteBytes(int species) {
    u8 *md=*(u8**)0x020B09B4;
    if(!find(species))return 0;
    u32 *meta=(u32*)(md+TOTAL*68+16+(TOTAL-FIRST)*32);
    if(meta[0]!=0x3550454D || meta[1]!=1 || meta[2]!=FIRST || meta[3]!=TOTAL-FIRST)return 0;
    return meta[4+(species-FIRST)*2+1];
}
