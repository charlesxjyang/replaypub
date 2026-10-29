# -*- coding: utf-8 -*-
"""Extract Isaiah Berlin, *The Hedgehog and the Fox* (Weidenfeld & Nicolson, 1953).

The PDF (arvindguptatoys.com) is a scan of the first edition whose OCR text layer is
unusually good: it carries the real Times fonts, so body type (9.1-10.2pt), block
quotations (8.2-9.0pt) and footnotes (<8.2pt) separate cleanly by size, and italics
survive as Times-Italic spans. Paragraphs are rebuilt from pymupdf line geometry
(indent relative to the neighbouring lines, because the scan is skewed).

What the scan loses, and what is repaired here:
  * thin spaces, so 'of the' reads 'ofthe' (SPLITS, plus a glued-word pass)
  * every dash is a hyphen, so line-end breaks, true compounds and em dashes have
    to be told apart (TRUE_HYPHENS / LINE_BREAKS, defaulting to an em dash)
  * scattered letter confusions (FIXES)
The 1953 footnotes are dropped, following the Millotat and Lacy feeds.

Usage: python extract_berlin.py   ->  berlin_clean.json
"""

import fitz, re, json, html, statistics
from collections import Counter

PDF = 'berlin_hedgehog.pdf'
OUT = 'berlin_clean.json'
SOURCE_URL = 'https://www.arvindguptatoys.com/arvindgupta/hedgehog-berlin.pdf'

BODY_PAGES = range(9, 91)
# The epigraph on the opening page, which the scan reads as part of the half-title.
EPIGRAPH = ('A queer combination of the brain of an English chemist with the soul '
            'of an Indian Buddhist.', 'E. M. DE VOG\u00dc\u00c9')
FOOT_MAX, QUOTE_MAX = 8.2, 9.05      # font-size class boundaries

# The eight section numerals, by (pdf page, y) of the line that holds them.
# A line the scan sets in quotation type although it continues the paragraph above.
BODY_OVERRIDE = {(21, 268.3)}

SECTION_MARKS = {(9, 97.4): 'I', (12, 309.8): 'II', (18, 67.8): 'III', (50, 105.3): 'IV',
                 (56, 267.3): 'V', (70, 392.2): 'VI', (80, 40.0): 'VII', (88, 148.4): 'VIII'}

d = fitz.open(PDF)


# ---------------------------------------------------------------- lines
def visual_lines(pno):
    """One record per printed line: justified text splits a line into fragments that
    must be sorted left-to-right and rejoined with a space before anything else."""
    raw = [l for b in d[pno].get_text('dict')['blocks'] for l in b.get('lines', [])]
    raw = [l for l in raw
           if ''.join(s['text'] for s in l['spans']).strip() and l['bbox'][1] > 0]
    raw.sort(key=lambda l: l['bbox'][1])
    rows = []
    for l in raw:
        if rows and abs(l['bbox'][1] - rows[-1][0]['bbox'][1]) <= 5:
            rows[-1].append(l)
        else:
            rows.append([l])
    out = []
    for c in rows:
        c.sort(key=lambda l: l['bbox'][0])
        text = ' '.join(''.join(s['text'] for s in l['spans']) for l in c)
        sizes = [s['size'] for l in c for s in l['spans'] if s['text'].strip()]
        out.append({'y': min(l['bbox'][1] for l in c),
                    'x': min(l['bbox'][0] for l in c),
                    'x1': max(l['bbox'][2] for l in c),
                    'sz': statistics.median(sizes),
                    't': re.sub(r'\s+', ' ', text).strip()})
    return out


# Page numbers, printed in brackets the scan mangles, sometimes preceded by the
# signature letter of the gathering ('B [ 9 ]'), and bare signature letters.
PAGENO = re.compile(r"^(?:[A-Za-z]\s*)?(?:[\[r(].{0,6}[\]J)]|[A-Za-z0-9])$")
FOOT_MARK = re.compile(r"^[\d'•,•]")


def footnote_start(lines, height):
    """Index of the first footnote line, or len(lines).

    Footnotes are the page's tail in type smaller than any block quotation, so the
    tail is walked backwards through everything below body size and cut at the
    highest line that is footnote size. On the pages that are wholly block
    quotation (30) the footnote is only a shade smaller than the quote, and there
    the page-bottom gap decides instead.
    """
    gaps = [lines[i]['y'] - lines[i - 1]['y'] for i in range(1, len(lines))]
    med = statistics.median(gaps) if gaps else 11.0
    cut, i = len(lines), len(lines) - 1
    while i > 0 and lines[i]['sz'] < QUOTE_MAX:
        if lines[i]['sz'] < FOOT_MAX and lines[i]['y'] > height * 0.4:
            cut = i
        i -= 1
    if cut < len(lines):
        return cut
    for i, l in enumerate(lines):
        if i == 0 or l['y'] < height * 0.5:
            continue
        rest = lines[i:]
        if (len(rest) <= 6 and gaps[i - 1] >= med * 1.45 and FOOT_MARK.match(l['t'])
                and all(r['sz'] < QUOTE_MAX for r in rest)):
            return i
    return len(lines)


def page_units(pno):
    """-> list of (kind, starts_paragraph, [line text, ...]) for one page.

    kind is 'p' (body), 'q' (block quotation), 'h' (section numeral) or 'e' (epigraph).
    """
    height = d[pno].rect.height
    # Page numbers go first: they are set in large type and would otherwise hide
    # the footnote block that sits above them.
    lines = [l for l in visual_lines(pno)
             if (pno, round(l['y'], 1)) in SECTION_MARKS
             or not (PAGENO.match(l['t']) and l['y'] > height * 0.72)]
    cut = footnote_start(lines, height)
    body = []
    for i, l in enumerate(lines[:cut]):
        mark = SECTION_MARKS.get((pno, round(l['y'], 1)))
        if mark:
            # Section I shares its line with the drop-cap T of 'THERE'.
            if mark == 'I':
                lines[i + 1]['t'] = 'T' + lines[i + 1]['t']
            body.append({**l, 'kind': 'h', 't': mark})
            continue
        if pno == 9 and l['y'] < 70:
            continue                 # the half-title and the Vogüé epigraph (below)
        small = l['sz'] < QUOTE_MAX and (pno, round(l['y'], 1)) not in BODY_OVERRIDE
        body.append({**l, 'kind': 'q' if small else 'p'})

    units = []
    for i, l in enumerate(body):
        if l['kind'] in 'he':
            units.append((l['kind'], True, [l['t']]))
            continue
        near = [body[j]['x'] for j in (i - 1, i + 1)
                if 0 <= j < len(body) and body[j]['kind'] == l['kind']]
        indent = bool(near) and l['x'] > min(near) + 6
        if pno == 9 and l['y'] < 140:
            indent = False           # the first three lines clear the drop cap
        if units and units[-1][0] == l['kind'] and not indent:
            units[-1][2].append(l['t'])
        else:
            units.append((l['kind'], indent, [l['t']]))
    return units


# ---------------------------------------------------------------- dashes
# Hyphens that are real hyphens. Every other hyphen between two letters is an em
# dash the scan flattened; the list was read off the full inventory of the text.
TRUE_HYPHENS = {
    'all-embracing', 'all-important', 'all-pervasive', 'all-powerful', 'amour-propre',
    'ant-hill', 'anti-Bonapartism', 'anti-historical', 'anti-intellectualism',
    'anti-liberal', 'anti-liberalism', 'anti-metaphysical', 'anti-revolutionary',
    'anti-industrial', 'anti-theological', 'arch-fox', 'artistic-psychological',
    'bed-rock', 'bell-wether', 'blood-and-iron',
    'by-product', 'clear-sighted', 'co-ordinate', 'coarse-grained', 'common-sense',
    'corner-stone', 'counter-evidence', 'counter-revolutionaries', 'death-bed',
    'drawing-room', 'feeble-witted', 'fellow-men', 'first-hand', 'half-baked',
    'hey-day', 'high-minded', 'hobby-horse', 'home-made', 'ill-conducted',
    'knock-kneed',
    'latter-day', 'left-wing',
    'life-likeness', 'life-long', 'lip-service', 'little-known', 'lop-sided',
    'man-made', 'mid-nineteenth', 'mid-sixties', 'multi-coloured', 'mumbo-jumbo',
    'neo-feudalism', 'nineteenth-century', 'non-existent', 'non-rational',
    'non-human', 'non-philosophical', 'non-scientific', 'one-ness', 'one-time',
    'other-worldly', 'over-clever',
    'over-estimates', 'over-familiar', 'over-simple', 'Pan-Slav', 'pre-Raphaelites',
    'pre-revolutionary', 'present-day', 'pseudo-sciences', 'quasi-metaphysical',
    'quasi-theological', 'quasi-utilitarian', 're-establish', 'Saint-Simon',
    'Sankt-Petersburgskiya', 'self-blinded', 'self-confident', 'self-contradictory',
    'self-deception', 'self-destructive', 'self-educated', 'self-identification',
    'self-immolation', 'self-immolatory', 'self-important', 'self-renunciation',
    'self-deluded', 'self-defeating', 'self-hatred', 'self-abasing', 'self-sacrifice', 'self-sacrificing',
    'semi-official', 'second-rate', 'sharp-eyed', 'so-called', 'starting-point',
    'subject-matter', 'tea-merchant', 'tender-minded', 'three-dimensional',
    'theologico-political', 'three-quarters', 'time-serving', 'tough-minded',
    'town-bred', 'truth-finding', 'well-integrated', 'well-known', 'well-lighted',
    'well-meaning',
    # French and Latin, where the hyphen belongs to the language
    "c'est-a", "c'est-a-dire", "N'avons-nous", 'peut-il', 'sait-il',
    'savez-vous', 'Tolstoi-historien', 'voit-il',
    'day-to-day', 'might-have-beens', 'neo-medievalists',
}

# Line-end hyphens whose two halves make one word, where the joined form is not in
# the dictionary (proper names, period spellings) or where the default is wrong.
LINE_BREAKS = {
    # proper names and words the dictionary does not hold, broken across a line
    'join': {'Push-kin', 'Dostoev-sky', 'Shakes-peare', 'philo-sophise', 'Danilev-sky',
             'Rubin-shteyn', 'arri-ving', 'Tol-stoy', "Tol-stoy's", 'Bennig-sen',
             'prac-tised', 'eluci-dating', 'explana-tion', 'unana-lysed', 'sum-mate',
             'com-munities', 'ofposi-tive', 'Cherny-shevsky', 'absur-dities',
             'Schopen-hauer', 'diffi-culties', 'pour-quoi', 'activi-ties',
             'super-ficialities', 'commo-dities', 'Pau-lucci', 'probabi-lities',
             'arm-chair', 'describedsmallidiosyn-crasies', 'non-sense'},
    'hyphen': set(),
    'dash': set(),
}


def dash_decision(left, right, at_line_end):
    """'join' | 'hyphen' | 'dash' for a hyphen between *left* and *right*."""
    pair = f'{left}-{right}'
    for verdict in ('join', 'hyphen', 'dash'):
        if pair in LINE_BREAKS[verdict]:
            return verdict
    if pair.lower() in HYPHENS_LOWER:
        return 'hyphen'
    if at_line_end and (left + right).lower() in WORDS:
        return 'join'
    return 'dash'


# A line-break hyphen the scan read as something else. '.' only counts when the
# two halves make a word, so that a sentence end is never swallowed.
BREAK_CHARS = '-\u00b7~'


def join_lines(texts):
    out = ''
    for t in texts:
        if not out:
            out = t
            continue
        left = re.search(r'[A-Za-z]+$', out[:-1])
        right = re.match(r'[A-Za-z]+', t)
        broken = out[-1] in BREAK_CHARS
        if (out.endswith('.') and left and right and t[:1].islower()
                and (left.group(0) + right.group(0)).lower() in WORDS):
            broken = True
        if broken and left and right:
            verdict = dash_decision(left.group(0), right.group(0), True)
            out = out[:-1] + ('' if verdict == 'join'
                              else '-' if verdict == 'hyphen' else '\u2014') + t
        elif out.endswith('-'):
            out = out[:-1] + '\u2014' + t
        elif t.startswith('-'):               # an em dash carried to the next line
            out += '\u2014' + t[1:]
        else:
            out += ' ' + t
    return out


HYPHENS_LOWER = {h.lower() for h in TRUE_HYPHENS}
RUN = re.compile(r"[A-Za-z'\u2019]+(?:[-~\u00b7][A-Za-z'\u2019]+)+")
# A dash with a quotation mark or a bracket on one side of it. A dash between two
# words is left to RUN, which knows the compounds.
LOOSE = re.compile(r"""(?<=['\u2019")\].,!?])[-~\u00b7](?=[A-Za-z'\u2018"(])"""
                   r"""|(?<=[A-Za-z])[-~\u00b7](?=['\u2018\u2019")])""")


def dashes(text):
    """Decide every flattened dash: inside a compound the whitelist rules, and a
    hyphen anywhere else between two words is an em dash."""
    def run(m):
        seg = re.split(r'[-~\u00b7]', m.group(0))
        core = [x.strip('\'\u2018\u2019"') for x in seg]
        out = seg[0]
        for i in range(len(seg) - 1):
            covered = any('-'.join(core[j:k + 1]).lower() in HYPHENS_LOWER
                          for j in range(i + 1) for k in range(i + 1, len(seg)))
            out += ('-' if covered else '\u2014') + seg[i + 1]
        return out
    text = RUN.sub(run, text)
    return LOOSE.sub('\u2014', text)


# ---------------------------------------------------------------- vocabulary
def load_words():
    """Vocabulary for the glued-word and line-break passes: the pyspellchecker
    frequency list (which has inflections) plus the system list and the period
    and British spellings neither of them holds."""
    from spellchecker import SpellChecker
    words = set(SpellChecker().word_frequency.dictionary)
    try:
        with open('/usr/share/dict/words') as f:
            words.update(w.strip().lower() for w in f if len(w.strip()) > 2)
    except FileNotFoundError:
        pass
    words.update(EXTRA_WORDS)
    return words


EXTRA_WORDS = {
    'connexions', 'connexion', 'interconnexion', 'sceptical', 'scepticism', 'sceptic',
    'realise', 'realised', 'organising', 'organised', 'recognised', 'civilised',
    'analysed', 'emphasised', 'criticised', 'idealised', 'generalisations',
    'centralisation', 'rationalisation', 'moralising', 'unplausible', 'unhistorical',
    'interpenetration', 'uncontrollability', 'inexpressible', 'unassimilable',
    'unaccountable', 'ineradicable', 'indescribable', 'unanalysable', 'unverifiable',
    'unquantifiable', 'incommensurable', 'untranslatable', 'unintelligible',
    'unalterable', 'inescapable', 'unchanging', 'unrelated', 'unexplained',
    'misinterpretation', 'oversimplification', 'preoccupation', 'presuppositions',
    'superficiality', 'systematisation', 'disquisitions', 'theodicy', 'obscurantist',
    'metaphysicians', 'tous', 'beens',
    # names and French words the glued-word pass would otherwise split
    'sorel', 'toutes', 'maistre', 'tolstoy',
}

WORDS = set()


# ---------------------------------------------------------------- repairs
# The scan drops thin spaces. These are the function words it glues to the next
# word; the pass below splits them only when the remainder is itself a word.
GLUE_HEADS = ('of', 'to', 'in', 'is', 'if', 'as', 'at', 'by', 'on', 'or', 'so', 'be',
              'he', 'we', 'it', 'its', 'my', 'no', 'an', 'the', 'and', 'but', 'for',
              'his', 'her', 'not', 'all', 'any', 'one', 'out', 'who', 'was', 'that',
              'this', 'with', 'from', 'when', 'what', 'half', 'myself', 'himself',
              'itself', 'aim', 'writings', 'own')


def unglue(text):
    def fix(m):
        w = m.group(0)
        low = w.lower()
        if low in WORDS or len(w) < 3:
            return w
        for head in GLUE_HEADS:
            if low.startswith(head) and len(low) > len(head):
                rest = low[len(head):]
                if rest in WORDS and rest not in ('s', 'e', 'd', 'r', 't', 'n'):
                    return w[:len(head)] + ' ' + w[len(head):]
        return w
    return re.sub(r"[^\W\d_]['\u2019]?[^\W\d_]+", fix, text)


# Glued pairs the general pass cannot reach, digits the scan turned into letters,
# note markers it left behind, and plain misreadings. Each was checked against the
# page image; main() reports any that stops matching.
FIXES = [
    # note references the regex below cannot see
    ('Pavel Annenkov 1 Turgenev', 'Pavel Annenkov Turgenev'),
    ("Great's Nakaz 3 with", "Great's Nakaz with"),
    ('himself" and argued', 'himself and argued'),
    ("one's life.'\" Or again", "one's life.' Or again"),
    ("its proper aim'.\" The reason", "its proper aim'. The reason"),
    ("free will] 1 is destroyed", 'free will] is destroyed'),
    ("reading Maistre',' and on", "reading Maistre', and on"),
    ('(1846-53) 2 we find', '(1846-53) we find'),
    # dates and numerals
    ('fought in r812', 'fought in 1812'),
    ('in I g08, he declares', 'in 1908, he declares'),
    ('on August 2 I, 1562', 'on August 21, 1562'),
    ("in the year'I I quarrelled", "in the year '11 quarrelled"),
    ('Moscow in r8r2 Tolstoy', 'Moscow in 1812 Tolstoy'),
    ('In r 803 Maistre', 'In 1803 Maistre'),
    ('from r803 to r8r7', 'from 1803 to 1817'),
    ('met Maistre in r307', 'met Maistre in 1807'),
    ('on 7 April r888', 'on 7 April 1888'),
    ('interview in IgOI', 'interview in 1901'),
    ("1572 . .\u2022\u2022 \"", "1572....'"),
    # words run together or split by lost thin spaces
    ('poetArchilochus', 'poet Archilochus'),
    ("made to'yield", 'made to yield'),
    ('yetprimafacie', 'yet prima facie'),
    ('And halfa century', 'And half a century'),
    ('they bothagain began', 'they both again began'),
    ('triedtoturn historyintosociology', 'tried to turn history into sociology'),
    ('inferenceand similar meanswas', 'inference and similar means was'),
    ('General Staffat Drissa', 'General Staff at Drissa'),
    ('by itselfto provide', 'by itself to provide'),
    ('this beliefis exceptionally', 'this belief is exceptionally'),
    ('and beliefin freedom', 'and belief in freedom'),
    ('act, butan unintelligible', 'act, but an unintelligible'),
    ('that ofAuguste Comte', 'that of Auguste Comte'),
    ('describedsmallidiosyncrasies', 'described small idiosyncrasies'),
    ('Both were aufond unyieldingly', 'Both were au fond unyieldingly'),
    ('wisdom~liesin an understanding', "wisdom\u2014lies in an understanding"),
    ('logic?)~thegreat unalterable', 'logic?)\u2014the great unalterable'),
    ('and how and when~all of which', 'and how and when\u2014all of which'),
    ('the bleak truth~-sideby side', 'the bleak truths\u2014side by side'),
    ('doubtless influenced tr.~ young', 'doubtless influenced the young'),
    ('believed only in ~ ol),vast, unitary', 'believed only in one vast, unitary'),
    ("(and ,retrodiction ' of the past)", "(and, 'retrodiction' of the past)"),
    # note references the scan read as a stray quotation or letter
    ('Historians ofRussian thought\' tend', 'Historians ofRussian thought tend'),
    ('He reads Hume and Thiers\' as well', 'He reads Hume and Thiers as well'),
    ('this is almost unique.!', 'this is almost unique.'),
    ('the famous armchair\' and thereby', 'the famous armchair and thereby'),
    ('were the most useless.I Worst', 'were the most useless. Worst'),
    ('such conferring done?l The process', 'such conferring done? The process'),
    ('a particularly vivid simile! in which', 'a particularly vivid simile in which'),
    ('the furniture of the world.! Like', 'the furniture of the world. Like'),
    ('in any language,\' in the course', 'in any language, in the course'),
    ('and Peace had appeared,\' Tolstoy vacillates',
     'and Peace had appeared, Tolstoy vacillates'),
    ('into arbitrary segments.\' Tolstoy expresses',
     'into arbitrary segments. Tolstoy expresses'),
    ('an insult to the intelligence." Tolstoy', 'an insult to the intelligence. Tolstoy'),
    ('has pointed out,\' Tolstoy', 'has pointed out, Tolstoy'),
    ("scholars have shown,' not as much", 'scholars have shown, not as much'),
    ("with M. Paul Boyer,' Tolstoy coupled", 'with M. Paul Boyer, Tolstoy coupled'),
    # possessives the quotation-mark pass would otherwise read as quotes
    ("but old wives' tales", 'but old wives\u2019 tales'),
    ("kill his rivals' rickety", 'kill his rivals\u2019 rickety'),
    ('in glowing colours;!', 'in glowing colours;'),
    ('extensively in War and Peace.! Thus', 'extensively in War and Peace. Thus'),
    ('one critic of Maistre,l still largely', 'one critic of Maistre, still largely'),
    ("delivered on 7 April 1888.' He drew", 'delivered on 7 April 1888. He drew'),
    ("like Proudhon after him,' glorifies war", 'like Proudhon after him, glorifies war'),
    # the 1953 printing doubles 'and' across a line break
    ('secular faith and and efforts', 'secular faith and efforts'),
    # misread letters
    ('accumulates enough ,power\'', "accumulates enough 'power'"),
    ('doubtless all men arc liable', 'doubtless all men are liable'),
    ('and to deny th;-,t we could', 'and to deny that we could'),
    ('assumed by naIve historians', 'assumed by na\u00efve historians'),
    ('obsessed by the --) desire', 'obsessed by the desire'),
    ("'political'-public--events", "'political'-public-events"),
    ('or Mme de Stael or Baron Stein', 'or Mme de Sta\u00ebl or Baron Stein'),
    ('Erasmus, Moliere, Goethe', 'Erasmus, Moli\u00e8re, Goethe'),
    ("'il se repete! et il philosophise!'",
     "'il se r\u00e9p\u00e8te! et il philosophise!'"),
    ('as an aeute literary historian', 'as an acute literary historian'),
    ('his doctrine that anillysis of them', 'his doctrine that analysis of them'),
    ("significance or value ilnd 'reality'", "significance or value and 'reality'"),
    ('the raisons de crrur', 'the raisons de c\u0153ur'),
    ('observers of the vanetIeS of experience', 'observers of the varieties of experience'),
    ('theories moclelled upon', 'theories modelled upon'),
    ('experience, treatecl him', 'experience, treated him'),
    ('protest and suITer in vain', 'protest and suffer in vain'),
    ('make sorly fools', 'make sorry fools'),
    ('\\-Vhy is this called', 'Why is this called'),
    ("'\\Thy should we accept", 'Why should we accept'),
    ('ideas of l\\faistre', 'ideas of Maistre'),
    ('too, l\\1aistre talks', 'too, Maistre talks'),
    ('that to StendhaI.', 'that to Stendhal.'),
    ('from Wackenroder and Garres', 'from Wackenroder and G\u00f6rres'),
    ('ancient superstititions', 'ancient superstitions'),
    ('or by other-wordly mysteries', 'or by other-worldly mysteries'),
    ('in some defacto way', 'in some de facto way'),
    ('the appearance ofBagration', 'the appearance of Bagration'),
    ("the task of 'deduc:ing' any", "the task of 'deducing' any"),
    ('and self.abasing', 'and self-abasing'),
    ('voprosy" became fused', "voprosy' became fused"),
    ("alternatives-' might have beens'", "alternatives-'might-have-beens'"),
    ("their VISIOn is , profounder',", "their vision is 'profounder',"),
    ("for' C'est l'imagination qui perd les batailles',3 and 'peu de batailles "
     "sont perdues physiquement-vous tirez, je tire ... Ie veritable vainqueur, "
     "comme Ie veritable vaincu, c'est celui qui croit l'etre'.'",
     "for 'C'est l'imagination qui perd les batailles', and 'peu de batailles sont "
     "perdues physiquement\u2014vous tirez, je tire... le v\u00e9ritable vainqueur, comme "
     "le v\u00e9ritable vaincu, c'est celui qui croit l'\u00eatre'."),
    ('He died in 182 I, the author', 'He died in 1821, the author'),
    ('the celebrated actress MIle Georges', 'the celebrated actress Mlle Georges'),
    ('from the mystic to the. nihilist', 'from the mystic to the nihilist'),
    ('not a physical Issue:', 'not a physical issue:'),
    ('an empirical pis alter to which', 'an empirical pis aller to which'),
    ('and similarly :Maistre achieves', 'and similarly Maistre achieves'),
    ("by a montage sur l'epingle", "by a montage sur l'\u00e9pingle"),
    ('incompatible, posItions, to the elimination',
     'incompatible, positions, to the elimination'),
    ('offered to throwaway the terrible', 'offered to throw away the terrible'),
    ("Beside Tolstoy, Gogol' and Dostoevsky",
     'Beside Tolstoy, Gogol\u2019 and Dostoevsky'),
    ("Maistre's 'Expliquez pourquoi ce qu'il y a de plus honorable dans Ie monde, "
     "au jugement de tout Ie genre humain sans exception, est Ie droit de verser "
     "innocemment Ie sang innocent? ',2",
     "Maistre's 'Expliquez pourquoi ce qu'il y a de plus honorable dans le monde, "
     "au jugement de tout le genre humain sans exception, est le droit de verser "
     "innocemment le sang innocent?',"),
    # names the scan stripped of their accents
    ('interest to Vogue and Merezhkovsky', 'interest to Vogu\u00e9 and Merezhkovsky'),
    ('which Vogue and Albert Sorel', 'which Vogu\u00e9 and Albert Sorel'),
    ('not, pace Albert Sorel and Vogue, in', 'not, pace Albert Sorel and Vogu\u00e9, in'),
    ('Maistre, as later for Barres', 'Maistre, as later for Barr\u00e8s'),
    ('of the Crimean debdcle', 'of the Crimean d\u00e9b\u00e2cle'),
    ('the eminent emigres in Anna', 'the eminent \u00e9migr\u00e9s in Anna'),
    ('by his fellow emigres, than', 'by his fellow \u00e9migr\u00e9s, than'),
    ('lecture to the Ecole des Sciences', 'lecture to the \u00c9cole des Sciences'),
    ('enlightened or revolti at all', 'enlightened or r\u00e9volt\u00e9 at all'),
    ('all the ecrivasserie et avocasserie',
     'all the \u00e9crivasserie et avocasserie'),
    ('still recommended Emile as', 'still recommended \u00c9mile as'),
    ('celebrated Soirees de St. Petersbourg',
     'celebrated Soir\u00e9es de St. P\u00e9tersbourg'),
    ('possessed the SoirrJes, as well', 'possessed the Soir\u00e9es, as well'),
    # French in the Maistre quotations
    ('fa terre et fes morts', 'la terre et les morts'),
]

# The four long quotations from Maistre's *Soirées*. The scan reads French badly
# — it drops every accent and confuses c/e, l/I and tt/TT — so each is replaced
# whole, keyed by the opening words of the block the extractor builds.
FRENCH = {
    "'On parle beaucoup de batailles":
        "'On parle beaucoup de batailles dans le monde sans savoir ce que c'est; on est "
        "surtout assez sujet à les considérer comme des points, tandis qu'elles couvrent "
        "deux ou trois lieues de pays; on vous dit gravement: Comment ne savez-vous pas ce "
        "qui s'est passé dans ce combat puisque vous y étiez? tandis que c'est précisément "
        "le contraire qu'on pourrait dire assez souvent. Celui qui est à la droite sait-il "
        "ce qui se passe à la gauche? sait-il seulement ce qui se passe à deux pas de lui? "
        "Je me représente aisément une de ces scènes épouvantables: sur un vaste terrain "
        "couvert de tous les apprêts du carnage, et qui semble s'ébranler sous les pas des "
        "hommes et des chevaux; au milieu du feu et des tourbillons de fumée; étourdi, "
        "transporté par le retentissement des armes à feu et des instruments militaires, "
        "par des voix qui commandent, qui hurlent ou qui s'éteignent; environné de morts, "
        "de mourants, de cadavres mutilés; possédé tour à tour par la crainte, par "
        "l'espérance, par la rage, par cinq ou six ivresses différentes, que devient "
        "l'homme? que voit-il? que sait-il au bout de quelques heures? que peut-il sur lui "
        "et sur les autres? Parmi cette foule de guerriers qui ont combattu tout le jour, "
        "il n'y en a souvent pas un seul, et pas même le général, qui sache où est le "
        "vainqueur. Il ne tiendrait qu'à moi de vous citer des batailles modernes, des "
        "batailles fameuses dont la mémoire ne périra jamais; des batailles qui ont changé "
        "la face des affaires en Europe, et qui n'ont été perdues que parce que tel ou tel "
        "homme a cru qu'elles l'étaient; de manière qu'en supposant toutes les "
        "circonstances égales, et pas une goutte de sang de plus versée de part et "
        "d'autre, un autre général aurait fait chanter le Te Deum chez lui, et forcé "
        "l'histoire de dire tout le contraire de ce qu'elle dira.'",
    "'N'avons-nous pas fini":
        "'N'avons-nous pas fini même par voir perdre des batailles gagnées?... Je crois en "
        "général que les batailles ne se gagnent ni ne se perdent point physiquement.'",
    "'De meme une armee":
        "'De même une armée de 40,000 hommes est inférieure physiquement à une autre armée "
        "de 60,000: mais si la première a plus de courage, d'expérience et de discipline, "
        "elle pourra battre la seconde; car elle a plus d'action avec moins de masse, et "
        "c'est ce que nous voyons à chaque page de l'histoire.'",
    "'C'est l'opinion qui perd":
        "'C'est l'opinion qui perd les batailles, et c'est l'opinion qui les gagne.'",
    "'Qu'est ce qu'une bataillc perdue":
        "'Qu'est ce qu'une bataille perdue?... C'est une bataille qu'on croit avoir perdue. "
        "Rien n'est plus vrai. Un homme qui se bat avec un autre est vaincu lorsqu'il est "
        "tué ou terrassé, et que l'autre est debout; il n'en est pas ainsi de deux armées: "
        "l'une ne peut être tuée, tandis que l'autre reste en pied. Les forces se balancent "
        "ainsi que les morts, et depuis surtout que l'invention de la poudre a mis plus "
        "d'égalité dans les moyens de destruction, une bataille ne se perd plus "
        "matériellement; c'est-à-dire parce qu'il y a plus de morts d'un côté que de "
        "l'autre: aussi Frédéric II, qui s'y entendait un peu, disait: Vaincre, c'est "
        "avancer. Mais quel est celui qui avance? c'est celui dont la conscience et la "
        "contenance font reculer l'autre.'",
}


# Footnote-reference digits left in the body once the notes are dropped. A digit
# that opens with an apostrophe is a date ('07), not a reference, so a quotation
# mark only counts when a space follows it.
NOTE_MARK = re.compile(r"(?<=[.,;:!?)])\s?\d(?=\s|$)"
                       r"|(?<=[.,;:!?)]['\u2019\u201d\"])\d(?=\s|$)"
                       r"|(?<=['\u2019\u201d\"])\s\d(?=\s|$)")


# Between two letters a quote is an apostrophe when it makes an English
# contraction, a French elision, or one of the transliterated Russian names;
# otherwise it is a quotation mark the scan pushed against the word before it.
CONTRACTION = re.compile(r"(?:s|t|ll|ve|re|d|m)\b")
ELISION = re.compile(r"\b(?:l|d|n|s|c|j|m|t|qu|lorsqu|puisqu|jusqu)$", re.I)
RUSSIAN_APOSTROPHE = ("Nazar'ev",)


def is_apostrophe(text, i):
    if any(w in text[max(0, i - 6):i + 4] for w in RUSSIAN_APOSTROPHE):
        return True
    if CONTRACTION.match(text, i + 1):
        return True
    return bool(ELISION.search(text[:i]))


def quotes(text):
    """Curl the single quotes and close up the thin spaces the scan turned into
    ordinary ones ("says: ' The fox ... one big thing '." -> "says: ‘The fox ...
    one big thing’."). Quotation marks alternate, so an apostrophe has to be told
    apart from them: inside a word it is a contraction or an elision, and after a
    word while no quotation is open it is a transliterated soft sign (Gogol’,).
    """
    out, is_open, skip = [], False, False
    for i, ch in enumerate(text):
        if skip:
            skip = False
            if ch == ' ':
                continue
        if ch != "'":
            out.append(ch)
            continue
        prev = text[i - 1] if i else ' '
        nxt = text[i + 1] if i + 1 < len(text) else ' '
        if nxt.isdigit():                       # an elided year: ’07, ’11
            out.append('’')
        elif prev.isalpha() and nxt.isalpha() and is_apostrophe(text, i):
            out.append('’')
        elif is_open:
            while out and out[-1] == ' ':
                out.pop()
            out.append('’')
            is_open = False
        elif prev.isalpha() and not nxt.isspace() and not nxt.isalpha():
            out.append('’')
        else:
            if out and out[-1] not in ' ([—':
                out.append(' ')
            out.append('‘')
            is_open, skip = True, True
    return ''.join(out)


UNUSED_FIXES = {a for a, _ in FIXES} | set(FRENCH)


def clean(text):
    for key, french in FRENCH.items():
        if text.startswith(key):
            UNUSED_FIXES.discard(key)
            text = french
            break
    for a, b in FIXES:
        if a in text:
            UNUSED_FIXES.discard(a)
            text = text.replace(a, b)
    text = unglue(text)
    text = dashes(text)
    text = NOTE_MARK.sub('', text)
    text = quotes(text)
    text = re.sub(r'\s+([;:,.!?])', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def paragraphs(raw=False):
    """-> list of (kind, text) across the whole essay; raw=True skips the repairs."""
    out = []
    for pno in BODY_PAGES:
        for kind, indent, texts in page_units(pno):
            text = join_lines(texts)
            if out and out[-1][0] == kind and not indent and kind in 'pq':
                out[-1][1] = join_lines([out[-1][1], text])
            else:
                out.append([kind, text])
    return [(k, t if raw else clean(t)) for k, t in out]


# ---------------------------------------------------------------- italics
# The scan keeps Berlin's italics as Times-Italic spans, but they do not survive
# the repairs above, so they are restored here from the inventory of every italic
# run in the body text. Titles and foreign phrases are restored everywhere they
# occur; the handful of emphasized single words carry enough context to be unique.
ITALIC_PHRASES = [
    'War and Peace', 'Anna Karenina', 'Fathers and Children', 'Contrat Social',
    'La Guerre et la Paix', 'La Chartreuse de Parme', 'Correspondance diplomatique',
    'Soirées de St. Pétersbourg', 'Soirées', 'Émile', 'Nakaz',
    'obiter dicta', 'de facto', 'prima facie', 'au fond', 'amour-propre',
    'pis aller', 'vice versa', 'mutatis mutandis', 'per se', 'status quo',
    'Zeitgeist', 'débâcle', 'raconteur', 'émigrés', 'penseurs',
    'vignettes', 'panache', 'bourgeoisie', 'bourgeois', 'ethos', 'expertise',
    'révolté', 'obscurum per obscurius', 'in commotione Dominus',
    'Graeculus esuriens', 'écrivasserie et avocasserie', 'Te Deum',
    'L’ami du bourreau', 'la terre et les morts', 'montage sur l’épingle',
]
ITALIC_ONCE = [
    ('What it will tell us', 'What it <em>will</em> tell us'),
    ('connected with his skill, his plans, that it is his authority',
     'connected with <em>his</em> skill, <em>his</em> plans, that it is '
     '<em>his</em> authority'),
    ('This is the integrating of infinitesimals',
     'This <em>is</em> the integrating of infinitesimals'),
    ('a system to which they must belong',
     'a system to which they <em>must</em> belong'),
    ('Nevertheless, something is perceived',
     'Nevertheless, something <em>is</em> perceived'),
    ('the flow (it is the flow)', 'the flow (it <em>is</em> the flow)'),
    ('not, pace Albert Sorel', 'not, <em>pace</em> Albert Sorel'),
]
ITALIC_RE = re.compile('|'.join(r'\b%s\b' % re.escape(p) for p in
                                sorted(ITALIC_PHRASES, key=len, reverse=True)))


def esc(text):
    out = html.escape(text, quote=False)
    for plain, marked in ITALIC_ONCE:
        out = out.replace(plain, marked)
    return ITALIC_RE.sub(lambda m: f'<em>{m.group(0)}</em>', out)


# ---------------------------------------------------------------- posts
TARGET, SPLIT_OVER = 600, 800          # words per post; split a longer paragraph
SENTENCE = re.compile(r'(?<=[.!?’”])\s+(?=[‘"A-Z])')


def split_long(text):
    """Break a paragraph too long to be a post of its own at sentence ends."""
    words = len(text.split())
    if words <= SPLIT_OVER:
        return [text]
    parts, sentences = [], SENTENCE.split(text)
    per = words / max(1, round(words / TARGET))
    buf = []
    for sentence in sentences:
        buf.append(sentence)
        if len(' '.join(buf).split()) >= per and sentence is not sentences[-1]:
            parts.append(' '.join(buf))
            buf = []
    if buf:
        parts.append(' '.join(buf))
    return parts


def sections():
    """-> list of (numeral, [(kind, text), ...])."""
    out = []
    for kind, text in paragraphs():
        if kind == 'h':
            out.append((text, []))
        elif kind == 'q':
            out[-1][1].append(('q', text))
        else:
            out[-1][1].extend(('p', part) for part in split_long(text))
    return out


def build_posts():
    posts = []
    for numeral, blocks in sections():
        chunks, buf, count = [], [], 0
        for kind, text in blocks:
            words = len(text.split())
            if buf and count + words > SPLIT_OVER:
                chunks.append(buf)
                buf, count = [], 0
            buf.append((kind, text))
            count += words
            if count >= TARGET:
                chunks.append(buf)
                buf, count = [], 0
        if buf:
            if chunks and count < TARGET * 0.4:
                chunks[-1].extend(buf)      # a short tail reads better joined
            else:
                chunks.append(buf)
        for i, chunk in enumerate(chunks, start=1):
            title = f'Part {numeral}'
            slug = f'part-{numeral.lower()}'
            if len(chunks) > 1:
                title += f' ({i} of {len(chunks)})'
                slug += f'-{i}'
            body = []
            if not posts:
                body.append(f'<blockquote><p>{esc(EPIGRAPH[0])}<br>'
                            f'&mdash;{esc(EPIGRAPH[1])}</p></blockquote>')
            for kind, text in chunk:
                body.append(f'<blockquote><p>{esc(text)}</p></blockquote>'
                            if kind == 'q' else f'<p>{esc(text)}</p>')
            posts.append({'title': title, 'slug': slug, 'html': '\n'.join(body)})
    return posts


def main():
    global WORDS
    WORDS = load_words()
    posts = build_posts()
    out = []
    for index, post in enumerate(posts, start=1):
        words = len(re.sub(r'<[^>]+>', ' ', post['html']).split())
        out.append({
            'title': post['title'],
            'url': SOURCE_URL,
            'slug': post['slug'],
            'content_html': post['html'],
            'post_index': index,
            'word_count': words,
            'reading_time_minutes': max(1, round(words / 250)),
        })
    with open(OUT, 'w') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    for post in out:
        print(f"{post['post_index']:3d}  {post['word_count']:5d}w  {post['title']}")
    print(f"\n{len(out)} posts, {sum(p['word_count'] for p in out)} words")
    if UNUSED_FIXES:
        print('\nWARNING: repairs that no longer match:')
        for fix in sorted(UNUSED_FIXES):
            print(f'  {fix[:90]}')


if __name__ == '__main__':
    main()
