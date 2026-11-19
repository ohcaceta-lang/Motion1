"""Fotos REAIS de figuras públicas e de fatos noticiados (nunca imagens geradas por IA de pessoas reais).

uso:
  python3 buscar_fotos.py wiki "Jensen Huang"                 # Wikimedia Commons: lista fotos com licença e autor
  python3 buscar_fotos.py g1 URL_DA_MATERIA_DO_G1             # fotos da matéria, com legenda e crédito (agência)
  python3 buscar_fotos.py baixar URL arquivo.jpg              # baixa (com user-agent, 3 tentativas)

Prioridade de fontes:
  1. Wikimedia Commons: licença livre (CC BY / CC BY-SA / domínio público). Crédito: "Foto: <autor> / Wikimedia Commons (<licença>)".
  2. Fotos de matérias jornalísticas (G1 etc.), que mostram o fato noticiado (ex.: foto divulgada pela Reuters).
     Crédito obrigatório na tela: "Foto: <agência/veículo>". É uso jornalístico/comentário; avise o usuário que
     fotos de agência têm direitos autorais.
  3. Fotos enviadas pelo próprio usuário.
Hosts necessários: commons.wikimedia.org, upload.wikimedia.org, g1.globo.com, s2-g1.glbimg.com.
"""
import sys, re, html, json, subprocess, urllib.parse, time
UA = 'video-research-bot/1.0'

def get(url):
    return subprocess.run(['curl', '-sSL', '-m', '30', '-A', UA, url], capture_output=True, text=True).stdout

def wiki(q):
    url = ('https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrlimit=12&prop=imageinfo'
           '&iiprop=url|extmetadata|size&iiurlwidth=960&format=json&gsrsearch=' + urllib.parse.quote(q + ' filetype:bitmap'))
    d = None
    for espera in (0, 10, 25):          # o Wikimedia devolve 429 (texto, não JSON) quando há muitas buscas seguidas
        time.sleep(espera)
        try: d = json.loads(get(url)); break
        except ValueError: print(f'Wikimedia limitou as requisições; tentando de novo em instantes...', file=sys.stderr)
    if d is None:
        print('Wikimedia indisponível agora (limite de requisições). Use fotos da matéria (modo g1) ou tente mais tarde.'); return
    for p in d.get('query', {}).get('pages', {}).values():
        ii = p['imageinfo'][0]; m = ii.get('extmetadata', {})
        artist = re.sub('<[^>]+>', '', (m.get('Artist', {}).get('value') or '')).strip()[:50]
        print(f"{p['title']} | {ii['width']}x{ii['height']} | {m.get('LicenseShortName', {}).get('value')} | autor: {artist}\n    {ii.get('thumburl') or ii['url']}")

def g1(url):
    s = get(url)
    for m in re.finditer(r'<figure.*?</figure>', s, re.S):
        f = m.group(0)
        srcs = re.findall(r'https://s2-g1\.glbimg\.com/[^" ]+', f)
        big = [x for x in srcs if '/1000x0/' in x or '/1080x' in x] or srcs
        cap = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', f, re.S)
        if big:
            print('LEGENDA:', html.unescape(re.sub('<[^>]+>', '', cap.group(1))).strip()[:220] if cap else '-')
            print('   ', big[0])

def baixar(url, out):
    for _ in range(3):
        r = subprocess.run(['curl', '-sS', '-m', '60', '-A', UA, '-o', out, url])
        if r.returncode == 0: print('ok', out); return
        time.sleep(5)
    print('falhou', url)

if __name__ == '__main__':
    mode = sys.argv[1]
    {'wiki': lambda: wiki(sys.argv[2]), 'g1': lambda: g1(sys.argv[2]), 'baixar': lambda: baixar(sys.argv[2], sys.argv[3])}[mode]()
