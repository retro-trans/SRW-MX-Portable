"""Encode English for the game and fit it into the dialogue box (VWF-aware).

Dialogue box: drawString at font size 16, fixed advance 16 px for Japanese glyphs; patched Latin
glyphs advance round((W*16+9)/18) px (see vwf_patch.py). Usable line width 352 px (22 Japanese
characters), at most 3 lines per message. Line 1 also holds the speaker prefix "Name「".
Lines 2-3 start with one full-width space, like the Japanese script. '@' = new line.

Placeholders expand at runtime; their width is counted as PLACEHOLDER_PX.

usage:
  python textfit.py "Speaker" "English text"          -> prints wrapped lines + pixel widths
  python textfit.py --check file.json                   -> checks a translation file
"""
import json, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LINE_PX = 352
MAX_LINES = 3
SIZE = 16
INDENT = '　'
# runtime placeholders: nickname (max 5 chars), full name (max 9), squad / unit name (max 8)
PLACEHOLDER_PX = {'#男愛称': 5 * 16, '#女愛称': 5 * 16, '#男姓名': 9 * 16, '#女姓名': 9 * 16,
                  '#部隊名': 8 * 16, '#機体名': 8 * 16}

ASCII = {' ': 0x8140, ',': 0x8143, '.': 0x8144, ':': 0x8146, ';': 0x8147, '?': 0x8148, '!': 0x8149,
         '/': 0x815E, '~': 0x8160, "'": 0x8166, '(': 0x8169, ')': 0x816A, '[': 0x816D, ']': 0x816E,
         '+': 0x817B, '-': 0x817C, '=': 0x8181, '$': 0x8190, '%': 0x8193, '&': 0x8195, '*': 0x8196}
for i in range(26):
    ASCII[chr(65 + i)] = 0x8260 + i
    ASCII[chr(97 + i)] = 0x8281 + i
for i in range(10):
    ASCII[chr(48 + i)] = 0x824F + i
QUOTE_OPEN, QUOTE_CLOSE = 0x8167, 0x8168

_W = None


def _widths():
    global _W
    if _W is None:
        import vwf_patch
        static2 = os.environ.get('SRW_STATIC2', os.path.join(os.path.dirname(__file__), '..', 'work', 'build', 'STATIC2_ADD.BIN'))
        tab = vwf_patch.width_table(static2)
        _W = {}
        for code in list(ASCII.values()) + [QUOTE_OPEN, QUOTE_CLOSE]:
            v = code - 0x8140
            e = tab[v - (v >> 8) * 64]
            _W[code] = ((e & 31) * SIZE + 9) // 18 if e & 31 else SIZE
    return _W


def tokens(text):
    """Split into drawable tokens: placeholders, ascii chars, other (Japanese) chars."""
    out, i, q = [], 0, False
    while i < len(text):
        ph = next((p for p in PLACEHOLDER_PX if text.startswith(p, i)), None)
        if ph:
            out.append(ph)
            i += len(ph)
            continue
        c = text[i]
        if c == '"':
            out.append(('"', QUOTE_CLOSE if q else QUOTE_OPEN))
            q = not q
        else:
            out.append(c)
        i += 1
    return out


def tok_px(t):
    W = _widths()
    if isinstance(t, tuple):
        return W[t[1]]
    if t in PLACEHOLDER_PX:
        return PLACEHOLDER_PX[t]
    if t in ASCII:
        return W[ASCII[t]]
    return SIZE                      # Japanese / other full-width glyph


def px(text):
    return sum(tok_px(t) for t in tokens(text))


def encode(text):
    """English (ASCII + allowed Japanese/placeholders) -> Shift-JIS bytes for the game."""
    b = bytearray()
    for t in tokens(text):
        if isinstance(t, tuple):
            b += t[1].to_bytes(2, 'big')
        elif t in PLACEHOLDER_PX or t == '@':
            b += t.encode('cp932')
        elif t in ASCII:
            b += ASCII[t].to_bytes(2, 'big')
        else:
            b += t.encode('cp932')
    return bytes(b)


def wrap(prefix, body, suffix='', line_px=LINE_PX, indent=INDENT):
    """Greedy word wrap. prefix ('Hugo「') sits on line 1, suffix ('」') must fit on the last line.
    indent starts every continuation line (the dialogue box indents; help and narration use '').
    Returns (lines, ok)."""
    words = body.replace('\n', ' ').split(' ')
    lines, cur = [], prefix
    for w in words:
        if not w:
            continue
        cand = (cur + ' ' + w) if cur not in (prefix, indent) else cur + w
        if px(cand) <= line_px:
            cur = cand
        else:
            lines.append(cur)
            cur = indent + w
    cur += suffix
    if px(cur) > line_px:
        # move the last word down so the closing bracket fits
        head, _, last = cur.rpartition(' ')
        if head and head not in (prefix, indent):
            lines.append(head)
            cur = indent + last
    lines.append(cur)
    ok = len(lines) <= MAX_LINES and all(px(l) <= line_px for l in lines)
    return lines, ok


def fit_dialogue(speaker, body, thought=False):
    o, c = ('（', '）') if thought else ('「', '」')
    lines, ok = wrap(speaker + o, body, c)
    return '@'.join(lines), lines, ok


if __name__ == '__main__':
    if sys.argv[1] == '--check':
        rows = json.load(open(sys.argv[2], encoding='utf-8'))
        bad = 0
        for r in rows if isinstance(rows, list) else rows['rows']:
            if not r.get('en'):
                continue
            _, lines, ok = fit_dialogue(r.get('speaker_en', ''), r['en'], r.get('thought', False))
            if not ok:
                bad += 1
                print(f"OVER {r.get('id')}: {len(lines)} lines | " + ' / '.join(f'{px(l)}px' for l in lines))
        print('overflowing rows:', bad)
    else:
        spk, body = sys.argv[1], sys.argv[2]
        s, lines, ok = fit_dialogue(spk, body)
        for l in lines:
            print(f'{px(l):4d}px | {l}')
        print('FITS' if ok else f'DOES NOT FIT ({len(lines)} lines, max {MAX_LINES}, {LINE_PX}px each)')
