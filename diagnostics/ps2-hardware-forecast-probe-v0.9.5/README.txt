PS2 player forecast test v0.9.5

Apply this bare xdelta to a copy of the English PS2 v0.9.0 ISO.
Source SHA-256: f2a7b452d5feecc7dd784d94d332842cb0ddb0160f8e62474a3d92dca0a3faee
Output SHA-256: 5350c5616060c4ab702a47776b50726311a8421d43e1d44707036f6c7f87e0d8
Title footer: v0.9.5 and github.com/retro-trans

This build includes the v0.9.4 changes and fixes the Attack and
No Counter copies in the forecast's action row. PCSX2 logged a
repeated unaligned read of Attack after the player confirmed
Medius Locus on public v0.9.0. Physical PS2 testing is pending.

Repeat the player-initiated attack on your usual PS2 and loader.
Please report whether the weapon list opens, confirming the target
opens the forecast, and Start Battle completes and returns to the map.

PCSX2 2.8.2 EE interpreter replay: the candidate opened the forecast,
played Bloody Ray and Divided Rifle, and returned to the map.
The interpreter reported zero instances of the public build's
unaligned Attack read during this replay.
