# -*- coding: utf-8 -*-
"""Extract Alex B. Lacy, Jr., *The Development of the White House Office, 1939-1967*
(APSA conference paper, 1967; Nixon Library, White House Special Files box 39 folder 4).

Typewritten scan; the prose is re-OCR'd with Apple Vision (ocrmac) and cross-checked
against tesseract, the five statistical tables are transcribed by hand from the page
images, the endnotes are dropped and page 18 (missing from the scan) is flagged.

Usage: python extract_lacy.py [--audit]   ->  lacy_clean.json
"""
import json, os, re, sys, html, difflib
from collections import Counter

PDF = 'whsf39-04.pdf'
OCR_CACHE, TESS_CACHE, OUT = 'lacy_ocr_vision.json', 'lacy_ocr_tess.json', 'lacy_clean.json'
SOURCE_URL = 'https://www.nixonlibrary.gov/sites/default/files/virtuallibrary/documents/whsfreturned/WHSF_Box_39/WHSF39-04.pdf'
BODY_PAGES = list(range(3, 35))          # pdf page indexes; 2 = abstract, 35-39 = footnotes
AUDIT = '--audit' in sys.argv
audit_log = []
def audit(kind, msg):
    if AUDIT:
        audit_log.append((kind, msg))

def ocr_all():
    if os.path.exists(OCR_CACHE) and os.path.exists(TESS_CACHE):
        return ({int(k): v for k, v in json.load(open(OCR_CACHE)).items()},
                {int(k): v for k, v in json.load(open(TESS_CACHE)).items()})
    import fitz, tempfile, subprocess
    from ocrmac import ocrmac
    d = fitz.open(PDF); vis, tess = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(len(d)):
            p = f'{tmp}/p{i:03d}.png'; d[i].get_pixmap(dpi=300).save(p)
            res = ocrmac.OCR(p, recognition_level='accurate', language_preference=['en-US']).recognize()
            vis[i] = [{'t': t, 'c': c, 'x': b[0], 'y': b[1], 'w': b[2], 'h': b[3]} for t, c, b in res]
            tess[i] = subprocess.run(['tesseract', p, '-', '--psm', '6'], capture_output=True, text=True).stdout
    json.dump(vis, open(OCR_CACHE, 'w'), ensure_ascii=False); json.dump(tess, open(TESS_CACHE, 'w'), ensure_ascii=False)
    return vis, tess
VIS, TESS = ocr_all()

# ---------------------------------------------------------------- dictionary
WORDS = set(w.strip().lower() for w in open('/usr/share/dict/words'))
WORDS |= {'brownlow', 'roosevelt', 'truman', 'eisenhower', 'kennedy', 'johnson', 'rosenman', 'hopkins', 'corcoran',
          'cohen', 'mcintyre', 'hassett', 'niles', 'clifford', 'dawson', 'steelman', 'murphy', 'sorensen', 'sorenson',
          'schlesinger', 'bundy', 'o\'donnell', 'moyers', 'valenti', 'busby', 'califano', 'watson', 'jenkins', 'adams',
          'persons', 'goodpaster', 'hagerty', 'morgan', 'neustadt', 'corwin', 'rossiter', 'koenig', 'hobbs', 'merriam',
          'gulick', 'jefferson', 'mckinley', 'coolidge', 'wilson', 'grant', 'harding', 'hoover', 'dulles', 'stevenson',
          'salinger', 'feldman', 'dungan', 'reedy', 'cater', 'goldman', 'bill', 'ivy', 'ibid', 'op', 'cit', 'et', 'al',
          'fdr', 'hst', 'dde', 'jfk', 'lbj', 'apsa', 'cia', 'negroes', 'negro', 'staffers', 'staffer', 'liaison',
          'institutionalization', 'institutionalized', 'bureaucratization', 'reorganization', 'personnel', 'washington',
          'brookings', 'tulane', 'virginia', 'harvard', 'yale', 'princeton', 'georgetown', 'chicago', 'presidency',
          'presidencies', 'presidential', 'ph', 'll', 'ma', 'jr', 'mr', 'dr', 'vs', 'de', 'la', 'leahy', 'casey', 'wallace',
          'flynn', 'early', 'lyndon', 'baines', 'dwight', 'franklin', 'harry', 'jack', 'ted', 'larry', 'pierre', 'mcgeorge',
          'kenneth', 'ralph', 'myer', 'lawrence', 'theodore', 'arthur', 'walter', 'jack', 'ernest', 'bryce', 'harlow',
          'shanley', 'gray', 'benedict', 'hess', 'emmerich', 'polenberg', 'hoxie', 'egger', 'somers'}
WORDS |= {'began', 'became', 'begun', 'gave', 'took', 'ran', 'went', 'came', 'saw', 'grew', 'knew', 'threw', 'held', 'led', 'met', 'kept',
          'left', 'felt', 'found', 'built', 'sent', 'spent', 'lost', 'meant', 'dealt', 'brought', 'thought', 'bought', 'sought', 'fought',
          'caught', 'taught', 'said', 'made', 'paid', 'laid', 'stood', 'understood', 'told', 'sold', 'wrote', 'written', 'rose', 'chose',
          'chosen', 'spoke', 'broke', 'drove', 'drawn', 'seen', 'done', 'gone', 'been', 'women', 'men', 'children', 'reelected', 'midterm',
          'spokesmen', 'businessmen', 'expertise', 'glamourous', 'glamourized', 'enamoured', 'skilful', 'noticably', 'coordinate',
          'coordinating', 'coordination', 'coordinator', 'coordinated', 'rowe', 'dennison', 'fortas', 'reardon', 'tobin', 'manatos', 'goodwin',
          'jacobsen', 'vaughan', 'rostow', 'stowe', 'currie', 'denver', 'dutton', 'harriman', 'mafia', 'quincy', 'yalta', 'lehand', 'forrestal',
          'kaysen', 'goodpaster', 'koenig', 'komer', 'hatcher', 'dungan', 'shriver', 'rayburn', 'goldfine', 'taft', 'tugwell', 'heinlein',
          'byrnes', 'schwellenbach', 'connelly', 'schoeneman', 'zimmerman', 'lawton', 'lloyd', 'bell', 'wofford', 'busby', 'valenti', 'moyers',
          'jenkins', 'reedy', 'cater', 'macy', 'kintner', 'califano', 'watson', 'early', 'mcintyre', 'hassett', 'niles', 'leahy', 'hopkins',
          'casey', 'flynn', 'wallace', 'corcoran', 'cohen', 'mcreynolds', 'rosenman', 'averell', 'walt', 'carl', 'michael', 'robert', 'ralph',
          'pierre', 'andrew', 'timothy', 'mike', 'henry', 'hall', 'lawrence', 'kenneth', 'theodore', 'myer', 'feldman', 'lee', 'white', 'marguerite',
          'missy', 'eugene', 'samuel', 'luther', 'gulick', 'merriam', 'brownlow', 'hobbs', 'emmerich', 'polenberg', 'rossiter', 'corwin',
          'neustadt', 'sorenson', 'sorensen', 'schlesinger', 'salinger', 'bundy', 'wilson', 'persons', 'morgan', 'harlow', 'shanley', 'gray',
          'carroll', 'adams', 'dulles', 'hagerty', 'stephens', 'whitman', 'anderson', 'minnich', 'rabb', 'jackson', 'cutler', 'morrow', 'areeda',
          'harr', 'dodge', 'hughes', 'snyder', 'stephen', 'hess', 'benedict', 'tulane', 'virginia', 'georgetown', 'princeton', 'harvard', 'yale',
          'columbia', 'stanford', 'chicago', 'michigan', 'wisconsin', 'england', 'ivy', 'perkins', 'francis', 'clifford', 'murphy', 'dawson',
          'steelman', 'smith', 'harold', 'stevenson', 'adlai', 'arthur', 'walter', 'jake', 'jack', 'horace', 'douglass', 'cotter', 'bill',
          'mcnamara', 'abe', 'clark', 'matthew', 'daniel', 'james', 'william', 'lauchlin', 'george', 'raymond', 'lewis', 'paul', 'gerald',
          'bryce', 'gordon', 'sherman', 'rexford', 'donald', 'richard', 'frederick', 'david', 'charles', 'john', 'harry', 'dwight', 'lyndon',
          'franklin', 'thomas', 'woodrow', 'porter', 'short', 'grant', 'jefferson', 'mckinley', 'coolidge', 'hoover', 'harding', 'ike', 'fdr',
          'hst', 'dde', 'jfk', 'lbj', 'mcgeorge', 'tuesday', 'saturday', 'sunday', 'monday', 'american', 'republican', 'republicans', 'democratic',
          'democrats', 'negroes', 'egger', 'somers', 'hoxie', 'seligman', 'fenno', 'koenig'}
def ok(w):
    c = re.sub(r"[^a-z'-]", '', w.lower()).strip("'-")
    c = re.sub(r"'s$", '', c)
    if not c or len(c) == 1 or c in WORDS:
        return True
    for suf, stems in (('s', 1), ('es', 2), ('ed', 2), ('d', 1), ('ing', 3), ('ly', 2), ('ness', 4), ('er', 2), ('est', 3)):
        if c.endswith(suf):
            s = c[:-stems]
            if s in WORDS or s + 'e' in WORDS or (len(s) > 2 and s[-1] == s[-2] and s[:-1] in WORDS):
                return True
    for suf, rep in (('ies', 'y'), ('ied', 'y'), ('ier', 'y'), ('iest', 'y'), ('ment', ''), ('ments', ''), ('ally', 'al')):
        if c.endswith(suf) and (c[:-len(suf)] + rep) in WORDS:
            return True
    if c.startswith(('un', 'non', 're')) and (c[2:] in WORDS or c[3:] in WORDS):
        return True
    if '-' in c and all(ok(p) for p in c.split('-')):
        return True
    return False
def toks(s):
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", s)

# ---------------------------------------------------------------- tables (hand-transcribed from the scan)
def table_html(title, head, rows, notes):
    h = f'<p><strong>{html.escape(title)}</strong></p>\n<table>\n<thead><tr>' + ''.join(f'<th>{html.escape(c)}</th>' for c in head) + '</tr></thead>\n<tbody>\n'
    for r in rows:
        h += '<tr>' + ''.join(f'<td>{html.escape(str(c))}</td>' for c in r) + '</tr>\n'
    h += '</tbody>\n</table>\n' + ''.join(f'<p><small>{html.escape(n)}</small></p>\n' for n in notes)
    return h

TABLES = {
 'I': table_html('Table I. White House Office Budget, 1937–1967', ['Fiscal year', 'Total Personnel', 'Total Obligations Incurred'],
   [(1937, '109,222', '200,000 E*'), (1938, '128,759', '211,380'), (1939, '126,066', '213,160'), (1940, '145,842', '222,900'),
    (1941, '172,005', '222,800'), (1942, '164,448', '224,860'), (1943, '180,782', '226,210'), (1944, '225,789', '302,190'),
    (1945, '235,643', '339,131'), (1946, '250,996', '342,588'), (1947, '772,122', '848,507'), (1948, '1,067,200', '1,194,502'),
    (1949, '1,023,060', '1,123,843'), (1950, '1,185,660', '1,304,735'), (1951, '1,367,294', '1,495,699'), (1952, '1,446,264', '1,609,398'),
    (1953, '1,525,290', '1,732,324'), (1954, '1,435,479', '1,640,452'), (1955, '1,640,038', '1,854,770'), (1956, '1,649,934', '1,877,952'),
    (1957, '1,672,258', '1,846,946'), (1958, '1,748,437', '2,051,970'), (1959, '1,878,940', '2,222,000'), (1960, '1,906,000', '2,221,000'),
    (1961, '2,097,000', '2,478,000'), (1962, '2,003,000', '2,449,000'), (1963, '2,045,000', '2,534,000'), (1964, '2,156,000', '2,717,000'),
    (1965, '2,248,000', '2,841,000'), (1966, '2,435,000 E*', '2,940,000 E*'), (1967, '2,450,000 E*', '2,955,000 E*')],
   ['* Estimate']),
 'II': table_html('Table II. Age Distribution and Average Age at Date of Appointment, White House Office Professional Staff, 1939–1967',
   ['Age', 'FDR¹', 'HST²', 'DDE³', 'JFK⁴', 'LBJ⁵'],
   [('20–29', 0, 1, 4, 0, 1), ('30–39', 2, 6, 27, 10, 4), ('40–49', 4, 7, 25, 12, 18), ('50–59', 7, 4, 22, 1, 4),
    ('60–69', 1, 1, 7, 5, 2), ('Over 69', 0, 0, 1, 0, 0), ('Average Age', '49.6', '44.6', '45.6', '44.9', '45.6')],
   ['¹ Data available for 14 of 16 staff members. ² 19 of 22. ³ 86 of 86. ⁴ 28 of 28. ⁵ 29 of 33.']),
 'III': table_html('Table III. Geographical Origins, White House Office Professional Staff, 1939–1967',
   ['Census Region¹', '% of pop., 1950 census', 'FDR² Birth', 'FDR Prin. loc.', 'HST³ Birth', 'HST Prin. loc.', 'DDE⁴ Birth', 'DDE Prin. loc.',
    'JFK⁵ Birth', 'JFK Prin. loc.', 'LBJ⁶ Birth', 'LBJ Prin. loc.'],
   [('New England', '6%', 0, 2, 3, 1, 11, 8, 5, 8, 4, 5), ('Middle Atlantic', '20%', 0, 2, 5, 3, 25, 33, 8, 3, 8, 6),
    ('South Atlantic', '14%', 3, 7, 3, 14, 8, 25, 1, 12, 1, 14), ('East South Central', '8%', 2, 0, 1, 0, 3, 0, 0, 0, 1, 0),
    ('West South Central', '10%', 1, 0, 1, 0, 4, 1, 1, 1, 6, 2), ('East North Central', '20%', 3, 3, 1, 0, 11, 10, 2, 0, 4, 1),
    ('West North Central', '9%', 3, 0, 5, 2, 9, 2, 4, 1, 1, 0), ('Mountain', '3%', 0, 0, 0, 0, 5, 3, 4, 0, 3, 0),
    ('Pacific', '10%', 0, 0, 1, 0, 4, 4, 1, 3, 0, 1), ('Foreign', '', 2, 0, 0, 0, 6, 0, 2, 0, 0, 0),
    ('Rural*', '', 13, 3, 15, 0, 36, 12, 12, 2, 12, 0), ('Urban', '', 1, 11, 5, 20, 50, 74, 16, 26, 17, 29)],
   ['* Includes small towns.',
    '¹ New England: Me., Vt., N.H., Mass., Conn., R.I. Middle Atlantic: N.Y., Penn., N.J. South Atlantic: Del., Md., D.C., W.Va., Va., N.C., S.C., Ga., Fla. '
    'East South Central: Ky., Tenn., Miss., Ala. West South Central: La., Ark., Tex., Okla. East North Central: Ohio, Ind., Mich., Ill., Wisc. '
    'West North Central: Minn., Iowa, Mo., Kan., Neb., S.D., N.D. Mountain: Mont., Idaho, Wyo., Nev., Utah, Col., Ariz., N. Mex. Pacific: Wash., Ore., Calif., Alas., Hawaii.',
    '² Data available for 14 of 16 staff members. ³ 20 of 22. ⁴ 86 of 86. ⁵ 28 of 28. ⁶ 29 of 33.']),
 'IV': table_html('Table IV. Education, White House Office Professional Staff, 1939–1967',
   ['Educational Level', 'FDR¹', 'HST²', 'DDE³', 'JFK⁴', 'LBJ⁵'],
   [('No college degree*', '6 (42.9%)', '2 (10%)', '14 (16.3%)', '2 (7.1%)', '2 (6.9%)'),
    ("Bachelor's degree*", '7 (50%)', '16 (80%)', '63 (73.3%)', '25 (89.3%)', '25 (86.2%)'),
    ('Advanced degrees', '5 (35.7%)', '13 (65%)', '47 (54.6%)', '18 (64.3%)', '17 (58.6%)'),
    ('— Masters', '1 (7.1%)', '5 (25%)', '18 (21%)', '5 (17.9%)', '4 (13.8%)'),
    ('— LL.B.', '3 (21.4%)', '8 (40%)', '25 (29.1%)', '12 (42.6%)', '10 (34.5%)'),
    ('— Ph.D.', '1 (7.1%)', '1 (5%)', '9 (10.5%)', '4 (14.2%)', '2 (6.9%)'),
    ('— other', '1 (7.1%)', '2 (10%)', '5 (5.8%)', '2 (7.1%)', '2 (6.9%)')],
   ['* The total of the "No College Degree" and "Bachelor\'s Degree" columns may not add up to 100% because some staff members took advanced degrees in lieu of a Bachelor\'s Degree.',
    '¹ Data available for 14 of 16 staff members. ² 20 of 22. ³ 86 of 86. ⁴ 28 of 28. ⁵ 29 of 33.']),
 'V': table_html('Table V. Primary Occupations Before Appointment, White House Office Professional Staff, 1939–1967',
   ['Occupation', 'FDR¹', 'HST²', 'DDE³', 'JFK⁴', 'LBJ⁵'],
   [('Government, non-political', '4 (26.6%)', '11 (55%)', '11 (12.8%)', '11 (39.3%)', '13 (40.6%)'),
    ('— (Staff)', '(2) (13.3%)', '(2) (10%)', '(5) (5.8%)', '(10) (35.7%)', '(10) (31.3%)'),
    ('Politics', '3 (20%)', '0', '8 (9.3%)', '3 (10.7%)', '1 (3.1%)'), ('Business', '2 (13.3%)', '1 (5%)', '26 (30%)', '1 (3.6%)', '7 (21.9%)'),
    ('News Reporting', '4 (26.6%)', '3 (15%)', '6 (7%)', '1 (3.6%)', '3 (9.4%)'), ('Law, private practice', '0', '3 (15%)', '12 (14%)', '4 (14.2%)', '4 (12.5%)'),
    ('Academic', '0', '0', '11 (12.8%)', '7 (25%)', '4 (12.5%)'), ('Military', '1 (6.6%)', '2 (10%)', '7 (8.1%)', '1 (3.1%)', '0'),
    ('Labor', '1 (6.6%)', '0', '0', '0', '0'), ('Student', '0', '0', '5 (5.8%)', '0', '0')],
   ['¹ Data available for 15 of 16 staff members. ² 20 of 22. ³ 86 of 86. ⁴ 28 of 28. ⁵ 32 of 33.']),
}
# (page, table id, first line pattern, last line pattern): lines from first to last are replaced by the table
TABLE_SPANS = [(5, 'I', r'^Table\b.{0,6}$', r'Estimate'), (9, 'II', r'^Table\b.{0,6}$', r'29 o[fr] 33'), (11, 'III', r'^Table\b.{0,6}$', r'29 o[fr] 33'),
               (12, 'IV', r'^Table\b.{0,6}$', r'29 o[fr] 33'), (14, 'V', r'^(Table\b.{0,6}|Primary Occupations Before Appointment.*)$', r'32 o[fr] 33')]

# ---------------------------------------------------------------- lines
TESS_WORDS = {int(k): v for k, v in json.load(open('lacy_ocr_tess_words.json')).items()}
JUNK = re.compile(r"^[^A-Za-z0-9]+$")
JUNK_WORDS = {'SCC', 'Onn', 'nS', 'DEERE', 'EDD', 'EEE', 'IE', 'SIGS', 'LLL', 'ESSS', 'SZm', 'cae', 'LBy', 'VE', 'TT', 'ti', 'ae', 'oy', 'ee', 'oe', 'oo', 'Py', 'Po', 'Oe', 'Lt', 'bi', 'ot', 'ge', 'fa', 'nc', 'Cao', 'EF'}
KEEP_SHORT = {'I', 'a', 'A', 'an', 'in', 'on', 'of', 'to', 'is', 'it', 'as', 'at', 'be', 'by', 'he', 'or', 'so', 'we', 'no', 'if', 'up', 'us', 'do', 'go', 'me', 'my'}

def tess_lines(pno):
    """tesseract words -> cleaned lines (top-down); margin junk, running heads and page numbers dropped."""
    lines = []
    for ws in TESS_WORDS[pno]:
        kept = []
        for w in ws:
            t = w['t']
            junk = (JUNK.match(t) and t not in ('"', '“', '”')) or re.fullmatch(r'\d[!?]', t) or re.sub(r'[^A-Za-z]', '', t) in JUNK_WORDS or re.search(r'[®™&}{]', t)
            core = re.sub(r'[^A-Za-z0-9]', '', t)
            prev_t = ws[ws.index(w) - 1]['t'] if ws.index(w) > 0 else ''
            next_t = ws[ws.index(w) + 1]['t'] if ws.index(w) + 1 < len(ws) else ''
            lone = len(core) == 1 and core not in ('a', 'A', 'I') and not t.endswith('.') and not core.isdigit()
            middigit = core.isdigit() and len(core) <= 2 and w['c'] < 85 and prev_t[-1:].isalpha() and next_t[:1].islower()
            lowconf = lone or middigit or (len(core) <= 2 and ((w['c'] < 60 and core.lower() not in KEEP_SHORT) or t in ('i', 'oy', 'ee', 'ae', 'oe', 'ti')
                                          or (t in ('a', 'A') and w['c'] < 45 and (w is ws[0] or w is ws[-1]))
                                          or (core.isdigit() and w['c'] < 60)))
            if junk or lowconf:
                audit('drop-token', f'p{pno} {t!r} c={w["c"]:.0f} | {" ".join(x["t"] for x in ws)[:60]}')
                continue
            kept.append(w)
        if not kept:
            continue
        t = ' '.join(re.sub(r'^[_~|]+|[_~|]+$', '', w['t']) for w in kept).replace('-~', '-')
        wt = toks(t)
        if wt and len(wt) >= 3 and sum(ok(x) for x in wt) / len(wt) < 0.34:
            audit('drop-line', f'p{pno} {t[:80]!r}')
            continue
        x, x1, y = kept[0]['x'], kept[-1]['x1'], min(w['y'] for w in kept)
        if not re.search(r'[A-Za-z0-9]{2}', t):
            continue
        if y > 0.9 and ('Lacy' in t or 'Development' in t or 'House Office' in t):
            continue
        if y > 0.8 and re.fullmatch(r'\W*\d{1,2}\W*', t):
            continue
        if pno == 3 and y > 0.67:
            continue                                                             # title block on the first page
        if 'Gaylord' in t or 'Garlord' in t or ('MISSI' in t.upper() and 'PA' in t.upper() and len(t) < 20):
            continue
        lines.append({'t': t, 'x': x, 'y': y, 'w': x1 - x})
    return sorted(lines, key=lambda l: -l['y'])

def alnum(w):
    return re.sub(r'[^a-z0-9]', '', w.lower())

def correct_line_texts(pno, lines):
    """Merge with Vision: take Vision's word where tesseract's is not a dictionary word and Vision's is,
    and Vision's punctuation where the words agree."""
    vt = ' '.join(l['t'] for l in sorted(VIS[pno], key=lambda l: -l['y'])).split()
    for l in lines:
        tt = l['t'].split()
        sm = difflib.SequenceMatcher(a=[alnum(w) for w in tt], b=[alnum(w) for w in vt], autojunk=False)
        out, changed = [], False
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                for a, b_ in zip(tt[i1:i2], vt[j1:j2]):
                    if a != b_ and alnum(a) == alnum(b_) and re.search(r'[.,;:!?]$', a + b_):
                        out.append(b_); changed = changed or a != b_
                    else:
                        out.append(a)
            elif tag == 'replace' and i2 - i1 == j2 - j1:
                for a, b_ in zip(tt[i1:i2], vt[j1:j2]):
                    ra, rb = ok(a), ok(b_)
                    if not ra and rb and difflib.SequenceMatcher(a=alnum(a), b=alnum(b_)).ratio() >= 0.6:
                        out.append(b_); changed = True; audit('fix-word', f'p{pno} {a!r} -> {b_!r}')
                    else:
                        out.append(a)
            else:
                out.extend(tt[i1:i2])
        if changed:
            l['t'] = ' '.join(out)
    return lines

vision_lines = tess_lines
HEADINGS = [(r'^A Biographical Profile of the White House', 'A Biographical Profile of the White House Professional Staff, 1939-1967'),
            (r'^Age$', 'Age'), (r'^Geographical Origins$', 'Geographical Origins'), (r'^Education$', 'Education'),
            (r'^Occupation Prior to White House', 'Occupation Prior to White House Appointment'),
            (r'^The Road to the White House$', 'The Road to the White House'), (r'^Turnover$', 'Turnover'), (r'^Salaries$', 'Salaries'),
            (r'^The Organization of the White House Office', 'The Organization of the White House Office, 1939-1967'),
            (r'^.he Roosevelt .hite House Office', 'The Roosevelt White House Office, 1939-1945'),
            (r'^.he Eis\w+ White House Office', 'The Eisenhower White House Office, 1953-1961'),
            (r'^.he Kennedy White House Office', 'The Kennedy White House Office, 1961-1963'),
            (r'^.he Johnson White House Office', 'The Johnson White House Office, 1963-1967'), (r'^Conclusion$', 'Conclusion')]
def heading_for(t):
    t = t.strip(' .:_-')
    for pat, name in HEADINGS:
        if re.search(pat, t):
            return name
    return None

def page_units(pno):
    lines = correct_line_texts(pno, vision_lines(pno))
    spans = [(tid, a, b) for p, tid, a, b in TABLE_SPANS if p == pno]
    units = []
    in_table = None
    xs = Counter(round(l['x'], 2) for l in lines)
    base = min([x for x, n in xs.items() if n >= 3] or [min(xs)])
    prev_y = None
    for i, l in enumerate(lines):
        if in_table:
            if re.search(in_table[1], l['t']):
                in_table = None
            continue
        for tid, a, b in spans:
            if re.search(a, l['t'].strip(' .:_“"‘\'')):
                units.append(('table', tid)); in_table = (tid, b)
                break
        if in_table:
            continue
        gap_before = prev_y is not None and prev_y - l['y'] > 0.022
        h = heading_for(l['t'])
        if h and len(l['t']) < 75:
            units.append(('head', h)); prev_y = l['y']; continue
        if h and len(l['t']) < 100:
            audit('head-missed', f'p{pno} {l["t"]!r} gap={gap_before}')
        nb = [b['x'] for b in lines[max(0, i - 2):i] + lines[i + 1:i + 3]]
        ind = l['x'] > base + 0.018 and l['x'] > (min(nb) if nb else base) + 0.018
        quote = l['x'] > base + 0.075
        units.append(('line', l['t'], ind or gap_before, quote))
        prev_y = l['y']
    return units

# ---------------------------------------------------------------- assemble
def join_hyphen(a, b):
    m = re.search(r'([A-Za-z]+)-$', a); n = re.match(r'([A-Za-z]+)', b)
    if m and n and (ok(m.group(1) + n.group(1)) or (m.group(1) + n.group(1)).lower() in WORDS):
        return a[:-1] + b
    return a + b

NOTE_RE = re.compile(r'(?<![Nn][Oo]\.)(?<!pp\.)(?<!p\.)(?<!Vol\.)(?<![0-9$])(?<=[.,;!?"”’)])\s?(\d{1,2})(?=[\s"”’)]|$)')
def strip_notes(t):
    def rep(m):
        audit('note-marker', f'...{t[max(0, m.start()-40):m.end()+15]}')
        return ''
    return NOTE_RE.sub(rep, t)

import unicodedata
DOC_VOCAB = Counter()
def build_vocab():
    for p in BODY_PAGES + [2]:
        for l in TESS_WORDS[p]:
            for w in l:
                c = re.sub(r"[^a-z]", '', w['t'].lower())
                if c and ok(c):
                    DOC_VOCAB[c] += 1
FUNC = {'in', 'a', 'of', 'the', 'to', 'is', 'it', 'be', 'on', 'at', 'as', 'an', 'had', 'has', 'was', 'and', 'for', 'his'}
def edits1(w):
    L = 'abcdefghijklmnopqrstuvwxyz'
    s = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    return set([a + b[1:] for a, b in s if b] + [a + b[1] + b[0] + b[2:] for a, b in s if len(b) > 1] +
               [a + c + b[1:] for a, b in s if b for c in L] + [a + c + b for a, b in s for c in L])
def spell(word, ctx=''):
    raw = word
    m = re.match(r"^([^A-Za-z]*)([A-Za-z][A-Za-z'’\-]*[A-Za-z]|[A-Za-z])([^A-Za-z]*)$", unicodedata.normalize('NFKD', word).encode('ascii', 'ignore').decode())
    if not m:
        return word
    pre, core, post = m.groups()
    if ok(core) or len(core) < 4 or core.isupper() or "'" in core or '-' in core:
        return word
    low = core.lower()
    # merged function word: "inthe", "ofa", "hada"
    for i in range(1, len(low)):
        a, b = low[:i], low[i:]
        if a in FUNC and (b in WORDS or (len(b) > 3 and ok(b))) and (len(b) > 2 or b == 'a'):
            fixed = (core[:i] + ' ' + core[i:])
            audit('split', f'{raw!r} -> {fixed!r} | {ctx}')
            return pre + fixed + post
    cands = {c for c in edits1(low) if c in WORDS or DOC_VOCAB[c]}
    if not cands and len(low) >= 6:
        cands = {c2 for c in edits1(low) for c2 in edits1(c) if DOC_VOCAB[c2] >= 2}
    if not cands or (core[0].isupper() and not any(DOC_VOCAB[c] >= 5 for c in cands)):
        return word
    if core[0].isupper():
        cands = {c for c in cands if DOC_VOCAB[c] >= 5}
    best = sorted(cands, key=lambda c: (-DOC_VOCAB[c], -(c in WORDS), c))
    if len(best) > 1 and DOC_VOCAB[best[0]] == DOC_VOCAB[best[1]]:
        audit('spell-ambiguous', f'{raw!r} ~ {best[:4]} | {ctx}')
        return word
    fixed = best[0]
    if core[0].isupper():
        fixed = fixed[0].upper() + fixed[1:]
    audit('spell', f'{raw!r} -> {fixed!r} | {ctx}')
    return pre + fixed + post

def spell_all(t):
    if not DOC_VOCAB:
        build_vocab()
    return ' '.join(spell(w, t[:50]) for w in t.split())

def normalise(t):
    t = t.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    t = re.sub(r'"{2,}', '"', t)
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'\s+([;:!?,.])', r'\1', t)
    t = re.sub(r'([.,;:!?])(?=[A-Za-z]{2})', r'\1 ', t)
    t = re.sub(r'\s+-\s+', ' — ', t).replace('--', '—')
    t = re.sub(r'\(\s+', '(', t); t = re.sub(r'\s+\)', ')', t)
    t = re.sub(r"(?<=\w)'(?=\w)", '’', t)
    if t.count('"') % 2 == 0:
        parts = t.split('"'); s = parts[0]
        for i, part in enumerate(parts[1:], 1):
            if i % 2 == 1:
                s = (s.rstrip() + ' ' if s and not s.endswith(('(', '—', ' ')) else s) + '“' + part.lstrip()
            else:
                s = s.rstrip() + '”' + part
        t = s
    else:
        audit('quote-odd', t[:90])
    t = re.sub(r'”(?=[A-Za-z])', '” ', t)
    return t.strip()

def build_blocks(pages):
    """-> list of ('head', text) | ('p', text) | ('q', text) | ('table', id) | ('note', text)"""
    blocks, cur = [], None            # cur = [kind, text]
    def flush():
        nonlocal cur
        if cur and cur[1].strip():
            blocks.append((cur[0], repair(spell_all(repair(normalise(strip_notes(repair(cur[1]))))))))
        cur = None
    for pno in pages:
        for u in page_units(pno):
            if u[0] in ('head', 'table'):
                flush(); blocks.append(u); continue
            _, t, new, quote = u
            kind = 'q' if quote else 'p'
            if cur and (cur[0] != kind):
                # a quote's continuation line is never a new paragraph; a body line after a quote always is
                flush()
            elif cur and new and not (cur[1].endswith('-') and not cur[1].endswith('--')):
                if t[:1].islower() and not re.search(r'[.!?"”’)]\s*$', cur[1]):
                    audit('para-joined', f'p{pno} ...{cur[1][-30:]} | {t[:30]}')
                else:
                    flush()
            if cur is None:
                cur = [kind, t]
            elif cur[1].endswith('-') and not cur[1].endswith('--'):
                cur[1] = join_hyphen(cur[1], t)
            else:
                cur[1] += ' ' + t
        if pno == 19:
            flush(); blocks.append(('note', 'Page 18 of the original paper is missing from the Nixon Library scan; the text resumes on page 19, in the section on the Truman White House Office, 1945-1953.'))
            blocks.append(('head', 'The Truman White House Office, 1945-1953'))
    flush()
    merged = []
    for b in blocks:
        if b[0] in ('p', 'q') and merged and merged[-1][0] in ('p', 'q') and b[1].startswith('You were wasting his time'):
            merged[-1] = (merged[-1][0], merged[-1][1] + ' ' + b[1]); continue
        if b[1] == 'See' and merged and merged[-1][0] in ('p', 'q'):
            merged[-1] = (merged[-1][0], merged[-1][1] + ' [remainder of line illegible in the scan].'); continue
        if b[0] == 'q' and merged and merged[-1][0] == 'q' and not re.search(r'[.!?"\')]\s*$', merged[-1][1]):
            merged[-1] = ('q', merged[-1][1] + ' ' + b[1]); continue
        if b[0] in ('p', 'q') and merged and merged[-1][0] in ('p', 'q') and not re.search(r'[.!?"\')]\s*$', merged[-1][1]) and (b[1][:1].islower() or not b[1][:1].isalpha()):
            merged[-1] = (merged[-1][0], merged[-1][1] + ' ' + b[1]); continue
        if b[1] == 'Boe' and merged and merged[-1][0] == 'p':
            merged[-1] = ('p', merged[-1][1] + ' degree.'); continue
        if b[0] in ('p', 'q') and len(b[1].split()) <= 2 and not any(ok(w) and len(w) > 2 for w in b[1].split()):
            audit('block-dropped', b[1]); continue
        if merged and b[0] == 'p' == merged[-1][0] and b[1][:1].islower() and not re.search(r'[.!?"”’)]\s*$', merged[-1][1]):
            audit('para-merged', f'...{merged[-1][1][-30:]} | {b[1][:30]}')
            merged[-1] = ('p', merged[-1][1] + ' ' + b[1])
        else:
            merged.append(b)
    out = []
    for k, t in merged:
        if k in ('p', 'q'):
            if t.endswith(','):
                t = t[:-1] + '.'
            t2 = re.sub(r', (Most|This|These|Those|However|It|He|They|There|One|As|When|After|Since|Although|But|If|We|His|Their|Each|Several|Many|Few|Only|Some|All|What|Two|Three|Another|During|Both|Because|Before|Even|Under|While|Thus|Moreover|Nevertheless|Perhaps|Finally|First|Second)\b(?! and)', r'. \1', t)
            if t2 != t:
                audit('comma-period', t[:60]); t = t2
        out.append((k, t))
    return out

FIXES = [
    ('"in-gtituidn"', '"institution"'),
    ('work. "Clifford was appointed', 'work. Clifford was appointed'),
    ('it. would be impossible', 'It would be impossible'),
    ("observed. Roosevelt's pattern", "observed, Roosevelt's pattern"),
    ('Arthur! Schlesinger', 'Arthur Schlesinger'),
    ('it me flates', 'it deflates'),
    ('has bean conducted', 'has been conducted'),
    ('one out of See The Ivy', 'one out of seven a Ph.D. The Ivy'),
    ('Ivy League schools awarded of the', 'Ivy League schools awarded 27% of the'),
    ('however. involves,', 'however. It involves,'),
    ('tremor. al3 However', 'tremor." However'),
    ('put in in an interview', 'put it in an interview'),
    ('category Table were', 'category (Table V) were'),
    ('due dates.""""', 'due dates."'),
    ('due dates."" ', 'due dates." '),
    ('on the President? and "For instance', 'on the President?" and "For instance'),
    ('appointed /. rerill Harriman', 'appointed W. Averell Harriman'),
    ('appointed rerill Harriman', 'appointed W. Averell Harriman'),
    ('was "darger than the rest of the White House Office. staff. combined. He never really functioned', 'was larger than the rest of the White House Office staff combined. He never really functioned'),
    ('akin to 4 sense', 'akin to a sense'),
    ('know what was going on. There can be little', 'know what was going on." There can be little'),
    ('to Adams in our study. He was the key', 'to Adams in our study." He was the key'),
    ('rather than stated. Eisenhower and Adams', 'rather than stated." Eisenhower and Adams'),

    ('Security Council "regularly and seriously', 'Security Council regularly and seriously'),
    ('"Cabinet Operations Officer, "later changed', '"Cabinet Operations Officer," later changed'),
    ('that pressure. was being', 'that pressure was being'),
    ('Adams‘ resignation', "Adams' resignation"),
    ('the resignation Sherman Adams gained', 'the resignation of Sherman Adams gained'),
    ('not be able to get you. They were gratified', 'not be able to get you." They were gratified'),
    ('Kennedy staff. "He certainly was', 'Kennedy staff. He certainly was'),
    ("President's trips, Pierre Salinger", "President's trips. Pierre Salinger"),
    ("United States 'should be glamourized", 'United States should be glamourized'),
    ('by the President— because" it would not be proper to do so.', 'by the President because "it would not be proper to do so."'),
    ('"While few, of us had a \'passion for anonymity, \'most of us had a preference in that direction.', '"While few of us had a \'passion for anonymity,\' most of us had a preference in that direction."'),
    ('You can only say what has been done. This is certainly', 'You can only say what has been done." This is certainly'),
    ('in doubt since 1929,', 'in doubt since 1939.'),
    ('Thave already pointed out', 'I have already pointed out'),
    ('it me flates even', 'it deflates even'),
    ('it me- flates even', 'it deflates even'),
    ('saved the 1! Presidency', 'saved the Presidency'),
    ('Plan No. rank', 'Plan No. 1 rank'),
    ('Plan No. l rank', 'Plan No. 1 rank'),
    ('Plan NO. of that', 'Plan No. 1 of that'),
    ('Plan No. of that', 'Plan No. 1 of that'),
    ('constitutional poo mandate', 'constitutional mandate'),
    ('the President.’" a', 'the President.’"'),
    ('the President.\'" a', 'the President.\'"'),
    ('paperisa part', 'paper is a part'), ('{mpoct of', 'impact of'), ('Political §cience', 'Political Science'), ('the sécretary out', 'the secretary out'),
    ('Inthe years se- ar parating', 'In the years separating'), ('Inthe years se- parating', 'In the years separating'), ('presidential gtaff', 'presidential staff'),
    ('to Gongress', 'to Congress'), ('happen-dng', 'happening'), ('staff of. j twentv-seven', 'staff of twenty-seven'), ('twentv-seven', 'twenty-seven'),
    ("Coolidae’s", "Coolidge’s"), ('operating ona budget', 'operating on a budget'), ('$93,520.”', '$93,520.'), ('2 ,845,', '2,845.'), ('2,845,', '2,845.'),
    ('as Fapidly as', 'as rapidly as'), ('in 196] with', 'in 1961 with'), ('over ]00 separate', 'over 100 separate'), ('Plan NO. of that', 'Plan No. 1 of that'),
    ('Reorganization Plan. No. l rank', 'Reorganization Plan No. 1 rank'), ('“in-gtituidn”', '“institution”'), ('in general] and', 'in general and'),
    ('governne nt;', 'government;'), ('constitutional poo mandate', 'constitutional mandate'), ('personal. nl4 Corwin', 'personal." Corwin'),
    ('the Presicent and Cengress', 'the President and Congress'), ('stil! free', 'still free'), ('a manas he can"?', 'a man as he can"?'),
    ('counted asthe leading', 'counted as the leading'), ('Pexford G. Tugwell', 'Rexford G. Tugwell'), ('J. Heinlein has', 'J. C. Heinlein has'),
    ('been written VE by', 'been written by'), ('Office gince 1939', 'Office since 1939'), ('Some fespondents', 'Some respondents'),
    ('House Oftice.', 'House Office.'), ('Ivy League Boe The', 'Ivy League degree. The'), ('over’seventy', 'over seventy'), ('Atlantic ¢ities', 'Atlantic cities'),
    ('business -vorld', 'business world'), ('any parti-. cular region', 'any particular region'), ('overrepresanted', 'overrepresented'),
    ('improved_since', 'improved since'), ('of re- I spondents', 'of respondents'), ("Roosevelt’s. Daniel J, Tobin", "Roosevelt’s Daniel J. Tobin"),
    ('Demecratic precinct', 'Democratic precinct'), ('like McGeorge i Roky, Walt Rastow, end Actheor Ssllesingsr, Jr. had been ecvising from the siselines',
     'like McGeorge Bundy, Walt Rostow, and Arthur Schlesinger, Jr. had been advising from the sidelines'),
    ('although Jenn R. Steelman', 'although John R. Steelman'), ('staffmembers I. For', 'staff members. For'), ('House sdlaries severa] of', 'House salaries, several of'),
    ('was ina -very personal', 'was in a very personal'), ('could not per- 7 sonally', 'could not personally'), ('In so farasI can', 'In so far as I can'),
    ('Office bay-gol in 1944', 'Office payroll in 1944'), ('Tne big changes', 'The big changes'), ('be-rowing process', 'borrowing process'),
    ('one Roosevell nlatt member', 'one Roosevelt staff member'), ('with his pealt were', 'with his staff were'), ('feeling fora cardinal', 'feeling for a cardinal'),
    ('calling him. <A big', 'calling him. A big'), ('more-help. "', 'more help."'), ('Watson dies_at sea abroad the', 'Watson died at sea aboard the'),
    ('Mc-Reynolds developed', 'McReynolds developed'), ('valua-~ ble', 'valuable'), ('in no sgyse a chief', 'in no sense a chief'), ('Hopking! role', "Hopkins’ role"),
    ('inter-“ested', 'interested'), ('Commander-in Chief” held by Adm. William D Leahy', 'Commander-in-Chief” held by Adm. William D. Leahy'),
    ('Adm.: ', 'Adm. '), ('necessitate] zpecial', 'necessitated special'), ('W. /. rerill Harriman', 'W. Averell Harriman'), ('Harrin7~ sat', 'Harriman sat'),
    ('the ccordination of', 'the coordination of'), ('The day becin with', 'The day began with'),
    ('attended by most of ths sen ee tae Te tha narlu manthe thece conferences wore held at 8:69', 'attended by most of the staff members. In the early months these conferences were held at 8:00 or 8:30 [A.M. The]'),
    ('interest in the EF; Cao Dennison', 'interest in the F.B.I. Dennison'), ('in especially nigh regard', 'in especially high regard'),
    ('men_continued', 'men continued'), ("Poosevelt’s example", "Roosevelt’s example"), ('of “Tne Assistant', 'of “The Assistant'), ('Specia! Counsel', 'Special Counsel'),
    ('to the Presi dent.', 'to the President.'), ('Johan R. Ste~lman', 'John R. Steelman'), ('executive “cn3rtments and 7 agencies', 'executive departments and agencies'),
    ('executive “cn3rtments and agencies', 'executive departments and agencies'), ('He ‘andled', 'He handled'), ('agency, oy althougi: Harold', 'agency, although Harold'),
    ('agency, althougi: Harold', 'agency, although Harold'), ('end Feo’crick Lawton', 'and Frederick Lawton'), ('them Inter returned', 'them later returned'),
    ('for_writing', 'for writing'), ('for_drafting', 'for drafting'), ('and patro-__ mage.', 'and patronage.'), ('out ef-Congress', 'out of Congress'),
    ('Murphy and *-wson the', 'Murphy and Dawson the'), ('Truman Administvation', 'Truman Administration'), ('development cf an able cadre. _of', 'development of an able cadre of'),
    ('he uid i make', 'he did make'), ('he uid make', 'he did make'), ('the "O.K., S’A. was affixed', 'the "O.K., S.A." was affixed'),
    ('directive frog the President', 'directive from the President'), ('responsiblities', 'responsibilities'), ('ard, if it had', 'and, if it had'),
    ('describes him as” the man', 'describes him as “the man'), ('as much order as nossihle inta wanting', 'as much order as possible into running the'),
    ('immed-fate predecessors', 'immediate predecessors'), ('predisncsitions', 'predispositions'), ('They ad some responsibility', 'They had some responsibility'),
    ('Republicans in Cungress', 'Republicans in Congress'), ('the Nationa! Security', 'the National Security'), ('coordina’ tion for him', 'coordination for him'),
    ('knew “now, to he made the decision', 'knew “how he made the decision'), ('Assitant to the Pygsicent', 'Assistant to the President'),
    ('held by A. senior staff', 'held by a senior staff'), ('Mostof the', 'Most of the'), ('Most-of the', 'Most of the'), ('resignation ge Sherman Adams', 'resignation of Sherman Adams'),
    ('had been f "masterminded" from Sam Rayburn’s office fa political reasons. They knew that f pressure. was', 'had been "masterminded" from Sam Rayburn’s office for political reasons. They knew that pressure was'),
    ('coordinatedall', 'coordinated all'), ('strong °., kand. of Adams', 'strong hand of Adams'), ('to be i done?', 'to be done?'),
    ('and on Saturday marainne and Gundau afearnnnann thas cece atin as', 'and on Saturday mornings and Sunday afternoons [remainder of line illegible in the scan].'),
    ('Since Kennedy dropped the bi cenhower soso} ST SInTT Deceiany 0 Domnall also kept', 'Since Kennedy dropped the Eisenhower position of Staff Secretary, O’Donnell also kept'),
    ('a gperk in his own office', 'a clerk in his own office'), ('including tariftS and wade. qHe-IS0 Supervised the drafting of Presidential proclama-. ‘tions',
     'including tariffs and trade. He also supervised the drafting of Presidential proclamations'), ('coordination " with Robert Kennedy', 'coordination with Robert Kennedy'),
    ('pardons pardons and and pleas pleas for for clemency. clemency, Good Goodwin', 'pardons and pleas for clemency. Goodwin'), ('affairs. i', 'affairs.'),
    ('complex national i security', 'complex national security'), ('the White. House. However, where Liseniower’s national security advisers in the White House 7 “WEYE primarily',
     'the White House. However, where Eisenhower’s national security advisers in the White House were primarily'), ('the vast and com-, i plex activities', 'the vast and complex activities'),
    ('the be Bundy team', 'the Bundy team'), ('personality Suited him', 'personality suited him'), ('Bundy. wes assisted', 'Bundy was assisted'),
    ('“Little State Depariment.', '“Little State Department.”'), ('in some Tespects resenibled', 'in some respects resembled'), ('specialist for_ European', 'specialist for European'),
    ('Far Eastern A. fairs', 'Far Eastern Affairs'), ('the same i office', 'the same office'), ("MclIntyre’s", "McIntyre’s"), ('in this respect,, handled', 'in this respect), handled'),
    ('F.B.1.', 'F.B.I.'), ('in BIS memoirs', 'in his memoirs'), ("Kennecy attracted unprecedenied public attention. to", "Kennedy attracted unprecedented public attention to"),
    ('Mostcf the', 'Most of the'), ('of them putit,', 'of them put it,'), ('stories akout them', 'stories about them'), ('constantly i in the news', 'constantly in the news'),
    ('mass circulation i magazines', 'mass circulation magazines'), ('their own i men', 'their own men'), ('had 4 ‘passion', 'had a ‘passion'),
    ('Even the keenest 7 i observer', 'Even the keenest observer'), ('advisinga ‘President', 'advising a President'), ('staffing practices 7 which', 'staffing practices which'),
    ('serve the ‘President in very personal', 'serve the President in a very personal'), ('unheard of behavior “for', 'unheard of behavior” for'),
    ('a “hard boss “and “a difficult', 'a “hard boss” and “a difficult'), ('to bed, early to rise “advocate', 'to bed, early to rise” advocate'),
    ('knew that” he didn’t', 'knew that “he didn’t'), ('from 7:00 to 7:00 P. M.', 'from 7:00 A.M. to 7:00 P.M.'), ('after Goldfine', 'after the Goldfine'),
    ('Eiscnhower wanted', 'Eisenhower wanted'), ('clearly Structured hierarchy', 'clearly structured hierarchy'), ('Adams, was, in every', 'Adams was, in every'),
    ('the White House. “Adams listened', 'the White House. Adams listened'), ('among 7 other staff. members', 'among other staff members'),
    ('difficulty 7 in persuading', 'difficulty in persuading'), ('He i was highly', 'He was highly'), ('in the i White House', 'in the White House'),
    ('Office with 7 valuable', 'Office with valuable'), ('the Office, of Defense', 'the Office of Defense'), ('DEERE Ei EDD EEE EEE IE SIGS', ''),
    ('Byrnes had had unusual', 'Byrnes had had unusual'), ('some-~ thing akin to 4 sense', 'something akin to a sense'), ('unanimous-~ ly replied', 'unanimously replied'),
    ('key staff, members', 'key staff members'), ('more thin a dozen', 'more than a dozen'), ('"Wore the professional', '"Were the professional'),
    ('on the staff?!, the', 'on the staff?", the'), ('“darger than the rest of the White House Office. staff. combined. He never really i functioned', 'larger than the rest of the White House Office staff combined. He never really functioned'),
    ('with him! were formal and cool', 'with him were formal and cool'), ('the “staff felt low"', 'the "staff felt low"'), ('a Chief of Staff. He was', 'a Chief of Staff. He was'),
    ('and Sherman Adams from the staff', 'and Sherman Adams from the staff'), ('Eisenhower Presidency the President’s two lengthy illnesses', 'Eisenhower Presidency: the President’s two lengthy illnesses'),
    ('the staff. organization and the genius', 'the staff organization and the genius'), ('“Eisenhower’s critics', 'Eisenhower’s critics'),
    ('routine. “Most of the respondents', 'routine. Most of the respondents'), ('settled that Adams', 'settled: that Adams'), ('more easy going willing', 'more easy going, willing'),
    ('Eisenhower used the Nationa! Security Council “regularly', 'Eisenhower used the National Security Council regularly'), ('great respect, “exerted', 'great respect, exerted'),
    ('It was in the difficult early months of his Administration', 'It was in the difficult early months of his Administration'), ('and a Special Assitant', 'and a Special Assistant'),
    ('Board. “The first position', 'Board. The first position'), ('‘The task of coordinating', 'The task of coordinating'), ('a very important, one', 'a very important one'),
    ('Sorenson has written, “decided what it is he need not decide."', 'Sorenson has written, "decided what it is he need not decide."'),
    ('of others," There was', 'of others." There was'), ('assignments, personally, received', 'assignments personally, received'), ('from his, top aides', 'from his top aides'),
    ('His position was made firm', 'His position was made firm'), ('agriculture matters,', 'agriculture matters.'), ('assignment.. There', 'assignment. There'),
    ('occaSional "jockeying for position.', 'occasional "jockeying for position."'), ('deadlines set by due dates.', 'deadlines set by due dates."'),
    ('with distinction on the United States Conciliation', 'with distinction in the United States Conciliation'), ('as "The Assistant to the President. Steelman had', 'as "The Assistant to the President." Steelman had'),
    ('staff-for policy', 'staff for policy'), ('began to do much of Rosenman’s work. “Clifford was', 'began to do much of Rosenman’s work. Clifford was'),
    ('for one politician." However', 'for one politician." However'), ('“i though a good many', 'though a good many'), ('i made with you', 'made with you'),
    ('White House job? and "What', 'White House job?" and "What'), ('he bumped. into', 'he bumped into'), ('Table JI indicate', 'Table II indicate'),
    ('average age of “the Kennedy', 'average age of the Kennedy'), ('and the i average age', 'and the average age'), ('the Truman staff, a', 'the Truman staff.'),
    ('Rossiter has put it,” We can never again talk about it the Presidency) sensibly without accounting for ‘the men around the President!',
     'Rossiter has put it, "We can never again talk about [the Presidency] sensibly without accounting for ‘the men around the President.’"'),
    ('constitutional at developments', 'constitutional developments'), ('development of staff, po However', 'development of staff. However'), ('development of staff,', 'development of staff.'),
    ('Presidency What have', 'Presidency? What have'), ('“institutionalization" of i the office', '“institutionalization" of the office'), ('he can"? a In order', 'he can"? In order'),
    ('the five a presidents', 'the five presidents'), ('decision-making? a', 'decision-making?'), ('radical amendment,', 'radical amendment.'),
    ('the 7 relationship', 'the relationship'), ('sides of the argument. Rossiter', 'sides of the argument. Rossiter'), ('the “institutionalization"', 'the "institutionalization"'),
    ('recognition value of the job." 1', 'recognition value of the job."'), ('to be counted asthe', 'to be counted as the'), ('the momentous administrative', 'the momentous administrative'),
    ('The debate is familiar one', 'The debate is a familiar one'), ('Professors Rossiter and Corwin wrote', 'Professors Rossiter and Corwin wrote'),
    ('ninety minutes. The i', 'ninety minutes. The'), ('were born rural areas', 'were born in rural areas'), ('ee Primary Occupations', 'Primary Occupations'),
    ('Goverment, non', 'Government, non'), ('World War Il', 'World War II'), ('Administrative Assistants (six had been authorized) were added', 'Administrative Assistants (six had been authorized) were added'),
    ('a title S| especially', 'a title especially'), ('interest - for t instance', 'interest - for instance'), ('who usually a occupied', 'who usually occupied'),
    ('a very “4 special one', 'a very special one'), ('Hopkins was a very special', 'Hopkins was a very special'), ('Truman would iron them out here.', 'Truman would iron them out here.'),
    ('doing be informed, know', 'doing, be informed, know'), ('Every staff man could hear', 'Every staff man could hear'), ('r The Truman staff members felt', 'The Truman staff members felt'),
    ('extensive experience with © J military staff', 'extensive experience with military staff'), ('President Py in the national', 'President in the national'),
    ('Administra- 4 sons', 'Administration and Persons'), ('gener- 1 ous', 'generous'), ('was a sign t most part', 'was a sign that it was Adams and not Eisenhower who had been running the Presidency for the most part'),
    ('more easy going - Po willing', 'more easy going, willing'), ('ought to be i done', 'ought to be done'), ('by Persons and the Lt nature', 'by Persons and the nature'),
    ('his assistants 1 were needed', 'his assistants were needed'), ('Bundy’s i own training', 'Bundy’s own training'), ('He would not have Oe f been', 'He would not have been'),
    ('(Robert Komer). ~— oe', '(Robert Komer).'), ('O’Donnell occupied the same i office', 'O’Donnell occupied the same office'), ('a Presidential i staff position', 'a Presidential staff position'),
    ('from the departments ee', 'from the departments'), ('Clifford. The nc’ ’ SCC Onn nS, latter', 'Clifford. The latter'), ('among a the most glamourous', 'among the most glamourous'),
    ('%-.7-kins had been', 'Jenkins had been'), ('Clifford ot about', 'Clifford about'), ('Althoughhe has.found', 'Although he has found'), ('private sector, The most', 'private sector. The most'),
    ('the Presi-— dent.', 'the President.'), ('the i next.', 'the next.'), ('in 1967 is bi staggering', 'in 1967 is staggering'), ('expansion of 7 the staff', 'expansion of the staff'),
    ('extent ~- especially', 'extent - especially'), ('3:00-5:00 P. Ni.', '3:00-5:00 P.M.'), ('A. M.', 'A.M.'), ('P. M.', 'P.M.'), ('members. 7 David Stowe', 'members. David Stowe'),
    ('matters. 7 But the great', 'matters. But the great'), ('decisions. 7 He frequently', 'decisions. He frequently'), ('publicity White. 7 House staff', 'publicity White House staff'),
    ('term. 7 Matthew', 'term. Matthew'), ('appearances. 7', 'appearances.'), ('much, " 4', 'much."'), ('much, "', 'much."'), ('useful. 7', 'useful.'), ('the assassination. However, 7', 'the assassination. However,'),
    ('Truman Administration that the Bureau', 'Truman Administration that the Bureau'), ('the twentieth-century governme nt', 'the twentieth-century government'),
    ('“cn3rtments', 'departments'), ('7 government, 18 and', 'government, and'), ('in the federal 7 government', 'in the federal government'),
    ('the White House Oftice', 'the White House Office'), ('Reorganization Act of 1939 and Rec organization Plan', 'Reorganization Act of 1939 and Reorganization Plan'),
    ('“the men around the President! 9 a', '“the men around the President.”'), ('Whai', 'What'), ('whal', 'what'), ('Hitle', 'little'), ('svggest,', 'suggest,'), ('siggest,', 'suggest,'),
    ('håd', 'had'), ('g{ ', 'of '), ('foreign-born. if', 'foreign-born.'), ('was got within the sphere', 'was not within the sphere'), ('[A.M. The] or hour was', '[A.M. The] hour was'),
    ('Gcodpaster', 'Goodpaster'), ('patro-mage', 'patronage'), ('a “hard boss “and difficult man to get along with”', 'a “hard boss” and “a difficult man to get along with”'),
    ('a "hard boss "and difficult man to get along with"', 'a "hard boss" and "a difficult man to get along with"'),
    ('the Middle Atlantic  ¢ities. the other hand', 'the Middle Atlantic cities. On the other hand'), ('Atlantic ¢ities. the other hand', 'Atlantic cities. On the other hand'),
    ("Roosevelt's. Daniel Tobin", "Roosevelt's Daniel J. Tobin"), ('professional staffmembers', 'professional staff members'), ('confidence ina man', 'confidence in a man'),
    ('out ofa man', 'out of a man'), ('office ina general', 'office in a general'), ('who sucaested that', 'who suggested that'), ('organization guaryntees', 'organization guarantees'),
    ('Board. “The first position was held by A. senior', 'Board. The first position was held by a senior'), ('Board. "The first position was held by A. senior', 'Board. The first position was held by a senior'),
    ('legislative Maison activities', 'legislative liaison activities'), ('departments Nene emma', 'departments.'), ('the tyne of staff', 'the type of staff'),
    ('as big aman as heven." Infect, the White House Office stefi gives the Fresident a chance to c’v:-come', 'as big a man as he can." In fact, the White House Office staff gives the President a chance to overcome'),
    ('com-, plex activities', 'complex activities'), ("MclIntyre's", "McIntyre's"), ('Ivy League Boe', 'Ivy League degree.'),
    ('Ivy League Boe The', 'Ivy League degree. The'), ('constitutional poo mandate', 'constitutional mandate'), ('Thenterview schedule', 'The interview schedule'),
    ('saved the 1! Presidency', 'saved the Presidency'), ('birthplace. 2? Their', 'birthplace. Their'), ('members. j 4 Data', 'members. 4 Data'),
    ('for both 2 bachelor’s', 'for both bachelor’s'), ('months. j Political', 'months. Political'), ('category Table V were', 'category (Table V) were'),
    ('frequently do. 38 However', 'frequently do. However'), ('Murphy to t coordinate', 'Murphy to coordinate'), ('he did f gather', 'he did gather'),
    ('9:00 or 9:30 The staff', '9:00 or 9:30 A.M. The staff'), ('set Jaside', 'set aside'), ('out of a t group', 'out of a group'), ('three staff t members', 'three staff members'),
    ("Kennecy'‘s first Congress", "Kennedy’s first Congress"), ('practices had 4 Significant', 'practices had a significant'),
    ('like McGeorge Roky, Walt Rastow, end Actheor Ssllesingsr, Jr. had been ecvising from the siselines', 'like McGeorge Bundy, Walt Rostow, and Arthur Schlesinger, Jr. had been advising from the sidelines'),
    ('The Roosevelt *Vhite House', 'The Roosevelt White House'), ('development cf an able cadre. of', 'development of an able cadre of'), ('Harrin7 sat', 'Harriman sat'),
    ('attended by most of ths sen tae tha narlu manthe thece conferences wore held at 8:69', 'attended by most of the staff members. In the early months these conferences were held at 8:00 or 8:30 [A.M. The]'),
    ('Presi-. dency', 'Presidency'), ('such, alent for', 'such a talent for'), ('coordi-nation of', 'coordination of'), ('the Persons~Morgan staii-. prepared', 'the Persons-Morgan staff prepared'),
    ('illustrative. af the', 'illustrative of the'), ('confirmed by tng transition', 'confirmed by the transition'), ('the White. House. However, where Liseniower’s', 'the White House. However, where Eisenhower’s'),
    ('White House “WEYE primarily', 'White House were primarily'), ('dropped the cenhower ST SInTT Deceiany Domnall also kept', 'dropped the Eisenhower position of Staff Secretary, O’Donnell also kept'),
    ('departments Nene emma Arthur! Schlesinger', 'departments. Arthur Schlesinger'), ('idea mapoin the White House', 'idea man in the White House'),
    ('by no means YHS CXCTUSIVE Salt member', 'by no means the exclusive staff member'), ('Administration. Fost of the', 'Administration. Most of the'),
    ('as big aman as heven.” Infect, the White House Office stefi gives the Fresident a chance to c’v:-come', 'as big a man as he can.” In fact, the White House Office staff gives the President a chance to overcome'),
    ('been erueial tn fact it mav be', 'been crucial. In fact it may be'), ('permitted a lrroer staff', 'permitted a larger staff'), ('respondents inthis study', 'respondents in this study'),
    ('an expanded personnal staff', 'an expanded personal staff'), ('sharp contrast. to the', 'sharp contrast to the'), ('own “staff system “until', 'own “staff system” until'),
    ('(no women held', '(no women held'), ('World War Il', 'World War II'), ('Reorganization Plan. No.', 'Reorganization Plan No.'),
    ('the expansion Of the', 'the expansion of the'), ('interesting Observations', 'interesting observations'), ('"Every staff man could hear what his colleagues were doing be informed, know what was going on.', '"Every staff man could hear what his colleagues were doing, be informed, know what was going on."'),
    ('recommendation. "', 'recommendation."'), ('“Adams listened and said, ‘Well, what do you want me to do about it?"', '"Adams listened and said, ‘Well, what do you want me to do about it?’'),
    ('the White House. Adams listened', 'the White House. "Adams listened'), ('office political reasons', 'office for political reasons'),
    ('"The Assistant to the President. Steelman', '"The Assistant to the President." Steelman'), ('at 8:69', 'at 8:00'), ('Truman staff, a', 'Truman staff.'),
]
REGEX_FIXES = [
    (r'most of ths sen .*? conferences wore held at 8:\d\d', 'most of the staff members. In the early months these conferences were held at 8:00 or 8:30 [A.M. The]'),
    (r'Pro- \w{1,3} fessors', 'Professors'), (r'do about it\?["”] You were wasting', 'do about it?’ You were wasting'), (r"the men around the President[!.]['’]?\s*a?\s*$", "the men around the President.'\""),
    (r"(O\.K\., S)[’']A\.(?![\"”])", '\\1.A."'), (r'and one out of See\b\.?', 'and one out of [remainder of line illegible in the scan].'),
    (r"explosive for the White House\.[\"”] Adams listened and said, [‘']Well, what do you want me to do about( it\?[’']?)?", "explosive for the White House. \"Adams listened and said, ‘Well, what do you want me to do about it?’"), (r'individual in modern times\.(?!["”])', 'individual in modern times."'),
    (r"the men around the President\.(['’])\s*a?$", "the men around the President.\\1\""), (r'set by due dates\.(?!["”])', 'set by due dates."'), (r"around the President\.'(?!\")", "around the President.'\""), (r'proper to do so\.(?!")', 'proper to do so."'),
    (r'of Adams\. "Eisenhower', 'of Adams. Eisenhower'), (r'saved the (\d\S? )?Presidency from', 'saved the Presidency from'), (r'bio- \w{1,3} graphical', 'biographical'), (r'the 1! Presidency', 'the Presidency'),
]
FIX_HITS = Counter()
def repair(t):
    for pat, rep in REGEX_FIXES:
        t = re.sub(pat, rep, t)
    for a, b in FIXES:
        if a in t:
            FIX_HITS[a] += 1
            t = t.replace(a, b)
    return t

# ---------------------------------------------------------------- posts
TARGET, SPLIT_ABOVE = 600, 900
def esc(s): return html.escape(s, quote=False)
def render(blocks):
    out = []
    for k, t in blocks:
        if k == 'head': out.append(f'<h2>{esc(t)}</h2>')
        elif k == 'p': out.append(f'<p>{esc(t)}</p>')
        elif k == 'q': out.append(f'<blockquote><p>{esc(t)}</p></blockquote>')
        elif k == 'table': out.append(TABLES[t])
        elif k == 'note': out.append(f'<p><em>[{esc(t)}]</em></p>')
    return '\n'.join(out)
def wc(blocks):
    return sum(len(t.split()) for k, t in blocks if k in ('p', 'q', 'note')) + sum(120 for k, t in blocks if k == 'table')

def make_posts():
    blocks = [(k, normalise(repair(t))) if k in ('p', 'q') else (k, t) for k, t in build_blocks(BODY_PAGES)]
    # sections: split at headings
    sections, cur, title = [], [], 'Introduction'
    for b in blocks:
        if b[0] == 'head':
            if cur: sections.append((title, cur))
            title, cur = b[1], []
        else:
            cur.append(b)
    if cur: sections.append((title, cur))
    # chunk each section
    posts = []
    for title, bl in sections:
        n = max(1, round(wc(bl) / TARGET)) if wc(bl) > SPLIT_ABOVE else 1
        if n == 1:
            posts.append((title, bl)); continue
        per = wc(bl) / n; pieces, piece, acc = [], [], 0
        for b in bl:
            w = wc([b])
            if piece and acc + w / 2 > per and len(pieces) < n - 1:
                pieces.append(piece); piece, acc = [], 0
            piece.append(b); acc += w
        if piece: pieces.append(piece)
        for i, piece in enumerate(pieces, 1):
            posts.append((f'{title} ({i} of {len(pieces)})', piece))
    # merge tiny posts into the previous one
    merged = []
    for title, bl in posts:
        if merged and wc(bl) < 150:
            merged[-1] = (merged[-1][0], merged[-1][1] + [('head', title)] + bl)
        else:
            merged.append((title, bl))
    return merged

ABSTRACT_TITLE = 'Abstract'

if __name__ == '__main__':
    posts = []
    abstract = build_blocks([2])
    abstract = [(k, normalise(repair(t))) for k, t in abstract if k in ('p', 'q') and not t.startswith(('Abstract', 'by Alex', 'Woodrow', 'University', 'Prepared', 'Association'))]
    posts.append((ABSTRACT_TITLE, abstract))
    posts += make_posts()
    out = []
    for idx, (title, bl) in enumerate(posts, 1):
        body = render(bl)
        words = len(re.sub(r'<[^>]+>', ' ', body).split())
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        out.append({'title': title, 'url': SOURCE_URL, 'slug': slug, 'content_html': body, 'post_index': idx,
                    'word_count': words, 'reading_time_minutes': max(1, round(words / 250))})
    json.dump(out, open(OUT, 'w'), indent=2, ensure_ascii=False)
    for p in out:
        print(f"{p['post_index']:2d}  {p['word_count']:4d}w  {p['title']}")
    print(f"\n{len(out)} posts, {sum(p['word_count'] for p in out)} words -> {OUT}")
    if AUDIT:
        with open('lacy_audit.txt', 'w') as f:
            for kind, msg in audit_log: f.write(f'{kind:12s} {msg}\n')
            f.write('\n== unknown words ==\n'); seen = Counter()
            for p in out:
                ws = re.sub(r'<[^>]+>', ' ', p['content_html']).split()
                for i, w in enumerate(ws):
                    if not ok(w) and seen[w] < 2:
                        seen[w] += 1; f.write(f"{p['post_index']:2d}: {w!r:22s} | {' '.join(ws[max(0,i-5):i+6])}\n")
        with open('lacy_audit.txt', 'a') as f:
            f.write('\n== unmatched fixes ==\n')
            for a, b in FIXES:
                if FIX_HITS[a] == 0:
                    f.write(f'  {a!r}\n')
        print('audit -> lacy_audit.txt')
