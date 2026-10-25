# English logos, copyright and production cards — v0.4.47

The user supplied a Portable title screenshot, copyright page, opening
production card, and SRW 30 logo as the lettering reference. The built-in
image-generation tool produced two transparent logo masters: an English
Portable variant and a PS2 variant without the Portable badge. Prompts and
asset roles are recorded in `work/ui/title_credits_0.4.47/prompts.en.json`.
Native image assembly, palette compilation and movie encoding are deterministic.

`tools/mx_branding.py` compiles the PSP OPWND TX48 #44 logo into its existing
256-color palette. `tools/title_footer.py` reconstructs this English base for
versions starting at .47, retaining exact old-logo reconstruction for previous
versions. New footer stamps cannot silently restore the Japanese logo.
The English story-title backgrounds use IM_ADD offset 0x15b9000 and PS2 IM
offset 0x298f000. The PS2 native footer remains an executable draw callback.

Copyright pages are PSP IM_ADD 0x150c800 and PS2 IM 0x282e800. All thirteen
attribution lines remain, including PSP 2005 and PS2 2004. The names follow
the source credits; company English forms are cross-checked against the
[official Jupiter SRW copyright list](https://www.jupiter.co.jp/e/product/game/gb/suparobo.php).
Chimi Moriwo is a transliteration of the credited pen name; the attribution
is retained rather than replaced by a different author name. Committee names
and Yutaka Izubuchi are translated/transliterated from the original image.

The reported production card is part of the credited opening, not the staff
roll: PSP MOVIE entry29, PS2 STRM entry1. Their corresponding uncredited
entries30/3 supply the same clean robot montage. Only the final bounded video
tail is replaced with English text; preceding credits remain as authored.
The title-intro logos are separate PSP entry31 and PS2 entry2, so updating
only a static texture would have left the animated introductions Japanese.

`tools/localize_mx_movies.py` recompiles only the needed H.264/MPEG-2 access
units, fitting every replacement into its original elementary-byte budget.
Standard filler data uses the spare bytes. PES headers, timestamps, private
streams, audio and archive offsets remain unchanged. Original GOP timecodes,
picture types and temporal references are preserved on PS2; its two leading
B pictures are retained with compatible sequence flags. Title transitions use
a clean native mountain frame and the new logo, retaining the opening shot
and final white transition; logo/fade animation artwork is intentionally revised.

`tools/verify_mx_movies.py` verifies all non-video bytes, compressed prefixes,
full decoding, dimensions, profile, frame count and native start/end timing.
There is one duplicated DTS in the original PSP opening. Only the discarded
decode-test output is retimed to suppress its existing mux warning; the game
packets are unchanged. Movie playback in PPSSPP/PCSX2 and hardware is pending.

`tools/build_mx_branding.py` builds PSP over local .42 and PS2 over local .46,
protecting complete source/output hashes, file positions and all unrelated
disc bytes. Both filesystem views of changed PS2 resources are checked.
The .46 Objectives fix was subsequently confirmed by the user as working great.

English masters, native palettes/previews, copyright previews and encoded-movie
frame previews are in `work/ui/title_credits_0.4.47/`. Game movie binaries stay
ignored under `work/build/`; `ensure_movies()` can regenerate them from the
user's original discs. Both full platform builders and the reviewed PS2
builder retain these changes for subsequent releases.
