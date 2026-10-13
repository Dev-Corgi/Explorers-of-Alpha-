"""Inventory byte-slot consumers in the prerequisite full stack (read only)."""
import hashlib,json,sys
from pathlib import Path
from ndspy.rom import NintendoDSRom
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
REPO=Path(__file__).resolve().parents[2]
def build():
    path=REPO/"PatchTesting/Export Rom/Explorers of Alpha+.nds"
    rom=NintendoDSRom(path.read_bytes());overlays=rom.loadArm9Overlays()
    decoder=Cs(CS_ARCH_ARM,CS_MODE_ARM);decoder.skipdata=True
    sites=[]
    for overlay,base in ((29,0x022dc240),(36,0x023a7080)):
        for ins in decoder.disasm(bytes(overlays[overlay].data),base):
            if ins.mnemonic.startswith(("ldrb","strb")) and any(s in ins.op_str for s in ("#0x60]","#0x61]")):
                sites.append({"overlay":overlay,"site":hex(ins.address),"instruction":ins.mnemonic+" "+ins.op_str,
                              "classification":"byte_slot_candidate_requires_owner_review"})
    return {"source":"existing prerequisite English full stack; no latest module installed",
            "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"candidates":sites,
            "phase2_replaced_paths":["AbilityIsActive + veneer/defender/other-monster callers",
                "Trace selection/write","Skill Swap three-slot exchange","Role Play three-slot copy",
                "ability status equality","SetMonsterTypeAndAbility restore"],
            "phase3_effect_owners":"transform/imposter/illusion and other per-effect direct readers/writers",
            "phase8_display_owners":"two-slot summary/UI views; use ME_GetAbility API",
            "note":"Linear disassembly includes code/data candidates, not certified ability references."}
if __name__=="__main__":
    (REPO/"true_patches/mega_evolve/data/phase2_slot_audit.json").write_text(json.dumps(build(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
