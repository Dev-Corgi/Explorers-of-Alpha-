from __future__ import annotations



import tempfile

from pathlib import Path

from typing import Any



from ndspy.code import loadOverlayTable

from ndspy.rom import NintendoDSRom

from skytemple_files.common.util import get_ppmdu_config_for_rom



from .apply_asm import apply_asm_multi, apply_asm_single, verify_asm_module

from .manifest import load_module_manifest, load_rom_profile

from .state import AppliedModule, BuildState, load_state, save_state





def _true_patches_root() -> Path:

    return Path(__file__).resolve().parent.parent / "true_patches"





def _repo_root() -> Path:

    return _true_patches_root().parent





def _prior_hook_sites(state: BuildState | None, *, exclude_module: str | None = None) -> set[int]:

    sites: set[int] = set()

    if not state:

        return sites

    for mod in state.applied:

        if exclude_module and mod.id == exclude_module:

            continue

        for hook in mod.hooks:

            sites.add(hook.site)

    return sites





def apply_module(

    module_id: str,

    rom_in: Path,

    rom_out: Path,

    *,

    state_path: Path | None = None,

    armips: Path | None = None,

    force_reapply: bool = False,

) -> BuildState:

    root = _true_patches_root()

    module_dir = root / module_id

    manifest = load_module_manifest(module_dir)

    if manifest.get("id") != module_id:

        raise ValueError(f"manifest id {manifest.get('id')!r} != {module_id!r}")



    profile_id = manifest.get("rom_profile", "us_vanilla")

    profile = load_rom_profile(Path(__file__).resolve().parent, profile_id)

    overlay_load = int(profile.get("overlay29_load", 0x022DC240))



    state = load_state(state_path) if state_path else None

    if state is None:

        state = BuildState(rom_profile=profile_id, overlay29_load=overlay_load)

    elif state.rom_profile != profile_id:

        raise RuntimeError(

            f"state profile {state.rom_profile!r} != module {profile_id!r}"

        )



    if state.get_module(module_id) and not force_reapply:

        raise RuntimeError(

            f"module {module_id!r} already in state; pass force_reapply=True to redo"

        )



    rom = NintendoDSRom(rom_in.read_bytes())

    config = get_ppmdu_config_for_rom(rom)

    kind = manifest.get("kind", "asm")

    armips_exe = armips or (_repo_root() / "tools" / "armips.exe")

    if kind == "luminous_evolution":
        from .apply_luminous_evolution import apply_luminous_evolution_module

        record = apply_luminous_evolution_module(
            module_id, module_dir, manifest, rom, armips_exe, state,
        )
        state.upsert_module(record)
        rom_out.write_bytes(rom.save())
        if state_path:
            save_state(state_path, state)
        return state

    if kind == "berry_boost":
        if not armips_exe.is_file():
            raise FileNotFoundError(f"armips not found: {armips_exe}")
        from .apply_berry_boost import apply_berry_boost_module

        record = apply_berry_boost_module(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            rom=rom,
            armips=armips_exe,
            state=state,
            rom_in=rom_in,
        )
        state.upsert_module(record)
        rom_out.write_bytes(rom.save())
        if state_path:
            save_state(state_path, state)
        return state

    if kind == "tm_read":
        if not armips_exe.is_file():
            raise FileNotFoundError(f"armips not found: {armips_exe}")
        from .apply_tm_read import apply_tm_read_module

        prior = _prior_hook_sites(state, exclude_module=module_id if force_reapply else None)
        record = apply_tm_read_module(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            profile=profile,
            rom=rom,
            armips=armips_exe,
            state=state,
            rom_in=rom_in,
            prior_hook_sites=prior,
        )
        state.upsert_module(record)
        rom_out.write_bytes(rom.save())
        if state_path:
            save_state(state_path, state)
        return state

    if kind == "z_move":
        if not armips_exe.is_file():
            raise FileNotFoundError(f"armips not found: {armips_exe}")
        from .apply_z_move import apply_z_move_module

        prior = _prior_hook_sites(state, exclude_module=module_id if force_reapply else None)
        record = apply_z_move_module(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            profile=profile,
            rom=rom,
            armips=armips_exe,
            state=state,
            prior_hook_sites=prior,
            force_reapply=force_reapply,
        )
        state.upsert_module(record)
        rom_out.write_bytes(rom.save())
        if state_path:
            save_state(state_path, state)
        return state




    if kind == "spinda_ev":
        if not armips_exe.is_file():
            raise FileNotFoundError(f"armips not found: {armips_exe}")
        from .apply_spinda_ev import apply_spinda_ev_module

        prior = _prior_hook_sites(state, exclude_module=module_id if force_reapply else None)
        record = apply_spinda_ev_module(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            profile=profile,
            rom=rom,
            armips=armips_exe,
            state=state,
            prior_hook_sites=prior,
            force_reapply=force_reapply,
        )
        state.upsert_module(record)
        rom_out.write_bytes(rom.save())
        if state_path:
            save_state(state_path, state)
        return state




    if kind == "data":

        from .apply_data import apply_data_module



        return apply_data_module(

            module_id,

            rom_in,

            rom_out,

            state_path=state_path,

            force_reapply=force_reapply,

        )

    if kind == "damage_formula":
        if not armips_exe.is_file():
            raise FileNotFoundError(f"armips not found: {armips_exe}")
        from .apply_damage_formula import apply_damage_formula_module

        prior = _prior_hook_sites(state, exclude_module=module_id if force_reapply else None)
        record = apply_damage_formula_module(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            profile=profile,
            rom=rom,
            config=config,
            armips_exe=armips_exe,
            state=state,
            prior_hook_sites=prior,
            rom_in=rom_in,
        )
        state.upsert_module(record)
        rom_out.write_bytes(rom.save())
        if state_path:
            save_state(state_path, state)
        return state



    if kind == "korean":
        if not armips_exe.is_file():
            raise FileNotFoundError(f"armips not found: {armips_exe}")
        from .apply_korean import apply_korean_module

        prior = _prior_hook_sites(state, exclude_module=module_id if force_reapply else None)
        record = apply_korean_module(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            profile=profile,
            rom=rom,
            armips=armips_exe,
            state=state,
            prior_hook_sites=prior,
        )
        state.upsert_module(record)
        rom_out.write_bytes(rom.save())
        if state_path:
            save_state(state_path, state)
        return state

    if kind == "balance_change":
        if not armips_exe.is_file():
            raise FileNotFoundError(f"armips not found: {armips_exe}")
        from .apply_balance_change import apply_balance_change_module

        prior = _prior_hook_sites(state, exclude_module=module_id if force_reapply else None)
        record = apply_balance_change_module(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            profile=profile,
            rom=rom,
            config=config,
            armips_exe=armips_exe,
            prior_hook_sites=prior,
            state=state,
        )
        state.upsert_module(record)
        rom_out.write_bytes(rom.save())
        if state_path:
            save_state(state_path, state)
        return state

    if kind == "team_push":
        from true_patches.team_push.patch_team_push import apply_team_push_module

        record = apply_team_push_module(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            rom=rom,
            config=config,
        )
        state.upsert_module(record)
        rom_out.write_bytes(rom.save())
        if state_path:
            save_state(state_path, state)
        return state

    if kind not in ("asm", "both"):
        raise NotImplementedError(f"module kind {kind!r} not implemented yet")

    if not armips_exe.is_file():
        raise FileNotFoundError(f"armips not found: {armips_exe}")

    prior = _prior_hook_sites(state, exclude_module=module_id if force_reapply else None)
    asm_cfg = manifest.get("asm") or {}
    if asm_cfg.get("components") or asm_cfg.get("use_bundle"):
        record, rom = apply_asm_multi(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            profile=profile,
            rom=rom,
            config=config,
            armips_exe=armips_exe,
            prior_hook_sites=prior,
            rom_in=rom_in,
            state=state,
        )
    else:
        record, rom = apply_asm_single(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            profile=profile,
            rom=rom,
            config=config,
            armips_exe=armips_exe,
            prior_hook_sites=prior,
            state=state,
            rom_in=rom_in,
        )
    state.upsert_module(record)
    rom_out.write_bytes(rom.save())
    if state_path:
        save_state(state_path, state)
    return state


def verify_module_applied(
    rom_path: Path,
    module_dir: Path,
    state: BuildState | None,
) -> None:
    manifest = load_module_manifest(module_dir)
    kind = manifest.get("kind", "asm")

    if kind == "luminous_evolution":
        from .apply_luminous_evolution import verify_luminous_evolution_module

        mod_state = state.get_module(manifest["id"]) if state else None
        verify_luminous_evolution_module(rom_path, module_dir, manifest, mod_state)
        return

    if kind == "team_push":
        from true_patches.team_push.patch_team_push import verify_team_push_module

        verify_team_push_module(rom_path, module_dir)
        return

    if kind == "tm_read":
        from .apply_tm_read import verify_tm_read_module

        mod_state = state.get_module(manifest["id"]) if state else None
        profile = load_rom_profile(Path(__file__).resolve().parent, manifest.get("rom_profile", "us_vanilla"))
        verify_tm_read_module(rom_path, module_dir, manifest, profile, mod_state)
        return

    if kind == "z_move":
        from .apply_z_move import verify_z_move_module

        mod_state = state.get_module(manifest["id"]) if state else None
        profile = load_rom_profile(Path(__file__).resolve().parent, manifest.get("rom_profile", "us_vanilla"))
        verify_z_move_module(rom_path, module_dir, manifest, profile, mod_state)
        return




    if kind == "spinda_ev":
        from .apply_spinda_ev import verify_spinda_ev_module

        mod_state = state.get_module(manifest["id"]) if state else None
        profile = load_rom_profile(Path(__file__).resolve().parent, manifest.get("rom_profile", "us_vanilla"))
        verify_spinda_ev_module(rom_path, module_dir, manifest, profile, mod_state)
        return

    if kind == "berry_boost":
        from .apply_berry_boost import verify_berry_boost_module

        mod_state = state.get_module(manifest["id"]) if state else None
        verify_berry_boost_module(rom_path, module_dir, manifest, mod_state)
        return

    if kind == "korean":
        from .apply_korean import verify_korean_module

        mod_state = state.get_module(manifest["id"]) if state else None
        verify_korean_module(rom_path, module_dir, manifest, mod_state)
        return

    if kind == "balance_change":
        from .apply_balance_change import verify_balance_change_module

        mod_state = state.get_module(manifest["id"]) if state else None
        profile = load_rom_profile(Path(__file__).resolve().parent, manifest.get("rom_profile", "us_vanilla"))
        verify_balance_change_module(rom_path, manifest, profile, mod_state)
        return




    if kind == "data":

        from .apply_data import verify_data_module



        verify_data_module(rom_path, module_dir, manifest)

        return



    profile = load_rom_profile(Path(__file__).resolve().parent, manifest.get("rom_profile", "us_vanilla"))

    mod_state = state.get_module(manifest["id"]) if state else None

    verify_asm_module(rom_path, manifest, profile, mod_state)

