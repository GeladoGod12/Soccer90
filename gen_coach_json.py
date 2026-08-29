#!/usr/bin/env python3
"""Gera futebol_coach_pro.json (~20 MB) para treinar IA coach de futebol."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent / "coach_data" / "futebol_coach_pro.json"
out.parent.mkdir(parents=True, exist_ok=True)

posicoes = [
    "goleiro", "zagueiro central", "zagueiro lateral", "lateral direito",
    "lateral esquerdo", "volante", "primeiro volante", "segundo volante",
    "meia central", "meia atacante", "ponta direita", "ponta esquerda",
    "centroavante", "falso 9", "segundo atacante",
]
sistemas = ["4-4-2", "4-3-3", "4-2-3-1", "3-5-2", "3-4-3", "4-1-4-1", "5-3-2", "4-5-1", "3-4-2-1"]
qualidades = [
    "velocidade", "agilidade", "força", "resistência aeróbia", "resistência anaeróbia",
    "potência", "mobilidade", "coordenação", "equilíbrio", "flexibilidade",
    "aceleração", "desaceleração", "mudança de direção",
]
tecnicas = [
    "passe curto", "passe longo", "passe filtrado", "cruzamento", "finalização",
    "cabeceio", "domínio", "condução", "drible", "finta", "proteção de bola",
    "interceptação", "desarme", "marcação", "cobertura", "pressão alta",
    "bloco baixo", "saída de bola", "construção", "criação",
]
lesoes = [
    "isquiotibiais", "adutores", "quadricípite", "panturrilha", "LCA", "menisco",
    "tornozelo", "pubalgia", "lombar", "tendinite patelar", "canelite",
]
contextos = [
    "profissional", "base sub-17", "amador", "pré-temporada", "meio de temporada",
    "eliminatória", "elenco reduzido", "pós 3 jogos", "visitante",
    "gramado sintético", "calor", "viagem",
]
formatos = ["1x1", "2x2", "3x3", "4x4", "5x5", "6x6", "7x7"]
objetivos = ["posse", "finalização", "transição", "pressão", "amplitude", "compactação", "saída de bola"]
principios = [
    "posse de bola", "transição ofensiva", "transição defensiva",
    "organização defensiva", "organização ofensiva",
    "bola parada ofensiva", "bola parada defensiva",
]


def qa(q, a, score=1, tags=None):
    return {"q": q, "a": a, "score": score, "tags": tags or []}


TARGET = 20 * 1024 * 1024
f = open(out, "w", encoding="utf-8")
f.write(
    '{"app":"Soccer90 Coach Pro","version":2,'
    '"description":"Base massiva para IA coach de futebol profissional. '
    'Use: python3 soccer90_ai.py --import futebol_coach_pro.json","entries":['
)

count = 0
first = True
size = 512


def emit(obj):
    global count, first, size
    chunk = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    piece = ("" if first else ",") + chunk
    f.write(piece)
    size += len(piece.encode("utf-8"))
    first = False
    count += 1
    return size >= TARGET


for pos in posicoes:
    emit(qa(
        f"Como treinar um {pos}?",
        f"Treino do {pos}: combine técnico-tático da função, físico das demandas e jogos reduzidos. "
        f"Progressão analítico → situacional → global. Ambos os lados. Corrija orientação corporal e decisão. "
        f"Em semana de jogos, reduza volume e mantenha qualidade.",
        2, ["posicao", pos],
    ))
    emit(qa(
        f"Erros comuns de {pos}?",
        f"Erros no {pos}: desatenção posicional, má orientação corporal, decisão tardia, "
        f"lado não dominante fraco, falha de comunicação. Corrija com feedback, vídeo e jogos com regras.",
        2, ["posicao"],
    ))

for sis in sistemas:
    emit(qa(
        f"Como montar o sistema {sis}?",
        f"Sistema {sis}: papéis em posse e sem posse, compactação, altura do bloco, "
        f"padrões de saída/progressão/finalização. Adapte aos jogadores. Treine princípios, não só o desenho.",
        2, ["tatica", sis],
    ))

for q in qualidades:
    emit(qa(
        f"Como desenvolver {q} no futebol?",
        f"Desenvolvimento de {q}: estímulos com e sem bola, recuperação, progressão de carga, "
        f"integração à periodização. Evite excesso perto de jogos. Avalie com testes de campo.",
        2, ["fisico", q],
    ))

for tec in tecnicas:
    emit(qa(
        f"Como treinar {tec}?",
        f"Treino de {tec}: sem pressão → oposição passiva → ativa. Jogos reduzidos que premiem {tec}. "
        f"Ambos os pés. Qualidade > quantidade. Feedback curto.",
        2, ["tecnica", tec],
    ))

for les in lesoes:
    emit(qa(
        f"Como prevenir lesão de {les}?",
        f"Prevenção de {les}: aquecimento, força excêntrica quando indicada, mobilidade, "
        f"progressão de carga, sono. Não jogue com dor aguda. Retorno com critérios profissionais.",
        2, ["saude", les],
    ))

for pr in principios:
    emit(qa(
        f"Como treinar o princípio de {pr}?",
        f"Princípio {pr}: tarefas com regras claras, espaços adequados e feedback. "
        f"Repita até hábito coletivo. Vídeo com 3-5 clipes-chave.",
        2, ["principios"],
    ))

for fmt in formatos:
    for obj in objetivos:
        if emit(qa(
            f"Jogo {fmt} para treinar {obj}",
            f"Organize {fmt} premiando {obj}. Ajuste campo, toques e séries. "
            f"Alta intensidade, pausas ativas, 2 correções por bloco.",
            1, ["jogo_reduzido"],
        )):
            break

cenarios = [
    ("perdendo 0-1 aos 70", "amplitude e profundidade, mudanças ofensivas"),
    ("ganhando 1-0 aos 80", "gerir ritmo, compactar"),
    ("empate no intervalo", "ajustar pressão, lado fraco"),
    ("com 10 em campo", "compactar, estabilidade"),
    ("adversário linha alta", "profundidade, costas da defesa"),
    ("adversário bloco baixo", "paciência, entre linhas, bolas paradas"),
]
for t, a in cenarios:
    emit(qa(
        f"Como orientar o time {t}?",
        f"Cenário {t}: {a}. 2-3 pontos claros. Substituições com função.",
        2, ["gestao"],
    ))

extras = [
    " Registre PSE.",
    " Em base, reduza volume 20-40%.",
    " Com jogo em 48h, evite força máxima.",
    " Em calor, reforce hidratação.",
    " Individualize titulares e reservas.",
    " Critérios de sucesso mensuráveis.",
    " Feedback em até 90s.",
    " Feche em jogo mais aberto.",
]

i = 0
while size < TARGET and i < 120000:
    i += 1
    pos = posicoes[i % len(posicoes)]
    tec = tecnicas[i % len(tecnicas)]
    qual = qualidades[i % len(qualidades)]
    ctx = contextos[i % len(contextos)]
    sis = sistemas[i % len(sistemas)]
    pr = principios[i % len(principios)]
    templates = [
        (
            f"Sessão {i}: {tec} + {qual} para {pos} ({ctx})",
            f"Sessão {i} para {pos}: foco {tec} e {qual} ({ctx}). Aquecimento 10-12 min; "
            f"bloco de {tec} (3 séries); bloco de {qual}; jogo reduzido premiando {tec}; "
            f"volta à calma. Cones, coletes, bolas. Se PSE>8 perto de jogo, corte volume físico."
            + extras[i % len(extras)],
        ),
        (
            f"Padrão {i}: {pr} no {sis} ({ctx})",
            f"Treine {pr} no {sis} ({ctx}). Regras de pontuação, espaços e oposição. "
            f"Blocos 8-12 min, 2 correções-chave, aplicação final aberta. Avalie sob pressão."
            + extras[i % len(extras)],
        ),
        (
            f"Drill {i} de {tec} para {pos}",
            f"Drill {i}: {pos} em {tec} — sem oposição → passiva → ativa. 4-6 reps, ambos lados. "
            f"Corrija postura e decisão. Integre 4x4/5x5 no final."
            + extras[i % len(extras)],
        ),
        (
            f"Microciclo {i}: {qual} com jogo na semana ({ctx})",
            f"Estímulos de {qual} em {ctx}. Longe do jogo: mais volume. Perto: velocidade/ativação. "
            f"Monitore fadiga e sono. Evite força máxima + sprint no mesmo dia sem necessidade."
            + extras[i % len(extras)],
        ),
        (
            f"Gestão {i}: {pos} no {sis}",
            f"Papel do {pos} no {sis}: posse, sem posse e transição claros. Alinhe minutos e papéis. "
            f"Feedback individual curto pós-treino."
            + extras[i % len(extras)],
        ),
    ]
    q, a = templates[i % 5]
    if emit(qa(q, a, 1, ["expandido", ctx])):
        break
    if i % 5000 == 0:
        print(f"{count} entries, {size/1e6:.2f} MB", flush=True)

f.write('],"total_entries":%d}' % count)
f.close()
print(f"DONE entries={count} size={out.stat().st_size/1e6:.2f} MB")
print(f"PATH {out}")
