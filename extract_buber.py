# -*- coding: utf-8 -*-
"""Extract Martin Buber, *I and Thou* (tr. Ronald Gregor Smith, T. & T. Clark, 1937).

The PDF (buber_i_and_thou.pdf, from burmalibrary.org) is a scan whose embedded ABBYY
text layer is badly garbled, so every page is re-OCR'd with Apple's Vision framework
(ocrmac), with tesseract as a second opinion.  Line geometry from Vision rebuilds the
structure: a first-line indent starts a paragraph; Buber's centred star (seen by either
engine, or inferred from a vertical gap) separates sections.  Sections are grouped into
short posts.

Usage: python extract_buber.py [--audit]   ->  buber_clean.json
"""

import json, os, re, sys, html, difflib
from collections import Counter

PDF = 'buber_i_and_thou.pdf'
OCR_CACHE = 'buber_ocr_vision.json'      # Apple Vision lines with geometry
TESS_CACHE = 'buber_ocr_tess.json'       # tesseract --psm 6 text per page
OUT = 'buber_clean.json'
SOURCE_URL = 'https://www.burmalibrary.org/docs21/Buber-c1923-I_And_Thou-ocr-tu.pdf'

PARTS = [('Part One', range(11, 43)), ('Part Two', range(44, 80)), ('Part Three', range(81, 127))]
EPIGRAPH_PAGE = 9
AUDIT = '--audit' in sys.argv
audit_log = []
def audit(kind, msg):
    if AUDIT:
        audit_log.append((kind, msg))

# ---------------------------------------------------------------- OCR (cached)
def ocr_all():
    if os.path.exists(OCR_CACHE) and os.path.exists(TESS_CACHE):
        return ({int(k): v for k, v in json.load(open(OCR_CACHE)).items()},
                {int(k): v for k, v in json.load(open(TESS_CACHE)).items()})
    import fitz, tempfile, subprocess
    from ocrmac import ocrmac
    d = fitz.open(PDF)
    vis, tess = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(len(d)):
            p = f'{tmp}/p{i:03d}.png'
            d[i].get_pixmap(dpi=300).save(p)
            res = ocrmac.OCR(p, recognition_level='accurate', language_preference=['en-US']).recognize()
            vis[i] = [{'t': t, 'c': c, 'x': b[0], 'y': b[1], 'w': b[2], 'h': b[3]} for t, c, b in res]
            tess[i] = subprocess.run(['tesseract', p, '-', '--psm', '6'], capture_output=True, text=True).stdout
    json.dump(vis, open(OCR_CACHE, 'w'), ensure_ascii=False)
    json.dump(tess, open(TESS_CACHE, 'w'), ensure_ascii=False)
    return vis, tess

VIS, TESS = ocr_all()

# ---------------------------------------------------------------- dictionary
WORDS = set(w.strip().lower() for w in open('/usr/share/dict/words'))
WORDS |= {'thou', 'thee', 'thy', 'thine', 'brahmana', 'upanishad', 'buddha', 'buddhist', 'upanishads',
          'tao', 'jesus', 'socrates', 'goethe', 'napoleon', 'daimonic', 'daimon', 'moloch', 'incubus',
          'dionysus', 'sinai', 'mystics', 'mystic', 'eros', 'saith', 'kingdom', 'zarathustra', 'vedanta',
          'nirvana', 'atman', 'brahman', 'devas', 'asuras', 'prajapati', 'ur', 'lama', 'realised',
          'realise', 'realises', 'fulfilment', 'fulfil', 'fulfils', 'fulfilled', 'colour', 'centre',
          'ageing', 'tremendum', 'mysterium', 'numinous', 'yea', 'nay', 'whither', 'whence', 'wherein',
          'therein', 'thereby', 'hereby', 'nought', 'connexion', 'connexions', 'reflexion', 'ecstasy',
          'ecstasies', 'sistine', 'pathos', 'ethos', 'cf', 'hitherto', 'hallowed', 'hallow', 'hallows',
          'unhallowed', 'unrealised', 'unreal', 'confronter', 'twofold', 'threefold', 'manifold',
          'eternally', 'primal', 'undivided', 'ungraspable', 'uncanny', 'sunk', 'grown', 'unfolding',
          'priori', 'fulness', 'spectre', 'centreless', 'offence', 'practise', 'practises', 'esthetic',
          'apostacy', 'houselike', 'kant', 'nietzsche', 'greece', 'became', 'forsook', 'prajapati',
          'sandilya', 'eckehardt', 'colui', 'voi', 'ella', 'paradiso', 'vita', 'nuova', 'simeon', 'dike',
          'karma', 'charis', 'dynamis', 'papyri', 'cognosco', 'ergo', 'sum', 'coincidentia', 'oppositorum',
          'valore', 'metacosmic', 'metacosmical', 'presentness', 'actualised', 'characterisations',
          'utilisation', 'realisation', 'organisation', 'civilisation', 'individualities', 'exclusiveness',
          'relational', 'supersensuous', 'heaven-storming', 'garret-window', 'break-through', 'holies',
          'peter', 'napoleon', 'jews', 'jewish', 'christ', 'christianity', 'egyptian', 'greek', 'brahmana',
          'goethe', 'nirvana', 'buddha', 'hail'}
def ok(w):
    c = re.sub(r"[^a-z'-]", '', w.lower()).strip("'-")
    if not c or len(c) == 1:
        return True
    if c in WORDS:
        return True
    for suf, stems in (('s', 1), ('es', 2), ('ed', 2), ('d', 1), ('ing', 3), ('ly', 2), ('ness', 4), ('er', 2), ('est', 3)):
        if c.endswith(suf):
            s = c[:-stems]
            if s in WORDS or s + 'e' in WORDS or (len(s) > 2 and s[-1] == s[-2] and s[:-1] in WORDS):
                return True
    for suf, rep in (('ies', 'y'), ('ied', 'y'), ('ier', 'y'), ('iest', 'y'), ('ise', 'ize'), ('ised', 'ized'),
                     ('ises', 'izes'), ('ising', 'izing'), ('isation', 'ization'), ('our', 'or'), ('ours', 'ors'),
                     ('ouring', 'oring'), ('oured', 'ored'), ('re', 'er'), ('ment', ''), ('ments', '')):
        if c.endswith(suf) and (c[:-len(suf)] + rep) in WORDS:
            return True
    if c.startswith('un') and (c[2:] in WORDS or ok(c[2:])):
        return True
    if '-' in c and all(ok(p) for p in c.split('-')):
        return True
    return False

def toks(s):
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", s)

# ---------------------------------------------------------------- per-page lines
STAR_GLYPHS = {'*', '★', '☆', '•', '+', 'x', 'X', 'k', '*.', '.*', '·', '^', '&', '#'}

def vision_lines(pno):
    """Vision boxes -> visual lines (y-clustered, x-sorted), page numbers stripped."""
    raw = sorted(VIS[pno], key=lambda l: -l['y'])          # Vision y is bottom-up
    clusters = []
    for r in raw:
        if clusters and abs(r['y'] - clusters[-1][0]['y']) < 0.012:
            clusters[-1].append(r)
        else:
            clusters.append([r])
    lines = []
    for c in clusters:
        c.sort(key=lambda r: r['x'])
        t = ' '.join(r['t'] for r in c).strip()
        x, y = min(r['x'] for r in c), c[0]['y']
        w = max(r['x'] + r['w'] for r in c) - x
        if y < 0.10 and (re.fullmatch(r"([A-Z]\s+)?[0-9ivx]{1,3}['.°]?", t) or 'PRINTED' in t or 'GIBB' in t):
            continue
        star = 'glyph' if (t in STAR_GLYPHS or (w < 0.07 and len(t) <= 2 and 0.4 < x < 0.55)) else None
        lines.append({'t': t, 'x': x, 'y': y, 'w': w, 'star': star})
    return lines

def tess_star_anchors(pno):
    """Text of the tesseract line preceding each star-like line ('' = star at page top)."""
    anchors, prev = [], ''
    for l in TESS[pno].splitlines():
        l = l.strip()
        if not l:
            continue
        if re.fullmatch(r"[^\w\s]{0,2}[*xX#★][^\w\s]{0,2}", l) or l in ('k', 'A'):
            anchors.append(prev)
        elif not (len(l) <= 3 and re.fullmatch(r"[0-9]+['°]?", l)):
            prev = l
    return anchors

def correct_line_texts(pno, lines):
    """Fix Vision misreads using tesseract where the dictionary agrees with tesseract."""
    vt = toks(' '.join(l['t'] for l in lines))
    tt = toks(TESS[pno])
    sm = difflib.SequenceMatcher(a=[w.lower() for w in vt], b=[w.lower() for w in tt], autojunk=False)
    subs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'replace':
            continue
        v, t = vt[i1:i2], tt[j1:j2]
        if len(v) == 1 and len(t) == 2 and v[0].lower() == (t[0] + '-' + t[1]).lower() and ok(t[0]) and ok(t[1]):
            subs.append((v[0], t[0] + '—' + t[1], 'dash'))      # hyphen standing in for an em dash
        elif len(v) == len(t):
            for a, b in zip(v, t):
                if a.lower() == b.lower() or ok(a) or not ok(b):
                    continue
                r = difflib.SequenceMatcher(a=a.lower(), b=b.lower()).ratio()
                if r >= 0.7 and abs(len(a) - len(b)) <= 2:
                    subs.append((a, b, 'word'))
    for a, b, kind in subs:
        for l in lines:
            new = re.sub(r'(?<![\w-])' + re.escape(a) + r'(?![\w-])', b, l['t'])
            if new != l['t']:
                audit('fix-' + kind, f'p{pno} {a!r} -> {b!r}')
                l['t'] = new
    return lines

def page_units(pno):
    """-> [('star', source)] | [('line', text, starts_paragraph)]"""
    lines = correct_line_texts(pno, vision_lines(pno))
    body = [l for l in lines if not l['star']]
    xs = Counter(round(l['x'], 2) for l in body)
    base = min([x for x, n in xs.items() if n >= 2] or list(xs) or [0.11])
    # tesseract-seen stars: attach to the best-matching Vision line
    top_star = False
    for anchor in tess_star_anchors(pno):
        if not anchor:
            top_star = True
            continue
        best = max(body, key=lambda l: difflib.SequenceMatcher(a=anchor.lower(), b=l['t'].lower()).ratio())
        if difflib.SequenceMatcher(a=anchor.lower(), b=best['t'].lower()).ratio() > 0.5:
            best['tess_star_after'] = True
    units = [('star', 'tess')] if top_star else []
    prev_y = None
    for i, l in enumerate(body):
        nb = [b['x'] for b in body[max(0, i - 2):i] + body[i + 1:i + 3]]
        l['ind'] = l['x'] > (min(nb) if nb else base) + 0.02 and l['x'] > base + 0.015
    for l in lines:
        if l['star']:
            units.append(('star', 'glyph'))
            prev_y = l['y']
            continue
        if prev_y is not None and (prev_y - l['y']) > 0.055 and units[-1][0] != 'star':
            units.append(('star', 'gap'))
        units.append(('line', l['t'], l['ind']))
        if l.get('tess_star_after'):
            units.append(('star', 'tess'))
        prev_y = l['y']
    return units

# ---------------------------------------------------------------- hyphenation
def join_hyphen(a, b, pno):
    m = re.search(r'(\S+)-$', a)
    n = re.match(r'(\S+)', b)
    if not m or not n:
        return a + b
    head, tail = m.group(1), n.group(1)
    core = re.sub(r'[^A-Za-z]', '', head + tail).lower()
    if core in WORDS or ok(core):
        return a[:-1] + b
    audit('hyphen-kept', f'p{pno} {head}-{tail}')
    return a + b

END = re.compile(r'[.!?"”’\')][-—]?\s*$')

def build_sections(pages):
    """-> list of sections; a section is a list of paragraph strings."""
    sections, para, sec = [], [], []
    def flush_para():
        nonlocal para
        if para:
            sec.append(re.sub(r'\s+', ' ', para[0]).strip())
        para = []
    for pno in pages:
        for u in page_units(pno):
            if u[0] == 'star':
                if u[1] != 'glyph' and para and not END.search(para[0]):
                    audit('break-rejected', f'p{pno} {u[1]} after: ...{para[0][-60:]}')
                    continue
                flush_para()
                if sec:
                    audit('break', f'p{pno} {u[1]:5s} after: ...{sec[-1][-50:]}')
                    sections.append(sec)
                sec = []
                continue
            _, t, new = u
            if new and para and para[0].endswith('-') and not para[0].endswith('—'):
                new = False
            if new and para and t[:1].islower() and not END.search(para[0]):
                audit('para-joined', f'p{pno} ...{para[0][-40:]} | {t[:40]}')
                new = False
            if new:
                flush_para()
            if not para:
                para = [t]
            elif para[0].endswith('-') and not para[0].endswith('—'):
                para[0] = join_hyphen(para[0], t, pno)
            else:
                para[0] += ' ' + t
    flush_para()
    if sec:
        sections.append(sec)
    return sections


# ---------------------------------------------------------------- hand repairs
# Literal fixes for what the two OCR engines and the dictionary could not settle
# (audited against the page images where the reading was unclear).
FIXES = [
    ('oneand the same', 'one and the same'), ('speaker hae no thing', 'speaker has no thing'),
    ('every means hae collapsed', 'every means has collapsed'), ('He extracte knowledge', 'He extracts knowledge'),
    ('the eternal Thor.', 'the eternal Thou.'), ('I say Thore. : All real living', 'I say Thou. All real living'),
    ('ite colours', 'its colours'), ('out of ite own richness', 'out of its own richness'),
    ('none ofite zealous', 'none of its zealous'), ('is ita joy', 'is its joy'), ('ita exclusiveness', 'its exclusiveness'),
    ('only ia a different way', 'only in a different way'), ('matter ia not of evil', 'matter is not of evil'),
    ('of relation ia the greater', 'of relation is the greater'), ('In ihe act of experience', 'In the act of experience'),
    ('FoI Thou is more', 'For Thou is more'), ('it breaka me', 'it breaks me'), ('oI can become so', 'or can become so'),
    ('wishing him well oI assuring', 'wishing him well or assuring'), ('sleeping OI waking', 'sleeping or waking'),
    ('a too! oi a toy', 'a tool or a toy'), ('I see you", oI, "', 'I see you", or, "'),
    ('special being oI, rather', 'special being or, rather'), ('nothing but objecte.', 'nothing but objects.'),
    ('life of objecte is', 'life of objects is'), ('necesary being', 'necessary being'),
    ("I'hou may truly", 'Thou may truly'), ("endless I'hou, had", 'endless Thou, had'),
    ("silence before the I'how silence", 'silence before the Thou—silence'), ("leaves the I'rou free", 'leaves the Thou free'),
    ("binds up the I'nou in", 'binds up the Thou in'), ('mixture of Ihou and It', 'mixture of Thou and It'),
    ('no longer Fhou,', 'no longer Thou,'), ("I'he prima condition", 'The primal condition'), ("I'bus, too,", 'Thus, too,'),
    ('depraved.. Idea', 'depraved. Idea'), ('effect,through', 'effect, through'), ('come upon bein g.', 'come upon being.'),
    ('My Thou attecta me', 'My Thou affects me'), ('simultaneoualy', 'simultaneously'),
    ('butterily-except', 'butterfly—except'), ('pIe-gram-matical', 'pre-grammatical'), ('worn-ont formulas', 'worn-out formulas'),
    ('incidents—ex-perience', 'incidents—experience'), ('aIe set by', 'are set by'), ('nor aie tre able', 'nor are we able'),
    ('that tre do not have', 'that we do not have'), ('it-perhape in', 'it—perhaps in'), ('this buzan power', 'this human power'),
    ('fróm which', 'from which'), ('fióm which', 'from which'), ('cogrosco', 'cognosco'), ('prímitive', 'primitive'),
    ('The "I" ouergoa round', 'The "I" emerges round'), ('mytbical', 'mythical'),
    ('виррове who see in the spirit..confusing', 'suppose who see in the spirit—confusing'),
    ('Creațion', 'Creation'), ('To mạn the', 'To man the'), ('přesent', 'present'), ('rémotely', 'remotely'),
    ('autbéntic', 'authentic'), ('yousay Thouto itand give', 'you say Thou to it and give'), ('Jou cannot make', 'You cannot make'),
    ('Jou speak of', 'You speak of'), ('being Jou come', 'being you come'), ('make Yourself " understood "', 'make yourself " understood "'),
    ('as befite modern', 'as befits modern'), ('institutions kaow only', 'institutions know only'), ('status byit,', 'status by it,'),
    ('has beenseparated', 'has been separated'), ('holds it initslap', 'holds it in its lap'),
    ('teleologicalcharacter', 'teleological character'), ('world of Il,', 'world of It,'), ('freelyconfront', 'freely confront'),
    ('which haa been', 'which has been'), ("approaches the l'ace,", 'approaches the Face,'), ('causal neceasity', 'causal necessity'),
    ('recogaised as tyranny', 'recognised as tyranny'), ('necessary ouly to', 'necessary only to'), ('it belonga together', 'it belongs together'),
    ('new Ieversal-the break through', 'new reversal—the break-through'), ('appear. ance as person', 'appearance as person'),
    ('to experience and to ise,', 'to experience and to use,'), ('thisitacquires', 'this it acquires'), ('went qut to meet', 'went out to meet'),
    ('isthesaying of I', 'is the saying of I'), ('ez-pressed', 'expressed'), ('Beneath the Iow of pictures', 'Beneath the row of pictures'),
    ('Ire extended lines of relations meesar the etern Thou.', 'The extended lines of relations meet in the eternal Thou.'),
    ('a glimpse throney-thr • eternal Thou; by means of every particular Inu me primary word',
     'a glimpse through to the eternal Thou; by means of every particular Thou the primary word'),
    ('of all tensations of', 'of all sensations of'), ('to us aa twofold', 'to us as twofold'), ('nothing else exista;', 'nothing else exists;'),
    ('the lifeof things andof conditioned', 'the life of things and of conditioned'), ('tbinking subject-one that', 'thinking subject—one that'),
    ('self--Iecognition', 'self-recognition'), ('freed andhas become', 'freed and has become'), ('that whichalone is', 'that which alone is'),
    ('opposed tooneanother', 'opposed to one another'), ('the &v guev cannot', 'the ἓν ἔσμεν cannot'),
    ('history of destraction of', 'history of destruction of'), ('how wity without duality', 'how unity without duality'),
    ('in whichtwo,', 'in which two,'), ('reality ofthe everyday', 'reality of the everyday'), ('here" -"That", replies', 'here"—"That", replies'),
    ('Reality existe only', 'Reality exists only'), ('a limitingidea', 'a limiting idea'), ('not misb to impart', 'not wish to impart'),
    ('will bedisclosed', 'will be disclosed'), ('a retarn we would not Beek', 'a return we would not seek'), ('the Buddah that', 'the Buddha that'),
    ('theextinction', 'the extinction'), ('be extin. guished,', 'be extinguished,'), ('ieconciled-just as', 'reconciled—just as'),
    ('no longer Really opposed', 'no longer really opposed'), ('that Reveals itself', 'that reveals itself'), ('Him who Reveals:', 'Him who reveals:'),
    ('Round about the invisible', 'round about the invisible'), ('he Knits them', 'he knits them'), ('two Rows of pictures', 'two rows of pictures'),
    ('the Teal objective', 'the real objective'), ('indissolubly Real pair', 'indissolubly real pair'), ('and of the Race.', 'and of the race.'),
    ('co-opera-tion', 'co-operation'), ('disin-terestedness-the', 'disinterestedness—the'), ('I kown so', 'I known so'),
    ('when he saya Colui', 'when he says Colui'), ('the anbroken truth', 'the unbroken truth'), ('take wingsanew', 'take wings anew'),
    ('the metacosmica. primal', 'the metacosmical primal'), ('nature is Represented', 'nature is represented'), ('buthe who lives', 'but he who lives'),
    ('realisa-tion', 'realisation'), ("relation-modern man's", 'relation—modern man’s'), ('pure Ielation that', 'pure relation that'),
    ('Nietzache', 'Nietzsche'), ('his life -it makes', 'his life—it makes'), ('revelation ohange into', 'revelation change into'),
    ('an Ittakes the place', 'an It takes the place'), ('devotional exere.', 'devotional exercises.'), ('Allrevelation is', 'All revelation is'),
    ('com-munities', 'communities'), ('Via Nuova', 'Vita Nuova'), ('has no par in the world', 'has no part in the world'),
    ('ruddering at the alienation', 'shuddering at the alienation'), ('only Ie-lation between', 'only relation between'),
    ('undreamt-of more-ment', 'undreamt-of movement'), ('without present-neas,', 'without presentness,'), ('suI-rounded', 'surrounded'),
    ('say too much-what', 'say too much—what'), ('the like-as an event', 'the like—as an event'), ('Thou to men-witness', 'Thou to men—witness'),
    ('to keep-possessed by', 'to keep—possessed by'), ('possession—-has', 'possession—has'), ('likeness-impossible', 'likeness—impossible'),
    ('its Centre-and only', 'its Centre—and only'), ('un-fathomable—this', 'unfathomable—this'), ('one--no, two', 'one—no, two'),
    ('against rue and has', 'against me and has'), ('look on it sa a picture', 'look on it as a picture'), ('situations —life', 'situations—life'),
    ('spheres —is now', 'spheres—is now'), ('grand relational - events', 'grand relational events'), ('emotional. shocks', 'emotional shocks'),
    ('The world. . of It', 'The world of It'), ('in accordance. with', 'in accordance with'), ('the second-as in', 'the second—as in'),
    ('we answer-forming,', 'we answer—forming,'), ('eachrela-tional', 'each relational'), ('the persona, as expressed', 'the persons, as expressed'),
    ('conditioned being Jou', 'conditioned being you'), ('this con- dition only', 'this condition only'), ('in a priors', 'in a priori'),
    ('an a priors', 'an a priori'), ('a priors', 'a priori'),
    ('in a shock if bight or splash', 'in a shock of light, or splash'), ('live and more over against us', 'live and move over against us'),
    ('sell-preservation', 'self-preservation'), ('been split sunder', 'been split asunder'), ('clearly tarns out', 'clearly turns out'),
    ('Many a morement termed', 'Many a movement termed'), ('who ride himself of', 'who rids himself of'), ('The mose direct', 'The most direct'),
    ('the I rink into unreality', 'the I sink into unreality'), ('any real elation with', 'any real relation with'),
    ('the a prior of relation', 'the a priori of relation'), ('the fust myths', 'the first myths'), ('not to enounce the world', 'not to renounce the world'),
    ('satiated til he finda', 'satiated till he finds'), ('truth adda for him', 'truth adds for him'), ('by the Thous which', 'by the Thou which'),
    ('only in elective action', 'only in effective action'), ('It airs at and is', 'It aims at and is'), ('they Iely wholly', 'they rely wholly'),
    ('aiter the idol', 'after the idol'), ('ally maling the eternal', 'ally making the eternal'), ('the communa prayer', 'the communal prayer'),
    ('spearing-tube', 'speaking-tube'), ('the animal bad sunk', 'the animal had sunk'), ('two lands of happening', 'two kinds of happening'),
    ('”—30 he himself expressed', '”—so he himself expressed'), ('"The universe beholds us us In the end', '"The universe beholds us!" In the end'),
    ('cries out: "O mother, I am lost.\' "', 'cries out: ‘O mother, I am lost.’"'), ('can be "taken up in exclusiveness', 'can be taken up in exclusiveness'),
    ('full азвигапсе.', 'full assurance.'), ('до "going beyond ведве-experience" із десевзату', 'no "going beyond sense-experience" is necessary'),
    ('solitude wé are', 'solitude we are'), ('your sou —for', 'your soul—for'), ('your sou—for', 'your soul—for'),
    ('the man—I-and the tree-Thou-,', 'the man—I—and the tree—Thou—,'), ('a hell—-and', 'a hell—and'), ('is relation-as category', 'is relation—as category'),
    ('real connexion-as it will', 'real connexion—as it will'), ('yet waiting-to rise', 'yet waiting—to rise'),
    ('drawing-disclosing-the boundary', 'drawing—disclosing—the boundary'), ('meeting-the present-has come', 'meeting—the present—has come'),
    ('such-and-auca', 'such-and-such'), ('says I-it can be decided', 'says I—it can be decided'), ('all-embracing-the united', 'all-embracing—the united'),
    ('disgust-and be would see', 'disgust—and he would see'), ('undreamt-of morement', 'undreamt-of movement'), ('his I-which now appeared', 'his I—which now appeared'),
    ('Through the Thou & man becomes', 'Through the Thou a man becomes'), ('subconsciousness oI any', 'subconsciousness or any'),
    ('being that is ia the world', 'being that is in the world'), ("the relation' with God", 'the relation with God'),
    ('inclusiveness ате оде.', 'inclusiveness are one.'), ('satiated til he finds', 'satiated till he finds'),
]
FIXES_RE = [(re.compile(r'\b' + a + r'\b'), b) for a, b in [('bis', 'his'), ('bim', 'him'), ('bia', 'his'), ('bimself', 'himself'), ('ita', 'its')]]

def repair(t):
    for a, b in FIXES:
        t = t.replace(a, b)
    for rx, b in FIXES_RE:
        t = rx.sub(b, t)
    return t

def normalise(t):
    t = re.sub(r'([”"])\s*•\s*(?=[A-Z])', r'\1. ', t)                # speck where a full stop was lost after a quote
    t = re.sub(r'\s*•\s*', ' ', t).strip()                             # specks read as bullets
    t = t.replace('--', '—').replace(' — ', '—').replace('— ', '—').replace(' —', '—')
    t = re.sub(r'([.!?”])\s+-(?=[A-Z“])', r'\1—', t)                   # ". -Everything" -> ".—Everything"
    t = re.sub(r'”-(?=\w)', '”—', t).replace('-“', '—“')
    t = re.sub(r'^[-—]\s*', '—', t)                                 # dialogue dash
    t = re.sub(r"(?<=\w)'(?=\w)", '’', t)                           # apostrophes
    t = re.sub(r'\s+([;:!?,.])', r'\1', t)                          # French-style spacing "mean !"
    t = re.sub(r'([.,;:!?])(?=[A-Za-z])', r'\1 ', t)                # "word.Word"
    t = re.sub(r'\(\s+', '(', t); t = re.sub(r'\s+\)', ')', t)
    if t.count('"') % 2 == 0:                                       # pair straight quotes -> curly, trim inner spaces
        out, open_ = [], True
        for part in t.split('"'):
            out.append(part)
        s = ''
        for i, part in enumerate(out):
            if i == 0:
                s = part
            elif i % 2 == 1:
                s = s.rstrip() + ' “' + part.lstrip() if s and not s.endswith(('(', '—', ' ')) else s + '“' + part.lstrip()
            else:
                s = s.rstrip() + '”' + part
        t = s
    else:
        audit('quote-odd', t[:80])
    t = re.sub(r'”(?=[A-Za-z])', '” ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

# ---------------------------------------------------------------- posts
TARGET = 550          # words per post before we stop adding sections
SPLIT_ABOVE = 800     # a single section longer than this is split on paragraph boundaries

def split_section(paras):
    words = [len(p.split()) for p in paras]
    n = max(1, round(sum(words) / TARGET))
    if n == 1 or len(paras) < 2:
        return [paras]
    target = sum(words) / n
    pieces, cur, acc = [], [], 0
    for p, w in zip(paras, words):
        if cur and acc + w / 2 > target and len(pieces) < n - 1:
            pieces.append(cur); cur, acc = [], 0
        cur.append(p); acc += w
    if cur:
        pieces.append(cur)
    return pieces

ROMAN = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii']

def make_posts():
    posts = []
    for part_name, pages in PARTS:
        secs = [[normalise(repair(p)) for p in s] for s in build_sections(pages)]
        # queue of (section number, piece label, paragraphs)
        queue = []
        for si, s in enumerate(secs, 1):
            if len(' '.join(s).split()) > SPLIT_ABOVE:
                for k, piece in enumerate(split_section(s)):
                    queue.append((si, ROMAN[k], piece, True))
            else:
                queue.append((si, '', s, False))
        cur = []
        def flush():
            if cur:
                posts.append((part_name, list(cur)))
                cur.clear()
        for item in queue:
            words_cur = sum(len(' '.join(p).split()) for _, _, p, _ in cur)
            words_new = len(' '.join(item[2]).split())
            small = words_new < 150 or words_cur < 150
            if cur and ((item[3] or cur[-1][3]) and not small or words_cur + words_new > TARGET + 100):
                flush()
            cur.append(item)
        flush()
    return posts

def esc(s):
    return html.escape(s, quote=False)

def render(items):
    parts = []
    for k, (si, label, paras, _) in enumerate(items):
        if k:
            parts.append('<p style="text-align:center">&#9733;</p>')
        for p in paras:
            parts.append(f'<p>{esc(p)}</p>')
    return '\n'.join(parts)

EPIGRAPH = ('<blockquote><p>So, waiting, I have won from you the end:<br>God’s presence in each element.</p>'
            '<p>— Goethe</p></blockquote>')

def title_for(part_name, items):
    first, last = items[0], items[-1]
    if first[0] == last[0]:
        ref = f'§{first[0]}' + (f' ({first[1]})' if first[1] else '')
    else:
        ref = f'§{first[0]}–{last[0]}'
    opening = first[2][0]
    words = opening.split()
    snippet = ' '.join(words[:7]).rstrip(',;:.—')
    if len(words) > 7:
        snippet += '…'
    return f'{part_name}, {ref}: {snippet}', f'{part_name.lower().replace(" ", "-")}-{first[0]}' + (f'-{first[1]}' if first[1] else '') + (f'-{last[0]}' if last[0] != first[0] else '')

if __name__ == '__main__':
    posts = []
    for idx, (part_name, items) in enumerate(make_posts(), 1):
        body = render(items)
        if idx == 1:
            body = EPIGRAPH + '\n' + body
        title, slug = title_for(part_name, items)
        words = len(re.sub(r'<[^>]+>', ' ', body).split())
        posts.append({'title': title, 'url': SOURCE_URL, 'slug': slug, 'content_html': body, 'post_index': idx,
                      'word_count': words, 'reading_time_minutes': max(1, round(words / 250))})
    with open(OUT, 'w') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    for p in posts:
        print(f"{p['post_index']:2d}  {p['word_count']:4d}w  {p['title']}")
    print(f"\n{len(posts)} posts, {sum(p['word_count'] for p in posts)} words -> {OUT}")
    if AUDIT:
        with open('buber_audit.txt', 'w') as f:
            for kind, msg in audit_log:
                f.write(f'{kind:15s} {msg}\n')
            f.write('\n== unknown words (after repair) ==\n')
            seen = Counter()
            for p in posts:
                text = re.sub(r'<[^>]+>', ' ', p['content_html'])
                ws = text.split()
                for i, w in enumerate(ws):
                    if not ok(w) and seen[w] < 2:
                        seen[w] += 1
                        f.write(f"{p['post_index']:2d}: {w!r:22s} | {' '.join(ws[max(0,i-5):i+6])}\n")
        print('audit -> buber_audit.txt')
