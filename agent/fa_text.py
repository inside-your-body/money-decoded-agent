"""Persian text helpers (owner Nov 9): the narrator gets numbers and symbols written out in Persian words; on-screen text stays as written."""
import re

_ONES = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه', 'ده', 'یازده', 'دوازده', 'سیزده', 'چهارده', 'پانزده',
         'شانزده', 'هفده', 'هجده', 'نوزده']
_TENS = ['', '', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود']
_HUND = ['', 'صد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد']
_BIG = [(10 ** 12, 'تریلیون'), (10 ** 9, 'میلیارد'), (10 ** 6, 'میلیون'), (1000, 'هزار')]
_FA_DIG = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


def _three(n):
    out = []
    if n >= 100: out.append(_HUND[n // 100]); n %= 100
    if n >= 20: out.append(_TENS[n // 10]); n %= 10
    if n: out.append(_ONES[n])
    return ' و '.join(out)


def num_words(n):
    n = int(n)
    if n == 0: return 'صفر'
    if n < 0: return 'منفی ' + num_words(-n)
    parts = []
    for v, name in _BIG:
        if n >= v:
            q = n // v; parts.append((num_words(q) if q >= 1000 else _three(q)) + ' ' + name); n %= v
    if n: parts.append(_three(n))
    return ' و '.join(parts).replace('یک هزار', 'هزار', 1) if parts[0].startswith('یک هزار') else ' و '.join(parts)


def _dec(s):
    s = s.replace(',', '').replace('٬', '').replace('٫', '.')
    if '.' in s:
        a, b = s.split('.', 1); b = b.rstrip('0')
        if not b: return num_words(int(a or 0))
        return num_words(int(a or 0)) + ' ممیز ' + num_words(int(b))
    return num_words(int(s))


def speakable(t):
    """'۶۵ میلیارد $' / '$65B' / '12%' / '1987' -> words, so the narrator never guesses."""
    t = t.translate(_FA_DIG)
    t = re.sub(r'\$\s?(\d[\d,]*(?:\.\d+)?)\s?(B|M|K|T)\b', lambda m: _dec(m[1]) + ' ' + {'B': 'میلیارد', 'M': 'میلیون', 'K': 'هزار', 'T': 'تریلیون'}[m[2]] + ' دلار', t)
    t = re.sub(r'\$\s?(\d[\d,]*(?:\.\d+)?)', lambda m: _dec(m[1]) + ' دلار', t)
    t = re.sub(r'(\d[\d,]*(?:\.\d+)?)\s?(%|٪)', lambda m: _dec(m[1]) + ' درصد', t)
    t = re.sub(r'\d[\d,]*(?:\.\d+)?', lambda m: _dec(m[0]), t)
    t = t.replace('$', ' دلار').replace('€', ' یورو').replace('£', ' پوند').replace('%', ' درصد').replace('٪', ' درصد').replace('&', ' و ')
    return re.sub(r'\s+', ' ', t).strip()
