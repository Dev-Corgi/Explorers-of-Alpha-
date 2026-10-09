# Alpha+ Fixed Room viewer for SkyTemple

Install with `.venv\Scripts\python.exe tools\skytemple_fixed_room_viewer\install.py`.
Restart SkyTemple, accept its plugin-loading prompt, then reopen the ROM.

For ROMs containing `BALANCE/fr_mst.bin`, the plugin loads every 12-byte stats
row from that file instead of the fixed 99-row overlay10 table. Fixed Room maps
and the entity list can then be inspected without out-of-range stats indices.
Entity/item/monster/tile/stats table cell editing is disabled and the table save
method is guarded. Existing Fixed Room layout editing is not changed.

ROMs without the mirror file use the original loader and save method.
The plugin never modifies the relocated table or the ROM on load.

Remove `%LOCALAPPDATA%\skytemple\plugins\alpha_fixed_room_viewer-1.0.0-py3-none-any.whl`
to uninstall. No SkyTemple executable or ROM rebuild is required.
