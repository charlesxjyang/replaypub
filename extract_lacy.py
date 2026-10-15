# -*- coding: utf-8 -*-
"""Build Alex B. Lacy, Jr., *The Development of the White House Office, 1939-1967*
(APSA conference paper, 1967; Nixon Library, White House Special Files box 39 folder 4).

The typewritten scan OCR'd badly, so the prose in `lacy_pages/` is a page-by-page
transcription read off the page images (pdf page index -> pNN.txt); the five
statistical tables are transcribed by hand below and cross-checked against their
own column totals. Endnotes are dropped. Page 18 is missing from the scan and the
foot of several pages is cut off by the photocopy; both are flagged in the text.

Markers in lacy_pages/*.txt:
  @@ABSTRACT        the abstract page
  @@H1 / @@H2 text  section / subsection heading
  @@TABLE_x ... @@ENDTABLE   replaced by the hand-transcribed table x
  @@MISSING text    editorial note rendered in brackets
  @@CONT            paragraph continues across the page break (leading or trailing)
  @@GAP             a line the photocopy cut off
  >                 block quotation

Usage: python extract_lacy.py   ->  lacy_clean.json
"""
import json, os, re, html

PAGES_DIR, OUT = 'lacy_pages', 'lacy_clean.json'
SOURCE_URL = 'https://www.nixonlibrary.gov/sites/default/files/virtuallibrary/documents/whsfreturned/WHSF_Box_39/WHSF39-04.pdf'
BODY_PAGES = list(range(3, 35))   # pdf page indexes; 2 = abstract, 35-39 = footnotes
GAP = ' […] '
TAIL_NOTE = ('The Nixon Library scan breaks off in mid-sentence here: the foot of page 33, '
             'the last page of text in the folder, is cut off in the photocopy.')

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

# ---------------------------------------------------------------- typography
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
    t = re.sub(r'”(?=[A-Za-z])', '” ', t)
    return t.strip()

# ---------------------------------------------------------------- blocks
def page_blocks(pno):
    """-> list of ('head'|'p'|'q'|'table'|'note', text) for one transcribed page."""
    path = os.path.join(PAGES_DIR, f'p{pno:02d}.txt')
    raw = open(path, encoding='utf-8').read()
    out, in_table = [], None
    for chunk in re.split(r'\n\s*\n', raw):
        chunk = chunk.strip()
        if not chunk:
            continue
        if in_table or chunk.startswith('@@TABLE_'):
            if chunk.startswith('@@TABLE_'):
                in_table = chunk.split('@@TABLE_', 1)[1].split()[0].split('\n')[0]
            if '@@ENDTABLE' in chunk:
                out.append(('table', in_table)); in_table = None
            continue
        if chunk.startswith('@@ABSTRACT'):
            chunk = chunk.split('\n', 1)[1].strip() if '\n' in chunk else ''
            if not chunk:
                continue
        while chunk.startswith('@@H1 ') or chunk.startswith('@@H2 '):
            head, _, rest = chunk.partition('\n')
            out.append(('head', head[5:].strip()))
            chunk = rest.strip()
        if not chunk:
            continue
        if chunk.startswith('@@MISSING '):
            out.append(('note', chunk[len('@@MISSING '):].strip()))
            continue
        for para in chunk.split('\n'):
            para = para.strip()
            if not para:
                continue
            kind = 'q' if para.startswith('>') else 'p'
            out.append((kind, para.lstrip('> ').strip()))
    return out

def build_blocks(pages):
    blocks = []
    for pno in pages:
        for kind, text in page_blocks(pno):
            joins = kind in ('p', 'q') and text.startswith('@@CONT')
            text = text.replace('@@CONT', '')
            if joins and blocks and blocks[-1][0] in ('p', 'q'):
                prev_kind, prev = blocks[-1]
                sep = '' if prev.endswith(('-', GAP.rstrip())) else ' '
                blocks[-1] = (prev_kind, (prev.rstrip('-') if prev.endswith('-') else prev) + sep + text)
            else:
                blocks.append((kind, text))
    if blocks and blocks[-1][0] in ('p', 'q'):
        blocks.append(('note', TAIL_NOTE))
    return [(k, t.replace('@@GAP', GAP)) for k, t in blocks]

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
    blocks = [(k, normalise(t)) if k in ('p', 'q') else (k, t) for k, t in build_blocks(BODY_PAGES)]
    sections, cur, title = [], [], 'Introduction'
    carry, from_head = [], False   # a heading straight after a heading leads the next section
    for b in blocks:
        if b[0] == 'head':
            if cur:
                sections.append((title, carry + cur)); carry = []
            elif from_head:
                carry = carry + [('head', title)]
            title, cur, from_head = b[1], [], True
        else:
            cur.append(b)
    if cur: sections.append((title, carry + cur))
    # a heading whose own text is only a lead-in (e.g. the biographical profile) keeps its
    # title and absorbs the following subsection rather than being swallowed by the one before
    folded = []
    for title, bl in sections:
        if folded and wc(folded[-1][1]) < 150 and folded[-1][1] and folded[-1][1][-1][0] != 'head':
            prev_title, prev_bl = folded.pop()
            bl = prev_bl + [('head', title)] + bl
            title = prev_title
        folded.append((title, bl))
    sections = folded
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
    merged = []
    for title, bl in posts:
        if merged and wc(bl) < 150:
            merged[-1] = (merged[-1][0], merged[-1][1] + [('head', title)] + bl)
        else:
            merged.append((title, bl))
    return merged

ABSTRACT_TITLE = 'Abstract'

if __name__ == '__main__':
    abstract = [(k, normalise(t)) for k, t in build_blocks([2]) if k in ('p', 'q')]
    posts = [(ABSTRACT_TITLE, abstract)] + make_posts()
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
