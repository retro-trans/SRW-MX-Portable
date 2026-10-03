"""Independent slice 1 drafting and fit preview. Writes only with explicit flags."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import textfit

DRAFT = {
80: "But Dendoh chose those children.",
81: "Even if you take their place out of pity...",
82: "If that leads to this planet's destruction, those children will have no future either.",
83: "Seventeen years ago... Your arrival on Earth allowed us to prepare for Gulfer.",
84: "I will not stand by and let Earth suffer the same fate as your planet...",
85: "Yes...",
86: "Lift your head and look ahead. You cannot fight with your head hung low.",
87: "Painful as it is, that is the duty of you, Chief Shibuya and everyone at GEAR... and of #部隊名.",
88: "Always be cheerful and full of energy in front of the children.",
89: "...Our feelings take shape... If you let anxiety, fear and sorrow consume you...",
90: "The children will lose sight of their path to tomorrow, too.",
91: "Yes... Thank you.",
92: "Even if you face Altair again, you can fight without hesitation, can't you?",
93: "Then go. And do everything in your power to protect them... Those children, and this planet's future.",
94: "I will...",
95: "You certainly came home out of the blue...",
96: "I couldn't help it. They gave me time off out of the blue, too.",
97: "And tomorrow, I have to head back to the Moon.",
98: "Honestly... You leave, never get in touch, then suddenly come home. You're just like your father.",
99: "Your father...? You mean Dad?",
100: "Yes. He's probably somewhere in Spain, chasing a scoop right now.",
101: "I wonder what he'll be obsessed with when he comes home this time.",
102: "...And how about you? Are you doing all right?",
103: "Huh? What do you mean, all right...?",
104: "Isn't being a junior science trainee hard on you...?",
105: "Well... You haven't been getting into danger, have you...?",
106: "I-I'm fine! Look how full of energy I am!",
107: "Well, all right then... But things have been dangerous lately, haven't they? With Gulfer, the Hyakki Empire...",
108: "Don't worry! Dendoh and #部隊名 will beat all the bad guys!",
109: "Right, Otome?",
110: "Yeah! Go, Dendoh! Go, Dendoh!",
111: "What's this, Otome? You really like Dendoh?",
112: "I love Dendoh!",
113: "Hehe... Otome cheers for Dendoh every single day.",
114: "And of course, I do too...",
115: "Mom...",
116: "You take care of yourself, too...",
117: "...Mom... I... I, uh...",
118: "Hm? What's the matter...?",
119: "I can't...! If Mom finds out I'm Dendoh's pilot, she'll worry for sure...",
120: "...It's all right, Gin. As long as you're healthy, that's all your mom needs.",
121: "Y-yeah...",
122: "Do your best, Gin. We'll be right here at home, waiting for you.",
123: "Yeah...! Well, I... I'll be off again, then.",
124: "Gin! Don't forget to bring me a present next time!",
125: "You got it! I'll bring you a little lion, a little boar, whatever you want!",
126: "...That concludes the ground forces' report on the Earth Federation Army's large-scale operation.",
127: "Damn the Earth Federation Army... Now that they can mass-produce Metal Armors, they intend to launch a counteroffensive...",
128: "Your Excellency! They're sending one fleet after another from Earth into space!",
129: "Now is the time to order a Mass Driver strike against the Earth Federation Army's bases!",
130: "Lieutenant Colonel Dorchenov. As I said before, I intend to use the Mass Driver only as a show of force.",
131: "But Your Excellency! Enemy forces are driving our army back on every front!",
132: "At this rate, it won't be long before they advance all the way to the Moon!",
133: "Then meet them in battle. With Giganos's iron unity, defend our lunar headquarters to the last!",
134: "Exactly, Your Excellency! That is why we must...",
135: "Enough. Do not make me repeat myself.",
136: "...",
137: "...Lieutenant Colonel, the Federation's special robot unit also seems to be heading for the Moon.",
138: "The unit called #部隊名 mentioned in the report?",
139: "Yes, sir. We believe they will likely form the core of this counteroffensive.",
140: "If we can strike them before the operation begins, we may sap the Federation's fighting spirit.",
141: "At the very least, if we can hold them up, events should turn in our favor...",
142: "Very well... Deploy an attack force. Captain Plato, I entrust you with command.",
143: "Yes, sir...!",
144: "Grr... Damn you, Meio Plato... Trying to look clever in front of His Excellency...!",
145: "And His Excellency is no better...! If this keeps up, Giganos will...!",
146: "We've cleared the atmosphere. Setting course for the Moon.",
147: "...It's almost time to begin Operation Moonraker.",
148: "Yes...",
149: "Giganos forces must be keeping a close eye on our movements. All hands, Level 2 battle stations...",
150: "Captain! Giganos Metal Armors are approaching!!",
151: "1. Nadesico reaches the destination within 7 turns",
152: "1. An allied mothership is shot down@2. Nadesico fails to reach the destination within 7 turns",
153: "Giganos Metal Armor units are entering the area!",
154: "Heh! They just keep coming!",
155: "Damn it! We don't have time to deal with these guys!",
156: "We're serving as a decoy anyway... I suppose it can't be helped.",
157: "Right. If the enemy focuses on us, the other fleets will have an easier time advancing into lunar space.",
158: "B-but...!",
159: "Ginga, rescuing Unicorn and Leo won't mean our job is over.",
}

# Corrections to the full draft before any width-driven compression.
DRAFT[99] = "You mean... Dad?"

NOTES = {
81: "Preserved the open conditional continued in row 82; taking the children's place is motivated by pity.",
87: "GEAR duty includes Orie, Chief Shibuya and their colleagues; preserved squad placeholder.",
90: "Ignored stray closing quote and trailing line marker in the source.",
94: "Restored Orie's promise as 'I will'; its object is the protection ordered in row 93.",
98: "Named Ginga's father in the comparison; row 99 confirms the referent.",
101: "Treated 'be colored by' as taking on a new obsession or influence after traveling.",
104: "Junior science trainee is Ginga's cover story; kept a descriptive job label.",
112: "Restored the object Dendoh, established in row 111.",
114: "Restored Midori's subject and verb; she too cheers for Dendoh.",
117: "Preserved Ginga's interrupted attempt to confess; the thought in row 119 explains it.",
120: "Gin is Midori's source nickname for Ginga.",
122: "'We' refers to Midori and the family waiting at home.",
124: "Gin is Otome's familiar address to her older brother; dropped sibling honorific.",
125: "The playful lion and boar language alludes to the Data Weapons; left it childlike.",
129: "Restored Dorchenov's request for Guiltorre to order the strike.",
134: "Preserved Dorchenov's interrupted request; Guiltorre cuts him off in row 135.",
137: "Special robot unit translates the force category without assuming a specific machine type.",
138: "Preserved squad placeholder at runtime width.",
142: "Used Captain Plato from the glossary's full name Meio Plato.",
145: "Ignored stray closing thought delimiter and trailing line marker; retained interrupted prediction.",
147: "Operation Moonraker checked against Akurasu MX Flow Chart; term is absent from local glossary.",
151: "Plain objective: preserved one source line; checked against conservative 352 px per-line limit.",
152: "Plain defeat conditions: preserved two source lines; checked against conservative 352 px per-line limit.",
158: "Preserved the interrupted objection as in the source.",
159: "Unicorn and Leo are the source's shortened forms of Unicorn Drill and Leo Circle.",
}
UNCERTAIN = {
89: ["Rendered the literal idea 'feelings take form' as 'our feelings take shape'; the following warning concerns their effect on the children."],
101: ["The travel-related idiom may refer to cultural affectations rather than an obsession; no specific new influence is named."],
134: ["The source intentionally leaves Dorchenov's request unfinished; the proposed Mass Driver strike is established by row 129."],
117: ["The source intentionally leaves Ginga's attempted confession unfinished."],
137: ["The category 'special robot unit' is descriptive; its exact English institutional label is not supplied by the glossary."],
145: ["The source intentionally leaves the consequence for Giganos unfinished."],
147: ["Operation Moonraker is not in the local glossary; Akurasu MX Flow Chart verifies the spelling."],
158: ["The source intentionally omits the rest of Ginga's interrupted objection."],
}

FINAL_OVERRIDES = {
    152: "1. An allied mothership is shot down@2. Nadesico fails to reach the destination in 7 turns",
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save-draft', action='store_true')
    parser.add_argument('--write-final', action='store_true')
    args = parser.parse_args()
    source = json.loads((ROOT / 'work/translation/en/script/stage30s.json').read_text(encoding='utf-8'))['rows']
    rows = [r for r in source if 80 <= r['id'] <= 159]
    output = []
    failures = []
    for row in rows:
        rid = row['id']
        en = FINAL_OVERRIDES.get(rid, DRAFT[rid])
        if row['kind'] == 'plain':
            widths = [textfit.px(line) for line in en.split('@')]
            ok = len(en.split('@')) == len(row['body_jp'].split('@')) and all(w <= 352 for w in widths)
            print(f'PLAIN {rid}: {widths} {"FITS" if ok else "OVER"} | {en}')
        else:
            _, lines, ok = textfit.fit_dialogue(row['speaker_en'], en, thought=row['kind'] == 'thought')
            widths = [textfit.px(line) for line in lines]
            if not ok: print(f'OVER {rid}: {len(lines)} lines {widths} | {en}')
        if not ok: failures.append(rid)
        notes = NOTES.get(rid, '')
        if rid in FINAL_OVERRIDES:
            notes += (' ' if notes else '') + 'Compressed after the full draft exceeded the measured box limit.'
        output.append(dict(id=rid, speaker_en=row['speaker_en'], en=en, notes=notes, uncertain=UNCERTAIN.get(rid, [])))
    print('rows:',len(output),'overflow:',failures,'compressed:',sorted(FINAL_OVERRIDES))
    print('PREVIEW SAMPLES',json.dumps([output[0],output[19],output[67],output[-1]],ensure_ascii=False))
    folder = ROOT / 'work/translation/en/script'
    if args.save_draft:
        draft = [dict(o, en=DRAFT[o['id']], notes=NOTES.get(o['id'],'')) for o in output]
        (folder / 'stage30s_codex_draft_1.json').write_text(json.dumps({'slice':1,'rows':draft},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.write_final:
        (folder / 'stage30s_codex_slice_1.json').write_text(json.dumps({'slice':1,'rows':output},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__ == '__main__':
    main()
