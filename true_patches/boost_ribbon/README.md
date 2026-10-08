# boost_ribbon

Dungeon bag submenu for the listed held items.

Each item shows one line:

- Hp Up
- Atk Up
- Def Up
- SpA Up
- SpD Up

Choosing it opens the same team target menu as Ingest. After a member is picked, the bag item is removed and that member's matching stat rises by 3, the same way Protein, Iron, Calcium, Zinc, or a max-HP vitamin does in a dungeon. The leader's turn passes. Cancelling the target menu returns to the bag with the item kept. Spinda EV clears that gain when the save prompt appears.

Hooks in ov31 `ItemsMenu`: `0x02384FA0` adds action 43 to the target-menu check (with 0x12/13/14), and `0x02385068` records the leader and the chosen slot's entity, then exits through the plain-action path with a pass-turn action. Action 43 never reaches `ExecuteMonsterAction`.

The boost itself runs at `0x022FE4D8` in `ExecuteMonsterAction`, when the recorded leader's pass turn executes after the bag menu has closed. The next action clears the record either way. A message logged while the bag menu is still open leaves an empty message window behind when the menu closes.

Submenu string codes are the display string id plus 1. `Hp Up` is string 19121 and is stored as 19122.

Apply after `tm_read` and `z_move_v2`.
