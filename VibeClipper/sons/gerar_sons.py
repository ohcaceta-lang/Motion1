"""VibeClipper: gera os 3 efeitos sonoros da skill por código (nenhum arquivo de terceiro, nada baixado da internet).

  python sons/gerar_sons.py            # grava whoosh.wav, whoosh-2.wav e pop.wav nesta pasta

  - whoosh.wav   (o zoom entra): ruído filtrado com a frequência subindo, cresce, passa da esquerda pra direita e some;
  - whoosh-2.wav (o zoom sai): o mesmo, mais grave e com a frequência descendo;
  - pop.wav      (palavra de destaque): uma senoide curta que cai de tom, com ataque rápido e queda rápida.
É determinístico (semente fixa): rodar de novo grava exatamente os mesmos arquivos. Só precisa do numpy.
Os sons são seus: pode usar, mudar e distribuir à vontade.
"""
import math
import os
import wave

import numpy as np

SR = 48000
AQUI = os.path.dirname(os.path.abspath(__file__))


def envelope(n, pico, subida=2.2, queda=3.0):
    """Sobe até `pico` (0 a 1 da duração) e cai, com curvas suaves; começa e termina em zero."""
    t = np.linspace(0.0, 1.0, n)
    sobe = np.clip(t / pico, 0, 1) ** subida
    desce = np.clip((1 - t) / (1 - pico), 0, 1) ** queda
    return np.where(t <= pico, sobe, desce)


def passa_banda(x, fc, q=1.6):
    """Filtro de estado variável (Chamberlin) com a frequência central mudando amostra a amostra: devolve a banda."""
    baixo = banda = 0.0
    out = np.empty_like(x)
    amort = 1.0 / q
    for i in range(len(x)):
        f = 2.0 * math.sin(math.pi * min(fc[i], SR / 7) / SR)
        alto = x[i] - baixo - amort * banda
        banda += f * alto
        baixo += f * banda
        out[i] = banda
    return out


def whoosh(dur, f_ini, f_fim, pico, semente, pan=(-0.6, 0.6)):
    n = int(dur * SR)
    rng = np.random.default_rng(semente)
    t = np.linspace(0.0, 1.0, n)
    fc = f_ini * (f_fim / f_ini) ** (t ** 0.8)                           # varredura exponencial (soa natural)
    peso = np.sqrt(1000.0 / fc)                                          # a mesma energia em qualquer altura
    corpo = passa_banda(passa_banda(rng.standard_normal(n), fc, 1.3), fc, 1.3) * peso
    brilho = passa_banda(passa_banda(rng.standard_normal(n), fc * 2.1, 2.0), fc * 2.1, 2.0) * peso * 0.3
    sinal = (corpo + brilho) * envelope(n, pico)
    p = pan[0] + (pan[1] - pan[0]) * t                                   # passa de um lado pro outro
    esq, dir_ = sinal * np.sqrt((1 - p) / 2), sinal * np.sqrt((1 + p) / 2)
    return np.stack([esq, dir_], axis=1)


def pop(dur=0.32, f_ini=980.0, f_fim=430.0, semente=7):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f_fim + (f_ini - f_fim) * np.exp(-t / 0.018)                    # o tom cai rápido (o "pó" do pop)
    fase = 2 * np.pi * np.cumsum(f) / SR
    env = (1 - np.exp(-t / 0.0015)) * np.exp(-t / 0.055)                 # ataque de 1,5 ms, queda de ~55 ms
    corpo = np.sin(fase) * env + 0.25 * np.sin(2 * fase) * env * np.exp(-t / 0.02)
    rng = np.random.default_rng(semente)
    clique = rng.standard_normal(n) * np.exp(-t / 0.0012) * 0.18         # o estalo do começo
    s = corpo + clique
    return np.stack([s, s], axis=1)


def fade(x, ms=4):
    k = min(int(SR * ms / 1000), len(x) // 2)
    r = np.linspace(0, 1, k)[:, None]
    x[:k] *= r
    x[-k:] *= r[::-1]
    return x


def gravar(nome, x, pico_db):
    x = fade(np.array(x, dtype=np.float64))
    x *= 10 ** (pico_db / 20) / max(np.abs(x).max(), 1e-9)
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    caminho = os.path.join(AQUI, nome)
    with wave.open(caminho, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"[sons] {nome}: {len(x) / SR:.2f} s, pico {pico_db} dB -> {caminho}")


def main():
    gravar("whoosh.wav", whoosh(0.58, 320.0, 3600.0, pico=0.30, semente=11), -2.0)
    gravar("whoosh-2.wav", whoosh(0.72, 2400.0, 180.0, pico=0.28, semente=23, pan=(0.5, -0.5)), -2.0)
    gravar("pop.wav", pop(), -6.0)


if __name__ == "__main__":
    main()
