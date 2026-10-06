"""Compare incremental resource edits against older PS2 regression fixtures."""
import json
from port_ps2_translations import sha

def check(base,previous,name):
 before=(previous/name).read_bytes();after=(base/name).read_bytes()
 if before==after:return
 assert name=='MAP.BIN' and (base/'weapon_battle.json').exists(),name
 change=json.loads((base/'weapon_battle.json').read_text())['map_caption']
 ranges=[]
 if (base/'map_support.json').exists():
  ranges+=json.loads((base/'map_support.json').read_text())['changed_pixel_ranges']
 a=int(change['pixel_offset'],16);ranges.append([a,a+change['bytes']])
 last=0
 for a,z in sorted(ranges):assert after[last:a]==before[last:a],(name,last,a);last=z
 assert len(after)==len(before) and after[last:]==before[last:],name
 assert sha(after)==change['target_map_sha256']
