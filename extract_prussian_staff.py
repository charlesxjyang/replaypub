# -*- coding: utf-8 -*-
"""Extract Millotat, *Understanding the Prussian-German General Staff System* (SSI, 1992).

The PDF is a scan with an OCR text layer. Paragraphs are rebuilt from pymupdf line
geometry (indent starts a paragraph; a run of indented lines with a short right edge
is a block quote), then repaired, then split into one post per subsection.

Usage: python extract_prussian_staff.py   ->  prussian_staff_clean.json
"""

import fitz, re, sys, json, html
from collections import Counter

PDF = 'prussian_staff.pdf'
OUT = 'prussian_staff_clean.json'

d = fitz.open(PDF)

def page_lines(pno):
    raw = []
    for b in d[pno].get_text('dict')['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans'])
            if not t.strip():
                continue
            raw.append({'y': l['bbox'][1], 'x': l['bbox'][0], 'x1': l['bbox'][2],
                        'sz': max(s['size'] for s in l['spans']), 't': t.strip()})
    raw.sort(key=lambda r: r['y'])
    clusters = []
    for r in raw:
        if clusters and abs(r['y'] - clusters[-1][0]['y']) < 5.0:
            clusters[-1].append(r)
        else:
            clusters.append([r])
    out = []
    for c in clusters:
        c.sort(key=lambda r: r['x'])
        t = ' '.join(r['t'] for r in c)
        if re.fullmatch(r'[ivxlcIVXLC0-9]{1,4}', t.replace(' ', '')):
            continue
        out.append({'y': c[0]['y'], 'x': min(r['x'] for r in c),
                    'x1': max(r['x1'] for r in c),
                    'sz': max(r['sz'] for r in c), 't': t})
    return out

def blocks_for_pages(pages):
    units = []
    for pno in pages:
        lines = page_lines(pno)
        if not lines:
            continue
        xs = Counter(round(l['x']) for l in lines)
        base = min([x for x, c in xs.items() if c >= 2] or list(xs))
        right = max(l['x1'] for l in lines)
        for l in lines:
            l['ind'] = l['x'] > base + 8
            l['quote'] = l['ind'] and l['x1'] < right - 12
        # a lone indented+short line is a one-line paragraph, not a quote
        for i, l in enumerate(lines):
            if l['quote']:
                prev_q = i > 0 and lines[i-1]['quote']
                next_q = i + 1 < len(lines) and lines[i+1]['quote']
                if not prev_q and not next_q:
                    l['quote'] = False
        runs = []
        for l in lines:
            new = (not runs or runs[-1][0]['quote'] != l['quote']
                   or (not l['quote'] and l['ind']))
            if new:
                runs.append([l])
            else:
                runs[-1].append(l)
        for run in runs:
            units.append(('q' if run[0]['quote'] else 'p', run[0]['ind'], run))
    paras = []
    for kind, starts_new, run in units:
        txt = ''
        for l in run:
            if not txt:
                txt = l['t']
            elif txt.endswith('-') and not txt.endswith('--'):
                txt = txt[:-1] + l['t']
            else:
                txt += ' ' + l['t']
        if paras and paras[-1][0] == kind and not starts_new:
            prev = paras[-1][1]
            paras[-1][1] = (prev[:-1] + txt) if (prev.endswith('-') and not prev.endswith('--')) else prev + ' ' + txt
        else:
            paras.append([kind, txt])
    return [(k, re.sub(r'\s+', ' ', t).strip()) for k, t in paras]



SOURCE_URL = ('https://bootcampmilitaryfitnessinstitute.com/wp-content/uploads/2015/07/'
              '41-understanding-the-prussian-german-general-staff-system-millotat-1992.pdf')

# --- OCR repairs -----------------------------------------------------------
# Straight substitutions applied to every block.
FIXES = [
    ('admiristrative', 'administrative'),
    ('19th cenury', '19th century'),
    ('figurE!s', 'figures'),
    ('the General. Staff officers', 'the General Staff officers'),
    ('in the Bundeswehra diminution', 'in the Bundeswehr a diminution'),
    ('the WehrmachtAir Force', 'the Wehrmacht Air Force'),
    ('despite the German loss in World War I1', 'despite the German loss in World War II'),
    ('after the war."', 'after the war.'),
    ('PrussianGerman', 'Prussian-German'),
    ('at the lake Steini-ider Meer', 'at the lake Steinhuder Meer'),
    ('Frederick Wilhelm Ill', 'Frederick Wilhelm III'),
    ('there were not very many of them 42', 'there were not very many of them.'),
    ('General Stdff', 'General Staff'),
    ("matters of 'heir functional areas", 'matters of their functional areas'),
    ('officers tc use initiative', 'officers to use initiative'),
    ('laid the correrstone', 'laid the cornerstone'),
    ('Each army co-rps', 'Each army corps'),
    ('was taskad to observe', 'was tasked to observe'),
    ('Emperor Wilhelm 11.68', 'Emperor Wilhelm II.'),
    ('officers from ncn-NATO countries', 'officers from non-NATO countries'),
    ('fundamentals of sta;; work', 'fundamentals of staff work'),
    ('3-week Advanced Education fr Field Grade', '3-week Advanced Education for Field Grade'),
    ('The sy, dicates', 'The syndicates'),
    ('at the Ac3demy at he same time', 'at the Academy at the same time'),
    ('career, usualiy as senior', 'career, usually as senior'),
    ('Voluntary participation :n', 'Voluntary participation in'),
    ('(Fuehrungsakademie der Bundesweh) at Hamburg', '(Fuehrungsakademie der Bundeswehr) at Hamburg'),
    ('(Universitaetder Bundeswehr)', '(Universitaet der Bundeswehr)'),
    ('with his cosast advisers', 'with his closest advisers'),
    ('(AIlIgemeine Kriegsschule)', '(Allgemeine Kriegsschule)'),
    ("armed forces of German's allies", "armed forces of Germany's allies"),
    ('the Chiefs of Gener& Staffs', 'the Chiefs of General Staffs'),
    ('of the opinion that L he wanted', 'of the opinion that he wanted'),
    ('among other things: _ __ _ _', 'among other things:'),
    ('In the third ysar of training', 'In the third year of training'),
    ("The excesses cf Ludendorff's", "The excesses of Ludendorff's"),
    ('Every Reichwehr officer', 'Every Reichswehr officer'),
    ('shattered - II the General Staff officers', 'shattered all the General Staff officers'),
    ('Throughout World War I the German High Command suffered',
     'Throughout World War II the German High Command suffered'),
    ('increase thi quality', 'increase the quality'),
    ('ever felt thc ° authority', 'ever felt their authority'),
    ('education, training and comMand and control', 'education, training and command and control'),
    ('without any advice, olily based', 'without any advice, only based'),
    ('In this Ilght', 'In this light'),
    ('elements of the Prussan-German', 'elements of the Prussian-German'),
    ('Itis therefore recommended', 'It is therefore recommended'),
    ("jobs in the Bundeswehrare reserved", 'jobs in the Bundeswehr are reserved'),
    ('The Fuehrungsakademie der Bundeswen( training', 'The Fuehrungsakademie der Bundeswehr training'),
    ('that talented practitioners" without', 'that talented "practitioners" without'),
    ('the ever deminishing threat', 'the ever diminishing threat'),
    ('New Strategic Concept8 9', 'New Strategic Concept'),
    ('(Hoehere Adjutantu)', '(Hoehere Adjutantur)'),
    ('Ecole Sup6rieure de Guerre', 'École Supérieure de Guerre'),
    ('as attach6s', 'as attachés'),
    ('after World War Il', 'after World War II'),
    ("Reflexions sur I'art de la guerre", "Réflexions sur l'art de la guerre"),
    ("Wehrmacht's division la officer", "Wehrmacht's division Ia officer"),
    ('(ie. ‘he Chief of the General Staff', '(i.e., the Chief of the General Staff'),
    ("(ie. 'he Chief of the General Staff", '(i.e., the Chief of the General Staff'),
    ('Konigsgraetz', 'Koeniggraetz'),
    ('retained to the present day.s°', 'retained to the present day.'),
    ('given a title of nobility."s', 'given a title of nobility.'),
    ('called Moltke\'s "demigods"', 'called Moltke\'s "demigods"'),
    ('the Imperial Archives (Reichsarchiv).7', 'the Imperial Archives (Reichsarchiv).'),
    ('to bring the army back home."0', 'to bring the army back home.'),
    ('General Staff officers. 4', 'General Staff officers.'),
    ('the sciences of war .... .', 'the sciences of war....'),
    ('their reason dictates .... .', 'their reason dictates....'),
    ('Steini-ider', 'Steinhuder'),
    ('since it was established 200 years ago.8°', 'since it was established 200 years ago.'),
]

# Page 65 of the scan lost its left margin; these lines are restored from context.
P65 = [
    ('e graduate of the assignment-oriented General and Admiral aff course has not yet '
     'concluded his training and education. is only in his following assignments in units, '
     'staffs and mmands, the Federal Ministry of Defense and NATO that he molded according '
     'to his professional image. This requires',
     'The graduate of the assignment-oriented General and Admiral Staff course has not yet '
     'concluded his training and education. It is only in his following assignments in units, '
     'staffs and commands, the Federal Ministry of Defense and NATO that he is molded according '
     'to his professional image. This requires'),
    ('own initiative. He has to go through a demanding If-educational process.',
     'his own initiative. He has to go through a demanding self-educational process.'),
    ('increasingly int out the fact that quite a few young General and Admiral aft officers '
     'strive to follow certain career patterns which are signed to present as little offense '
     'as possible and to agree :h their superiors\' opinions in order to receive the best '
     'iciency reports, thus proceeding easily up the career ladder. treamlined" and adaptable '
     'General Staff officers, however, 9 inappropriate, for they are unable to fulfill their '
     'main task advising their commanders and urging them to make cisions.',
     'increasingly point out the fact that quite a few young General and Admiral Staff officers '
     'strive to follow certain career patterns which are designed to present as little offense '
     'as possible and to agree with their superiors\' opinions in order to receive the best '
     'efficiency reports, thus proceeding easily up the career ladder. "Streamlined" and adaptable '
     'General Staff officers, however, are inappropriate, for they are unable to fulfill their '
     'main task of advising their commanders and urging them to make decisions.'),
    ('Here, senior General Staff officers are required to ercise an influence on the molding '
     'and education of junior .neral Staff officers. In doing so they must also explain the '
     'rticularities of a "commander\'s adviser" to other staff officers d support the junior '
     'General Staff officers. It would be acceptable if they did not tend to this task, for '
     'otherwise 3re may be unnecessary disagreements or unrest in the Iff s.',
     'Here, senior General Staff officers are required to exercise an influence on the molding '
     'and education of junior General Staff officers. In doing so they must also explain the '
     'particularities of a "commander\'s adviser" to other staff officers and support the junior '
     'General Staff officers. It would be unacceptable if they did not tend to this task, for '
     'otherwise there may be unnecessary disagreements or unrest in the staffs.'),
    ('It is uncontested at present that the 2-year General and Imiral Staff training is '
     'indispensable. It was discussed that 3neral and Admiral Staff assignments in the Federal '
     'Armed )rces and in NATO are becoming increasingly complex, and , beyond the classic areas '
     'of responsibility in the tactical and ierational fields. The curriculum at the Command and '
     '3neral Staff Academy must take this into consideration. re than ever before it is '
     'influenced by the rapidly changing litary-political surroundings, by the developments '
     'within the united Germany, and by the daily practical cooperation in ,TO staffs as well '
     'as by joint exercises with Germany\'s allies.',
     'It is uncontested at present that the 2-year General and Admiral Staff training is '
     'indispensable. It was discussed that General and Admiral Staff assignments in the Federal '
     'Armed Forces and in NATO are becoming increasingly complex, and go beyond the classic areas '
     'of responsibility in the tactical and operational fields. The curriculum at the Command and '
     'General Staff Academy must take this into consideration. More than ever before it is '
     'influenced by the rapidly changing military-political surroundings, by the developments '
     'within the united Germany, and by the daily practical cooperation in NATO staffs as well '
     'as by joint exercises with Germany\'s allies.'),
    ('All this and the fact that an increasing number of students the General and Admiral Staff '
     'training courses have a iiversity education and are holding master\'s degrees-more an 90 '
     'percent of the course that ended in October 1989-makes',
     'All this and the fact that an increasing number of students in the General and Admiral Staff '
     'training courses have a university education and are holding master\'s degrees—more than 90 '
     'percent of the course that ended in October 1989—makes'),
]

# Figure-page OCR noise: whole blocks to drop, and noise prefixes to strip.
DROP_BLOCKS = {42, 43, 44, 48, 49, 50, 51}
PREFIX_STRIP = {
    45: 'E ac~ ma Ee ',
    52: 'CD ~ UQ 3 ',
    60: '_ ',
}
# Text mangled by the Figure 2 caption bleeding into the column.
SPECIAL = {
    59: ('This subdivision into two categories comes at the specific goal level: of the 2,200 '
         'broad-aim-oriented instructional hours, 1,000 (i.e., 45 percent), serve for '
         'joint-service-oriented training; 1 200 (i.e., .... ...... .. .....',
         'This subdivision into two categories comes at the specific goal level: of the 2,200 '
         'broad-aim-oriented instructional hours, 1,000 (i.e., 45 percent) serve for '
         'joint-service-oriented training and 1,200 (i.e., 55 percent) for single '
         'service-oriented training.'),
    60: ('55 percent), for single service-oriented training. During the entire course',
         'During the entire course'),
}

# Section headings printed in bold in the book; the extractor leaves them glued to text.
HEADINGS = [
    'Military Staff Systems Today-A Result of Historical Processes.',
    'Between Condemnation and Admiration.',
    'General Staff Officers in the Bundeswehr.',
    'Ranks of General Staff Officers and Size of the Service.',
    'Selection and Training.',
    "The General Staff Officer as the Commander's Adviser.",
    'Esprit de Corps of German General Staff Officers.',
    'Mission-Oriented Command and Control.',
    'Function Overrides Rank.',
    'Consolidation of the Prussian General Staff System.',
    'Prussian-German General Staff Under Moltke and Schlieffen.',
    'Towards Professional General Staff Training in Prussia: The Bavarian Approach.',
    'The General Staff in World War I.',
    'The General Staff After the Treaty of Versailles, 1920-33.',
    'The General Staff in the Third Reich, 1933-45.',
    'Attempts to Abolish the Bundeswehr General Staff Officer Training.',
    'Challenges.',
]

ENDNOTE = re.compile(r'(?<=[.!?\'"’”])\s?\d{1,3}(?:\s\d{1,2})?(?=\s+[A-Z"“(]|$)')

def clean(text):
    for a, b in FIXES:
        text = text.replace(a, b)
    text = ENDNOTE.sub('', text)
    text = text.replace(' .', '.').replace('  ', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def load_blocks():
    raw = blocks_for_pages(range(9, 72))
    out = []
    for i, (kind, text) in enumerate(raw):
        if i in DROP_BLOCKS:
            continue
        if i in PREFIX_STRIP and text.startswith(PREFIX_STRIP[i]):
            text = text[len(PREFIX_STRIP[i]):]
        if i in SPECIAL:
            a, b = SPECIAL[i]
            assert a in text, f'block {i} special fix did not match'
            text = text.replace(a, b)
        for a, b in P65:
            if a in text:
                text = text.replace(a, b)
        text = clean(text)
        # pull a trailing bold heading off the end of a paragraph
        head = None
        for h in HEADINGS:
            hc = clean(h)
            if text.endswith(hc) and text != hc:
                text = text[:-len(hc)].strip()
                head = hc
                break
            if text == hc:
                head, text = hc, ''
                break
        out.append({'i': i, 'kind': kind, 'text': text, 'head': head})
    return merge_split_sentence(out)


# Paragraphs the layout broke in two: a full-page figure (41/45, 59/60) or the lost
# left margin on page 65 (167/168) interrupted them mid-sentence.
MERGES = [(41, 45), (59, 60), (167, 168)]


def merge_split_sentence(blocks):
    by_i = {b['i']: b for b in blocks}
    dropped = set()
    for head_i, tail_i in MERGES:
        a, b = by_i.get(head_i), by_i.get(tail_i)
        if a and b and a['text'] and b['text']:
            a['text'] = a['text'] + ' ' + b['text']
            a['head'] = a['head'] or b['head']
            dropped.add(tail_i)
    return [x for x in blocks if x['i'] not in dropped]


# Bullet runs the column-based extractor breaks apart; rebuilt here by hand.
LISTS = {
    32: (38, [
        "The brigade is the first level where General Staff officers can be found. The G3, who "
        "is the first General Staff officer of a brigade, has the position of Chief of Staff. He "
        "may be compared to the Wehrmacht's division Ia officer, who was the first General Staff "
        "officer, functioning as the Chief of Staff. The Bundeswehr brigade is, as was the "
        "Wehrmacht division, the lowest unit level that can fight the combined arms battle. The "
        "brigade's 2nd General Staff officer is the G4. In contrast to other western armies "
        "conducting General Staff officer training, the remaining heads of staff sections of a "
        "brigade are not trained as General Staff officers.",
        "In a Bundeswehr division there are five General Staff officers: the Chief of Staff, the "
        "G1, G2, G3, and G4. Divisions with special tasks have an additional General Staff "
        "officer, a G3 Operation's Officer (Ops) who deals with operational matters. In a German "
        "Army corps, the Chief of Staff, holding Brigadier General rank, oversees nine General "
        "Staff officers: the G1, G2, G2 Ops, the G3, G3 Planning and Exercises, the G3 Ops 1 and "
        "Ops 2, the G4 and the G4 Ops. Currently, the employment of a G6 officer at division and "
        "corps level is being evaluated in troop tests. This General Staff officer is envisaged "
        "to head a newly formed command, control, and communications section.",
        "At HQ AFCENT (Allied Forces, Central Europe) in Brunssum, Netherlands, for example, "
        "there are about 100 German officers. Only 17 of them are General Staff officers.",
    ], None),
    56: (58, [
        "Army: Forty-five German and 12-15 allied NATO students organized in four syndicates or "
        "sections;",
        "Air Force: Twenty-four German and two-to-five allied NATO students;",
        "Navy: Fourteen German and four-to-six allied NATO students.",
    ],
        "The syndicates are the most important instructional group and remain unchanged "
        "throughout the entire course. They are supervised by a senior lieutenant colonel i.G., "
        "who is a faculty class adviser, and a lecturer for the major subject of the respective "
        "single service-oriented instruction. He prepares an evaluation of his syndicate students "
        "at the end of the course. All syndicates are subordinate to one course director of "
        "colonel or navy captain's rank. An Army, Air Force and Navy General Staff Course starts "
        "every year at the beginning of October. It is preceded by a 6-month intensive language "
        "course at the Federal Office of Languages (Bundessprachenamt) at Huerth. A junior and "
        "one senior course is in progress simultaneously at the Academy at the same time."),
    147: (158, [
        'The nature of command and control of the armed forces as developed in German military '
        'history was first formulated by Moltke and is described in Paragraph 601 as follows: '
        '"Command and Control of armed forces is an art, a creative activity based on character, '
        'ability and mental power."',
        'Paragraph 609 contains another credo of Moltke and his successors: Resolute action is a '
        'must in war.... Commanders who merely wait for orders cannot seize favorable '
        'opportunities. They must always keep in mind that indecision and the failure to act '
        'might be just as fatal as action based on a wrong decision.',
        "The requirements of modern leadership based on the experience of German military "
        "tradition are described in Paragraphs 616-625. Matter of course obedience, discipline "
        "and courage, mutual confidence of commanders and subordinates and the necessary "
        "comradeship between the soldiers of all ranks are postulated as the bonds of soldierly "
        "togetherness. Great emphasis is placed on the commander's unwavering care for his men. "
        "As was discussed above, mission-oriented command and control is the fundamental "
        "operating principle and rules out routine and bureaucratic command in the military "
        "community.",
        'Numerous expositions of the HDv 100/100 on the allocation of forces in the enemy\'s '
        'flanks and rear, on deployment and reconnaissance, that is to say on operations, reflect '
        'Field Marshal Count von Schlieffen\'s operational concepts. They can be read in his '
        'writings which include the concise "Cannae Essay."',
        'The German tactical principles of the types of combat go back to the regulations of the '
        'Supreme Army Command of 1917-18, which were elaborated on General Ludendorff\'s order. '
        'Examples are the "Defense in Position Warfare" and the "Attack in Position Warfare."',
        'The Army Command Regulation of 1933 HDv 300/1, "Command and Control of Armed Forces" '
        'shows many parallels to the operational and tactical views that are still valid today.',
    ], None),
}

# (title, slug, first block, last block, opening subhead or None)
SECTIONS = [
    ('Chapter 1: Introduction', 'introduction', 2, 11,
     'Military Staff Systems Today—A Result of Historical Processes'),
    ('Chapter 2: Between Condemnation and Admiration', 'between-condemnation-and-admiration', 14, 24, None),
    ('Chapter 2: General Staff Officers in the Bundeswehr', 'general-staff-officers-in-the-bundeswehr', 25, 28, None),
    ('Chapter 2: Ranks and Size of the Service', 'ranks-and-size-of-the-service', 29, 39, None),
    ('Chapter 2: Selection and Training', 'selection-and-training', 40, 63, None),
    ("Chapter 2: The Commander's Adviser", 'the-commanders-adviser', 64, 75, None),
    ('Chapter 2: Esprit de Corps, Auftragstaktik, and Function Over Rank',
     'esprit-de-corps-auftragstaktik-and-function-over-rank', 76, 80, None),
    ('Chapter 3: Scharnhorst and the Birth of the General Staff',
     'scharnhorst-and-the-birth-of-the-general-staff', 82, 94, None),
    ('Chapter 3: Gneisenau and the Consolidation of the Prussian System',
     'gneisenau-and-the-consolidation-of-the-prussian-system', 95, 100, None),
    ('Chapter 3: Moltke and Schlieffen', 'moltke-and-schlieffen', 101, 107, None),
    ('Chapter 3: Professional Training and the Bavarian Approach',
     'professional-training-and-the-bavarian-approach', 108, 117, None),
    ('Chapter 3: The General Staff in World War I', 'the-general-staff-in-world-war-i', 118, 123, None),
    ('Chapter 3: After the Treaty of Versailles, 1920-33',
     'after-the-treaty-of-versailles-1920-33', 124, 127, None),
    ('Chapter 3: The General Staff in the Third Reich, 1933-45',
     'the-general-staff-in-the-third-reich-1933-45', 128, 138, None),
    ('Chapter 4: Effects and Ways', 'effects-and-ways', 140, 159, None),
    ('Chapter 4: Attempts to Abolish General Staff Officer Training',
     'attempts-to-abolish-general-staff-officer-training', 160, 163, None),
    ('Chapter 4: Challenges', 'challenges', 164, 169, None),
    ('Chapter 5: Observations and Conclusion', 'observations-and-conclusion', 171, 178, None),
]

# Headings that land mid-section become <h2> subheads rather than section titles.
INLINE_HEADS = {96, 76, 79}


def esc(t):
    return html.escape(t, quote=False)


def render(first, last, opening_head):
    blocks = {b['i']: b for b in load_blocks()}
    parts = []
    if opening_head:
        parts.append(f'<h2>{esc(opening_head)}</h2>')
    i = first
    while i <= last:
        if i in LISTS:
            end, items, tail = LISTS[i]
            parts.append('<ul>' + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ul>')
            if tail:
                parts.append(f'<p>{esc(tail)}</p>')
            i = end + 1
            continue
        b = blocks.get(i)
        if b is None:
            i += 1
            continue
        if b['text']:
            if b['kind'] == 'q':
                parts.append(f"<blockquote><p>{esc(b['text'])}</p></blockquote>")
            else:
                parts.append(f"<p>{esc(b['text'])}</p>")
        if b['head'] and i in INLINE_HEADS:
            parts.append(f"<h2>{esc(b['head'].rstrip('.'))}</h2>")
        i += 1
    return '\n'.join(parts)


def main():
    posts = []
    for idx, (title, slug, first, last, head) in enumerate(SECTIONS, start=1):
        body = render(first, last, head)
        words = len(re.sub(r'<[^>]+>', ' ', body).split())
        posts.append({
            'title': title,
            'url': SOURCE_URL,
            'slug': slug,
            'content_html': body,
            'post_index': idx,
            'word_count': words,
            'reading_time_minutes': max(1, round(words / 250)),
        })
    with open(OUT, 'w') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    total = sum(p['word_count'] for p in posts)
    for p in posts:
        print(f"{p['post_index']:2d}  {p['word_count']:5d}w  {p['reading_time_minutes']:2d}min  {p['title']}")
    print(f"\n{len(posts)} posts, {total} words")


if __name__ == '__main__':
    main()
