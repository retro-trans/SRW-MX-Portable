import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import textfit

BASE = Path(__file__).resolve().parents[1] / 'work/translation/en/script'
FULL = {
240: "Kazuya Ryuzaki, the man who bridged the gap between Earth and Baam... I know of you.",
241: "We can understand even people from other planets... So why must we...",
242: "The answer lies in the Federation's corruption! It should represent all humanity, so why does it seek only Earth's interests?!",
243: "Until their rule changes, we will never lower the swords we have raised!",
244: "Kyoshiro, this is reckless! You're facing the Blue Hawk of Giganos!",
245: "Be quiet, Nana! There's something I want to say to this man!",
246: "As the old saying goes, 'Man brings more misery upon man than anything else!' Those are Pliny's words!",
247: "What?!",
248: "Making people weep to set the world right is the height of folly! You ought to change your name from Hawk to Kite!",
249: "Get out of our way, Blue Hawk!!",
250: "We have to go to the Moon for Unicorn and Leo!",
251: "I do not know your circumstances, but we too have reasons why we cannot withdraw...!",
252: "If you have something at stake, then fight with every ounce of strength you possess!",
253: "You are not from Earth! Why do you side with #部隊名?!",
254: "Kenro's guidance... It means that justice lies here!",
255: "Fool! Look at the state Earth is in!",
256: "The Federation government's corruption brought about today's chaos! Giganos shall strike it with the hammer of justice!",
257: "Is that truly for the good of the world?!",
258: "A world floating on people's tears will one day sink in them! You are only creating such a world yourselves!",
259: "Hm...!",
260: "You're skilled...!",
261: "Heh... What a shame... To think someone who has strayed from the right path could possess such skill...",
262: "Silence! There is not a trace of doubt in my sword or my heart! That is the very source of my strength!",
263: "Then I too shall put my convictions into my sword and face you! Jeeet!",
264: "What you're saying may indeed not be entirely wrong...",
265: "You agree with us, then. In that case...",
266: "Hear us out! That doesn't mean that you are in the right!",
267: "As long as we stand between Giganos and the people it makes weep, we will fight!",
268: "We will use this power to protect the world, not to change it!",
269: "...Perhaps I should find out what that man truly intends...",
270: "...Char Aznable... No, Quattro Bajeena... Can you hear me?",
271: "I am Captain Meio Plato of the Giganos Imperial Guard.",
272: "...!",
273: "What is that man going to say to Captain Quattro...?!",
274: "...",
275: "If you can hear me, open a channel.",
276: "...What do you want with me?",
277: "I want an answer... Why are you there?",
278: "The ghosts of the Zabi family, who exploited Zeon Zum Deikun's ideals, should already have perished...",
279: "So why do you oppose us?",
280: "...",
281: "...Our United Empire Giganos is the sword that vanquishes evil, severing the Federation that breeds corruption...",
282: "Anyone who glimpsed humanity's evolution in that great war should surely support us.",
283: "...You are moving too quickly. Humanity needs to discern the course of the times, not undergo sudden evolution.",
284: "The course of the times, you say?",
285: "Yes. The time granted to any one person is limited.",
286: "Those who fail to understand that and try to force impossible reforms will eventually perish...",
287: "Just like Jamitov Hymen and Haman Karn.",
288: "...You say our Giganos will follow the same path?",
289: "Yes. Your hammer of justice only instills fear and hatred in people...",
290: "Those who cannot trust the next generation and try to accomplish everything within their own will instead face the hammer of justice themselves.",
291: "Are you saying that you in #部隊名 will bring that hammer down?",
292: "Exactly. Giganos's Mass Driver is no sword that vanquishes evil...",
293: "It is merely a tool that needlessly cuts down the young lives that will carry the next generation.",
294: "That is why I am here... To stop people like you.",
295: "...Char...",
296: "Then are you saying that you will become the foundation for the next generation?",
297: "Will you abandon your destiny, defy your bloodline, and let yourself be buried in the present age?",
298: "It is not old men who create a new era.",
299: "I learned that from Kamille Bidan and Judau Ashta.",
300: "!",
301: "Captain Quattro...!",
302: "Unless the wise guide the foolish, humanity and the Earth Sphere itself will perish.",
303: "You should have learned that in the One Year War and the Gryps Conflict.",
304: "Then why do you not seek a method other than the Mass Driver?",
305: "What is the point of destroying Earth's environment and causing so many people to die?",
306: "The Mass Driver was used solely to give our forces an advantage at the start of the war.",
307: "Its only purpose was to keep the Earth Federation Army in check.",
308: "As proof, Marshal Guiltorre has not authorized use of the Mass Driver since the opening of the war.",
309: "That still gives us no guarantee that you will never use it again...!",
310: "The Marshal thinks only of the Earth Sphere's future! And our purpose is not to destroy Earth's environment!",
311: "Our purpose is to purge the incompetent bureaucrats infesting our mother planet!",
312: "So you claim attacks with the Mass Driver are the necessary pain of transforming the world for a new era...!",
313: "But all you are doing is laying the groundwork for a dictatorship.",
314: "How could self-righteous reforms imposed by a handful of people ever guide people's hearts?",
315: "...!",
316: "You have turned your blades against the wrong people...!",
317: "How could a system of rule built amid chaos ever lead people toward a better future?!",
318: "...It seems that you and I are incompatible after all...!",
319: "But they hit a bit of a sore spot, didn't they?",
}

NOTES = {
241: ('The final question trails off as in the source; conflict between people of Earth is restored from row 239.', ['The unfinished final question deliberately preserves the source omission.']),
246: ('Pliny is absent from the glossary. Akurasu search found no entry; the name and thought are supported by Natural History, Book 7, https://www.attalus.org/pliny/hn7a.html . The source spells the name unusually.', ['Pliny identification is inferred from the quotation; the source spelling is unusual.']),
248: ('Preserves the bird-name insult: the Hawk is demoted to a kite.', []),
250: ('Unicorn and Leo are the source nicknames for glossary Unicorn Drill and Leo Circle.', []),
259: ('A reaction grunt is retained as a reaction, rather than supplied with a proposition.', []),
260: ('The skill being recognized belongs to Jet, as settled by the exchanged reactions in rows 259-262.', []),
263: ('The final shout uses the speaker\'s name.', []),
265: ('Meio begins an offer but is cut off by the protagonist in row 266.', ['The interrupted final clause deliberately preserves the source omission.']),
267: ('The people behind the protagonists are rendered as people the protagonists protect.', []),
268: ('The protagonists\' shared purpose continues row 267; the subject and verb are restored.', []),
269: ('That man is Quattro, named in the following row.', []),
273: ('Kamille reacts to Meio contacting Quattro; the omitted action is supplied as speaking rather than attacking.', ['The source omits the action; saying something is inferred from the surrounding radio exchange.']),
278: ('Zeon Zum Deikun and Zabi family are absent as exact glossary entries. Akurasu verifies Zeon Zum Deikun at https://akurasu.net/wiki/Char_Aznable and Zabi family at https://akurasu.net/wiki/Super_Robot_Wars/Glossary .', ['Names absent from the glossary: Zeon Zum Deikun; Zabi family.']),
281: ('Preserves the evil-banishing sword metaphor repeated in row 292.', []),
282: ('Humanity\'s evolution refers to the Newtype potential observed in the earlier war.', []),
287: ('Jamitov Hymen is absent from the glossary; Akurasu confirms the spelling at https://www.akurasu.net/wiki/SD_Gundam_G_Generation/G_Generation/Pilot_Database . Haman Karn expands the existing Haman entry.', ['Name absent from the glossary: Jamitov Hymen.']),
290: ('Preserves the reversed hammer-of-justice image and the contrast between the present and next generations.', []),
293: ('Young lives renders the source\'s budding-growth metaphor for people who will shape the future.', []),
297: ('Bloodline refers to Quattro\'s descent from Zeon Zum Deikun; the rhetorical question retains its subject.', []),
303: ('Source Gryps War is the same event as glossary Gryps Conflict.', []),
307: ('The subject refers to the Mass Driver in row 306.', []),
311: ('The omitted subject is restored as Giganos\'s purpose from row 310.', []),
}

COMPRESSED = {
290: "Those who distrust the next generation and try to do it all in their own lifetime will face the hammer of justice themselves.",
}
REVISED = {
287: "Jamitov Hymen and Haman Karn both met that fate.",
310: "The Marshal sincerely cares about the Earth Sphere's future! And our purpose is not to destroy Earth's environment!",
317: "How could a regime built by exploiting chaos ever lead people toward a better future?!",
}

def rows_for(texts):
    source = json.loads((BASE / 'stage30s.json').read_text(encoding='utf-8'))['rows']
    source = {r['id']: r for r in source if 240 <= r['id'] <= 319}
    result = []
    for row_id in range(240, 320):
        note, uncertain = NOTES.get(row_id, ('', []))
        if row_id in COMPRESSED and texts is not FULL:
            note += (' ' if note else '') + 'Compressed after the full draft exceeded the three-line box.'
        result.append(dict(id=row_id, speaker_en=source[row_id]['speaker_en'], en=texts[row_id], notes=note, uncertain=uncertain))
    return source, result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-draft', action='store_true')
    parser.add_argument('--final', action='store_true')
    parser.add_argument('--write-final', action='store_true')
    args = parser.parse_args()
    texts = {**FULL, **REVISED, **COMPRESSED} if args.final or args.write_final else FULL
    source, rows = rows_for(texts)
    bad = []
    for row in rows:
        kind = source[row['id']]['kind']
        assert kind in ('dialogue', 'thought')
        _, lines, ok = textfit.fit_dialogue(row['speaker_en'], row['en'], thought=kind == 'thought')
        if not ok:
            bad.append(row['id'])
            print(f"OVER {row['id']}: {len(lines)} lines: " + ' / '.join(f'{textfit.px(line)}px' for line in lines))
    print('Checked 80 rows; overflow:', bad)
    for row_id in [240, 246, 268, 269, 278, 290, 319]:
        row = next(row for row in rows if row['id'] == row_id)
        print(json.dumps(row, ensure_ascii=False))
    if args.write_draft:
        path = BASE / 'stage30s_codex_draft_3.json'
        if path.exists():
            raise RuntimeError('Refusing to replace preserved full draft.')
        path.write_text(json.dumps({'slice': 3, 'rows': rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.write_final:
        assert not bad, bad
        path = BASE / 'stage30s_codex_slice_3.json'
        path.write_text(json.dumps({'slice': 3, 'rows': rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
