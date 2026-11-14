"""Pesquisa de pauta: o que está em alta e o que a imprensa diz.

uso:
  python3 buscar_em_alta.py trends [BR]                 # Google Trends (buscas em alta + manchetes ligadas)
  python3 buscar_em_alta.py news "termo de busca"       # Google News (títulos, veículo, data)
  python3 buscar_em_alta.py g1 "palavra1,palavra2"      # matérias do G1 (feeds RSS) cujo título contém as palavras
  python3 buscar_em_alta.py ler URL_DO_G1               # texto da matéria (parágrafos)

Hosts necessários na rede do ambiente: trends.google.com, news.google.com, g1.globo.com.
O Google News só devolve links de redirecionamento (não dá para ler a matéria por ele); para ler texto
completo use o modo g1 + ler.
"""
import sys, re, html, subprocess, urllib.parse
import xml.etree.ElementTree as ET

def get(url):
    return subprocess.run(['curl', '-sSL', '-m', '30', url], capture_output=True, text=True).stdout

def trends(geo='BR'):
    ns = {'ht': 'https://trends.google.com/trending/rss'}
    r = ET.fromstring(get(f'https://trends.google.com/trending/rss?geo={geo}'))
    for it in r.iter('item'):
        print('##', it.findtext('title'), '|', it.findtext('ht:approx_traffic', namespaces=ns), '|', (it.findtext('pubDate') or '')[:22])
        for n in it.findall('ht:news_item', ns):
            print('   -', n.findtext('ht:news_item_title', namespaces=ns), '(', n.findtext('ht:news_item_source', namespaces=ns), ')')

def news(q):
    url = 'https://news.google.com/rss/search?q=' + urllib.parse.quote_plus(q) + '&hl=pt-BR&gl=BR&ceid=BR:pt-419'
    r = ET.fromstring(get(url))
    for it in list(r.iter('item'))[:15]:
        print('-', it.findtext('title'), '|', (it.findtext('pubDate') or '')[:16])

def g1(words):
    keys = [w.strip().lower() for w in words.split(',') if w.strip()]
    seen = set()
    for sec in ('economia', 'tecnologia', 'mundo', 'politica', 'pop-arte', 'brasil', 'ciencia', 'saude', 'esporte' ):
        try: r = ET.fromstring(get(f'https://g1.globo.com/rss/g1/{sec}/'))
        except Exception: continue
        for it in r.iter('item'):
            t, l = (it.findtext('title') or '').strip(), it.findtext('link')
            if l not in seen and any(k in t.lower() for k in keys):
                seen.add(l); print(l, '|', t)

def ler(url):
    s = re.sub(r'<script.*?</script>|<style.*?</style>', '', get(url), flags=re.S)
    for m in re.finditer(r'<(p|li|h2)[^>]*>(.*?)</\1>', s, re.S):
        t = html.unescape(re.sub('<[^>]+>', '', m.group(2))).strip()
        t = re.sub(r'\s+', ' ', t)
        if len(t) > 40 and 'newsletter' not in t.lower() and 'Em alta na' not in t: print('-', t)

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'trends'
    arg = sys.argv[2] if len(sys.argv) > 2 else ''
    {'trends': lambda: trends(arg or 'BR'), 'news': lambda: news(arg), 'g1': lambda: g1(arg), 'ler': lambda: ler(arg)}[mode]()
