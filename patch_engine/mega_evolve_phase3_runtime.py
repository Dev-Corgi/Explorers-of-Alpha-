"""Native prerequisite guards and ARM hook installation for the phase3 loader."""
from __future__ import annotations
import hashlib,struct
from .mega_evolve_runtime import OV29,OV36,word

def elf_sections(path):
    b=path.read_bytes()
    if b[:6]!=b'\x7fELF\x01\x01' or struct.unpack_from('<H',b,18)[0]!=40:
        raise ValueError('mega_evolve expects little-endian ARM ELF32')
    off=struct.unpack_from('<I',b,32)[0]
    stride,count,names=struct.unpack_from('<HHH',b,46)
    rows=[struct.unpack_from('<10I',b,off+i*stride) for i in range(count)]
    s=rows[names];strings=b[s[4]:s[4]+s[5]]
    result=[]
    for row in rows:
        name=strings[row[0]:].split(b'\0',1)[0].decode('ascii')
        result.append({'name':name,'type':row[1],'flags':row[2],'address':row[3],
                       'offset':row[4],'size':row[5],'align':row[8],
                       'data':bytes(row[5]) if row[1]==8 else b[row[4]:row[4]+row[5]]})
    return result

def native_defines(ov29):
    from .hook_registry import branch_target
    values={}
    # Trial Tower wraps the installed team-spawn call after control_mode_enhance.
    # Its installer additionally validates the known predecessor's entry body.
    team_site=0x022df6a4;team_head=word(ov29,team_site,OV29)
    if team_head>>24!=0xeb:raise RuntimeError('mega_evolve prior SpawnTeam call changed')
    values['TT_PRIOR_TEAM']=branch_target(team_site,team_head)
    for name,site in [('USE_MOVE',0x0232145c),('MOVE_TYPE',0x0230227c),
                      ('APPLY_DAMAGE',0x02308fe0),('DUNGEON_FREE',0x022deab0),
                      ('FAINT',0x022f7f34),('CALC_DAMAGE',0x0230bbac),('DEFENSE_DROP',0x02313814),
                      ('HIT_CHECK',0x02323c48),('EXECUTE_EFFECT',0x0232e864)]:
        instruction=word(ov29,site,OV29)
        if instruction>>24!=0xea:raise RuntimeError(f'mega_evolve phase3 prior {name} missing')
        values['PRIOR_'+name]=branch_target(site,instruction)
    from true_patches.mega_evolve.status_hooks import ENTRIES
    for i,(name,site,expected) in enumerate(ENTRIES):
        head=word(ov29,site,OV29)
        observed=head&0xff000000 if expected==0xea000000 else head
        if observed!=expected:raise RuntimeError(f'mega_evolve phase3 {name} status entry changed')
        values[f'STATUS_HEAD_{i}']=head
        values[f'STATUS_TARGET_{i}']=branch_target(site,head) if head>>24==0xea else site+4
    return values


def base_stat_consumers(ov29,ov36):
    """Follow installed BaseStats branches; preceding modules move its cave."""
    from .hook_registry import branch_target
    from true_patches.base_stats_speed.generate_tables import SENTINEL_OFF,SPEED_OFF

    def follow(data,base,site):
        instruction=word(data,site,base)
        if instruction>>24!=0xea:
            raise RuntimeError(f'mega_evolve BaseStats branch changed at {site:#x}')
        target=branch_target(site,instruction)
        if not OV36<=target<OV36+len(ov36)-4:
            raise RuntimeError('mega_evolve BaseStats consumer outside overlay36')
        return target

    combat=follow(ov29,OV29,0x0230c26c)
    # spinda_ev_speed redirects the ov29 hit caller into arm9. Locate the
    # BaseStats hit consumer from its unique installed table marker instead.
    marker=struct.pack('<I',0xb5a7e001)
    position=ov36.find(marker)
    if position<SENTINEL_OFF or ov36.find(marker,position+1)!=-1:
        raise RuntimeError('mega_evolve requires one installed BaseStats marker')
    hit=OV36+position-SENTINEL_OFF+SPEED_OFF
    if not OV36<=hit<OV36+len(ov36)-4:
        raise RuntimeError('mega_evolve BaseStats hit consumer outside overlay36')
    if word(ov36,combat,OV36)!=0xe59d1018:
        raise RuntimeError('mega_evolve BaseStats combat entry changed')
    sites={'ME_MagnetDefenseHook':combat+0x38,
           'ME_AttackStageHook':combat+0x18,
           'ME_UnawareHitStagesHook':hit}
    for name,expected in [('ME_MagnetDefenseHook',0xe3540000),
                          ('ME_AttackStageHook',0xe59d1044),
                          ('ME_UnawareHitStagesHook',0xe35a0000)]:
        if word(ov36,sites[name],OV36)!=expected:
            raise RuntimeError(f'mega_evolve {name} consumer changed')
    return sites


def install_hooks(ov29,ov36,symbols,patch):
    """Phase3 installation of ordinary effect consumers.

    Preserve the balance damage tail before dispatching new final multipliers.
    A changed prerequisite stops installation before ROM files are written.
    """
    from .mega_evolve_runtime import branch
    from .hook_registry import branch_target
    stage_sites=base_stat_consumers(ov29,ov36)
    guards={0x022ffdf4:0xe92d41f0,0x02311088:0xe92d4ff8,
            0x022fd9d4:0xe92d41f8,0x02309a28:branch(0x02309a28,0x022e81f8,True),
            0x02314e54:branch(0x02314e54,0x02314810,True),
            0x0231b094:branch(0x0231b094,0x0231493c,True),
            0x0231b394:branch(0x0231b394,0x0231493c,True),0x02324b24:0xe92d4038,
            0x0232e9c0:0xe1a00006,0x022ee1d8:0xe1a00009,0x0231fde0:0xe92d4ff8,
            0x022f53c0:branch(0x022f53c0,0x022eb60c,True),
            0x0232bcf0:branch(0x0232bcf0,0x023007a8,True),0x022fe4bc:0xe92d43f8,
            0x022fa9d4:branch(0x022fa9d4,0x02301d78,True),
            0x02301600:branch(0x02301600,0x02301d10,True),
            0x023016f8:branch(0x023016f8,0x02301d10,True),
            0x023355a8:branch(0x023355a8,0x02334e70,True),
            0x023277d4:branch(0x023277d4,0x020528fc,True),0x0232eaac:0xe1a00004,
            0x02305fdc:0xe92d43f8,0x023061a8:0xe92d4070,
            0x023063d4:0xe92d4070,0x02306258:0xe92d41f0,
            0x02327928:0xe92d4008,0x02314810:0xe92d43f8,
            0x0232c310:0xe92d41f8,0x0232c354:0xe3a00000,
            0x02332b38:branch(0x02332b38,0x023c1428,True)}
    for site,expected in guards.items():
        if word(ov29,site,OV29)!=expected:
            raise RuntimeError(f'mega_evolve phase3 instruction guard failed at {site:#x}')
    from true_patches.mega_evolve.phase3_items import load as item_data
    old_pickup=item_data()['legacy_pickup_block']
    if hashlib.sha256(ov29[old_pickup['start']-OV29:old_pickup['end']-OV29]).hexdigest()!=old_pickup['sha256']:
        raise RuntimeError('mega_evolve legacy Pickup block changed')
    patch(29,old_pickup['start'],branch(old_pickup['start'],old_pickup['end']),'ReplaceLegacyPickup')
    patch(29,0x022f53c0,branch(0x022f53c0,symbols['ME_BerryConsumeHook'],True),'ME_BerryConsumeHook','ME_BerryConsumeHook')
    patch(29,0x0232bcf0,branch(0x0232bcf0,symbols['ME_SleepTarget'],True),'ME_SleepTarget','ME_SleepTarget')
    for site in (0x0231b2b4,0x023265c0,0x02325cd8,0x023344d4,0x023344fc):
        if word(ov29,site,OV29)!=branch(site,0x023007a8,True):
            raise RuntimeError(f'mega_evolve sleeping consumer changed at {site:#x}')
        patch(29,site,branch(site,symbols['ME_SleepTarget'],True),'MoveSleepPredicate','ME_SleepTarget')
    patch(29,0x023355a8,branch(0x023355a8,symbols['ME_WeatherAppliedHook'],True),'ME_WeatherAppliedHook','ME_WeatherAppliedHook')
    patch(29,0x023277d4,branch(0x023277d4,symbols['ME_WeightMultiplierHook'],True),'ME_WeightMultiplierHook','ME_WeightMultiplierHook')
    patch(29,0x0232eaac,branch(0x0232eaac,symbols['ME_TargetGuardHook']),'ME_TargetGuardHook','ME_TargetGuardHook')
    patch(29,0x02313814,branch(0x02313814,symbols['ME_DefenseDropHook']),'ME_DefenseDropHook','ME_DefenseDropHook')
    patch(29,0x02323c48,branch(0x02323c48,symbols['ME_NoGuardHitHook']),'ME_NoGuardHitHook','ME_NoGuardHitHook')
    patch(29,0x0232e864,branch(0x0232e864,symbols['ME_ParentEffectHook']),'ME_ParentEffectHook','ME_ParentEffectHook')
    patch(29,0x02332b38,branch(0x02332b38,symbols['ME_SheerForceObserveHook'],True),'SheerForceMoveIdObserver','ME_SheerForceObserveHook')
    for overlay,site,expected,name,linked in (
        (29,0x0230c830,branch(0x0230c830,0x0230a940,True),'ME_IntimidateAuraHook',True),
        (29,0x023136e4,branch(0x023136e4,0x02311b94,True),'ME_AttackDropTraitHook',True),
        (36,stage_sites['ME_MagnetDefenseHook'],0xe3540000,'ME_MagnetDefenseHook',True),
        (36,stage_sites['ME_AttackStageHook'],0xe59d1044,'ME_AttackStageHook',True),
        (36,stage_sites['ME_UnawareHitStagesHook'],0xe35a0000,'ME_UnawareHitStagesHook',True),
        (36,0x023c0470,0xe3500001,'ME_StrongDamageWeatherHook',True),
        (36,0x023c04c4,0xe3a00000,'ME_StrongSunImmuneHook',True),
        (29,0x02305fdc,0xe92d43f8,'ME_EndSleepHook',False),
        (29,0x02332d9c,branch(0x02332d9c,0x023b05f0,True),'ME_LiquidOozeHook',True)):
        data,base=(ov29,OV29) if overlay==29 else (ov36,OV36)
        if word(data,site,base)!=expected:raise RuntimeError(f'mega_evolve {name} consumer changed')
        patch(overlay,site,branch(site,symbols[name],linked),name,name)
    for overlay,site,expected,value,name in (
        (36,0x023af4c8,0xe350000f,0xe350000c,'CursedBodyTwelvePercent'),
        (36,0x023c0454,0xe3a03001,0xe3a03003,'JustifiedThreeAttackStages'),
        (29,0x02323d8c,0x108aa00a,0x128aa001,'CompoundEyesOneAccuracyStage'),
        (29,0x023111d8,0x0a000005,0x1a000005,'IceBodyActiveRecoveryGate'),
        (29,0x023111f0,0xe1a00000,0x01a040c4,'IceBodySnowRecoveryHalfDenominator')):
        data,base=(ov29,OV29) if overlay==29 else (ov36,OV36)
        if word(data,site,base)!=expected:raise RuntimeError(f'mega_evolve {name} arithmetic changed')
        patch(overlay,site,value,name)
    # Known existing appearance consumers; only replace their ability reads.
    # No cave/storage is allocated in the protected original ov36 prefix.
    for site,hook in ((0x023bf470,'ME_SpawnTraitReadHook'),(0x023d5c10,'ME_SpawnTraitReadHook'),
                      (0x023bf9cc,'ME_AppearanceTraitReadHook'),(0x023d5dc0,'ME_AppearanceTraitReadHook')):
        if bytes(ov36[site-OV36:site-OV36+8])!=struct.pack('<2I',0xe5d50060,0xe5d51061):
            raise RuntimeError(f'mega_evolve appearance trait read changed at {site:#x}')
        patch(36,site,branch(site,symbols[hook],True),hook,hook)
        patch(36,site+4,0xe3a01000,'AppearanceSecondByteReadRemoved')
    # Follow the live caller, not the disconnected older copy at 0x023d9480.
    if word(ov29,0x02332b28,OV29)!=branch(0x02332b28,0x023af5e4,True):
        raise RuntimeError('mega_evolve active coefficient owner changed')
    frisk=0x023afbd8
    if bytes(ov36[frisk-OV36:frisk-OV36+12])!=struct.pack('<3I',0x11a02107,0x10827007,0x11a07127):
        raise RuntimeError('mega_evolve active Frisk coefficient changed')
    patch(36,frisk,(branch(frisk,symbols['ME_R7CoefficientHook'],True)&0x0fffffff)|0x10000000,'FriskSixFifths','ME_R7CoefficientHook')
    for offset in (4,8):patch(36,frisk+offset,0xe1a00000,'FriskOldScaleRemoved')
    for name,site in (('Sharpness',0x023afcf0),('Analytic',0x023b00f8),('MegaLauncher',0x023b0324),('ToughClaws',0x023b03a8)):
        expected=struct.pack('<4I',0xe1a00107,0xe3a01003,branch(site+8,0x0208fea4,True),0xe1a07000)
        if bytes(ov36[site-OV36:site-OV36+16])!=expected:
            raise RuntimeError(f'mega_evolve active {name} coefficient changed')
        patch(36,site,branch(site,symbols['ME_R7CoefficientHook'],True),name+'SixFifths','ME_R7CoefficientHook')
        for offset in (4,8,12):patch(36,site+offset,0xe1a00000,name+'OldScaleRemoved')
    for name,site in (('StrongJaws',0x023afba4),('SandForce',0x023b0094)):
        if bytes(ov36[site-OV36:site-OV36+8])!=struct.pack('<2I',0xe0877087,0xe1a070a7):
            raise RuntimeError(f'mega_evolve active {name} coefficient changed')
        patch(36,site,branch(site,symbols['ME_R7CoefficientHook'],True),name+'SixFifths','ME_R7CoefficientHook')
        patch(36,site+4,0xe1a00000,name+'OldScaleRemoved')
    site=0x023afa38
    if bytes(ov36[site-OV36:site-OV36+8])!=struct.pack('<2I',0x00877087,0x01a07127):
        raise RuntimeError('mega_evolve active Friend Guard coefficient changed')
    patch(36,site,branch(site,symbols['ME_FriendGuardCoefficientHook'],True)&0x0fffffff,'FriendGuardFourFifths','ME_FriendGuardCoefficientHook')
    patch(36,site+4,0xe1a00000,'FriendGuardOldScaleRemoved')
    site=0x0230b070
    if word(ov29,site,OV29)!=0xe59f272c:
        raise RuntimeError('mega_evolve shared Filter multiplier site changed')
    patch(29,site,branch(site,symbols['ME_FilterMultiplierHook'],True),'FilterFourFifths','ME_FilterMultiplierHook')
    site=0x0230c694
    if word(ov29,site,OV29)!=0x11a04084:
        raise RuntimeError('mega_evolve Guts numerator site changed')
    patch(29,site,(branch(site,symbols['ME_GutsRatioHook'],True)&0x0fffffff)|0x10000000,'GutsThreeHalves','ME_GutsRatioHook')
    site=0x0230bc40
    if bytes(ov29[site-OV29:site-OV29+12])!=struct.pack('<3I',0x10800080,0x10800fa0,0x11a000c0):
        raise RuntimeError('mega_evolve Reckless power arithmetic changed')
    patch(29,site,(branch(site,symbols['ME_PowerSixFifthsHook'],True)&0x0fffffff)|0x10000000,'RecklessPowerSixFifths','ME_PowerSixFifthsHook')
    for offset in (4,8):patch(29,site+offset,0xe1a00000,'RecklessOldPowerScaleRemoved')
    site=0x0230bc7c
    if word(ov29,site,OV29)!=branch(site,0x02001a54,True):
        raise RuntimeError('mega_evolve Iron Fist power call changed')
    patch(29,site,branch(site,symbols['ME_PowerSixFifthsHook'],True),'IronFistPowerSixFifths','ME_PowerSixFifthsHook')
    for site in (0x0230b2b8,0x0230b364,0x0230b410,0x0230b4bc):
        expected=0xe59f2000|(0x0230b7bc-(site+8))
        if word(ov29,site,OV29)!=expected:
            raise RuntimeError(f'mega_evolve pinch multiplier pointer changed at {site:#x}')
        patch(29,site,branch(site,symbols['ME_PinchMultiplierHook'],True),'PinchThreeHalves','ME_PinchMultiplierHook')
    for site in (0x0230b130,0x0230b1c0):
        expected=0xe59f2000|(0x0230b7a8-(site+8))
        if word(ov29,site,OV29)!=expected:raise RuntimeError('mega_evolve Thick Fat/Heatproof multiplier changed')
        patch(29,site,branch(site,symbols['ME_HalfMultiplierHook'],True),'ThickFatHeatproofHalfDamage','ME_HalfMultiplierHook')
    patch(29,0x02327928,branch(0x02327928,symbols['ME_BoostSpeedMoveHook']),'ME_BoostSpeedMoveHook','ME_BoostSpeedMoveHook')
    patch(29,0x02314810,branch(0x02314810,symbols['ME_IncreaseMovementHook']),'ME_IncreaseMovementHook','ME_IncreaseMovementHook')
    entry=0x0230d03c;owner=word(ov29,entry,OV29)
    if owner>>24!=0xea:raise RuntimeError('mega_evolve balance damage tail missing')
    start=branch_target(entry,owner)
    if bytes(ov36[start-OV36:start-OV36+12])!=struct.pack('<III',0xe92d40ff,0xe5987000,0xe3570000):
        raise RuntimeError('mega_evolve unexpected balance damage tail owner')
    exits=[site for site in range(start,start+0x110,4)
           if word(ov36,site,OV36)==branch(site,0x0230d040)]
    if len(exits)!=1:raise RuntimeError('mega_evolve balance damage tail exit changed')
    sound=start+0x18
    if word(ov36,sound,OV36)!=branch(sound,0x02013d5c,True):
        raise RuntimeError('mega_evolve sound damage classifier owner changed')
    patch(36,sound,branch(sound,symbols['ME_SoundMoveIdHook'],True),'SoundDamageMoveIdABI','ME_SoundMoveIdHook')
    # This pair belongs only to Punk Rock's defensive multiplier, after its
    # query. The aura multiplier later in the same owner must stay 4/5.
    for offset,expected in ((0x68,0xe3a01004),(0x70,0xe3a01005)):
        if word(ov36,start+offset,OV36)!=expected:
            raise RuntimeError('mega_evolve Punk Rock owner guard failed')
    patch(36,start+0x68,0xe3a01001,'PunkRockDefenseNumerator')
    patch(36,start+0x70,0xe3a01002,'PunkRockDefenseDenominator')
    patch(36,exits[0],branch(exits[0],symbols['ME_DamageTailHook']),
          'ME_DamageTailHook','ME_DamageTailHook')
    hooks=[(0x0232145c,'ME_ActionHook'),
           (0x0230227c,'ME_TypeHook'),(0x0230bbac,'ME_CalculationHook'),
           (0x022ffdf4,'ME_MovementHook'),(0x022f7f34,'ME_FaintHook'),
           (0x02311088,'ME_TurnHook'),(0x022fd9d4,'ME_InitHook'),
           (0x022deab0,'ME_FreeHook'),(0x02309a28,'ME_HitBoundaryHook'),(0x02324b24,'ME_CanUseMoveHook'),
           (0x0232e9c0,'ME_RedirectHook'),(0x022ee1d8,'ME_FloorTrapHook'),(0x0231fde0,'ME_BlowAwayHook'),
           (0x022fe4bc,'ME_ExecuteActionHook')]
    for site,name in hooks:
        patch(29,site,branch(site,symbols[name],site==0x02309a28),name,name)
    for site,name in ((0x02314e54,'ME_QuickFeet'),(0x0231b094,'ME_MotorDrive'),(0x0231b394,'ME_Steadfast')):
        patch(29,site,branch(site,symbols[name],True),name,name)
    from true_patches.mega_evolve.status_hooks import ENTRIES
    for name,site,expected in ENTRIES:
        symbol='ME_Status'+name+'Hook'
        patch(29,site,branch(site,symbols[symbol]),symbol,symbol)
