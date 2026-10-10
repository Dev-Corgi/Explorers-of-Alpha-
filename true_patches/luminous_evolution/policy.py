"""Species relationships; executable policy shared by the linker and checks."""
from __future__ import annotations


def relationship_tables(entries, groups, overrides=None):
    n = len(entries)
    previous = [0] * n
    form_groups = [0] * 600
    form_targets = [[0] * 4]
    for group_id, group in enumerate(groups, 1):
        ids = group["ids"]
        if not 2 <= len(ids) <= 4:
            raise ValueError("Spring target selector supports 2..4 explicit forms")
        for species in ids:
            if not 0 < species < 600 or form_groups[species]:
                raise ValueError("invalid/overlapping form group")
            form_groups[species] = group_id
        form_targets.append(ids + [0] * (4 - len(ids)))
    for i, entry in enumerate(entries):
        p = int(entry.pre_evo_index)
        if not 0 < p < n or p == i or entry.sprite_index < 0:
            continue
        # The primary/female MD blocks use the same canonical species indices.
        if p < 600 and int(entry.gender) == 2 and (i >= 600 or int(entries[p].gender) == 1):
            if p + 600 < n and int(entries[p + 600].gender) == 2:
                p += 600
        if form_groups[i % 600] and form_groups[i % 600] == form_groups[p % 600]:
            continue
        # Any other cyclic chain is invalid evolution data, not regression.
        seen = {i}
        cur = p
        while 0 < cur < n and cur not in seen:
            seen.add(cur)
            cur = int(entries[cur].pre_evo_index)
        if cur in seen:
            continue
        previous[i] = p
    for species, parent in (overrides or {}).items():
        species, parent = int(species), int(parent)
        if not 0 < species < n or not 0 < parent < n or species == parent:
            raise ValueError("invalid regression override")
        previous[species] = parent
    # The native MD entry for Sunshine Cherrim has no predecessor. It shares
    # Cherubi with Overcast Cherrim; changing form must not hide regression.
    for group in groups:
        for block in (0, 600):
            ids = [i + block for i in group["ids"] if i + block < n]
            parents = {previous[i] for i in ids if previous[i]}
            if len(parents) == 1:
                parent = parents.pop()
                for i in ids:
                    if not previous[i]:
                        previous[i] = parent
    secondary = [int(int(e.gender) in (1, 2) and i+600 < n and
                     int(entries[i+600].gender) == 2)
                 for i, e in enumerate(entries[:600])]
    return previous, form_groups, form_targets, secondary
