#!/usr/bin/env python3
"""
Soccer90 — Treinador IA em Python (local, treinável)

═══════════════════════════════════════════════════════════
  COMO TREINAR / ALIMENTAR A IA
═══════════════════════════════════════════════════════════

  1) Importar export do app HTML:
       python3 soccer90_ai.py --import soccer90-learning-bank.json

  2) Adicionar pergunta e resposta na mão:
       python3 soccer90_ai.py --add "Posso treinar enjoado?" "Só se estiver leve. Prefira descanso."

  3) Alimentar com arquivo de texto/markdown (fatos):
       python3 soccer90_ai.py --ingest conhecimento.txt
       python3 soccer90_ai.py --ingest pasta_conhecimento/

  4) Adicionar FAQ (várias Q&A de uma vez) — arquivo JSON:
       [
         {"q": "Preciso de tênis?", "a": "Sim, de preferência com bom amortecimento."},
         {"q": "Treino em jejum?", "a": "Pode, se for leve e você se sentir bem."}
       ]
       python3 soccer90_ai.py --import faq.json

  5) Ver estatísticas:
       python3 soccer90_ai.py --stats

  6) Chat / servidor:
       python3 soccer90_ai.py
       python3 soccer90_ai.py --server
       python3 soccer90_ai.py --server --ollama

Arquivos gerados:
  soccer90_memory.json   → Q&A aprendidas
  soccer90_knowledge.json → fatos / textos ingeridos
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
MEMORY_FILE = ROOT / "soccer90_memory.json"
KNOWLEDGE_FILE = ROOT / "soccer90_knowledge.json"
BANK_FILE = ROOT / "soccer90-learning-bank.json"
KNOWLEDGE_DIR = ROOT / "conhecimento"  # pasta opcional de .txt / .md / .json
HOST = "127.0.0.1"
PORT = 8765
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2"

SYSTEM_PROMPT = """Você é o TREINADOR OFICIAL do Soccer90, app de treino de futebol para APARTAMENTO.
Responda SEMPRE em português do Brasil, curto (1-3 parágrafos), prático e motivador.
Regras de segurança: dor aguda → parar e procurar profissional. Não invente exercícios perigosos.
Foque em pouco espaço (1,5m–2m), com ou sem bola.
"""

# ---------------------------------------------------------------------------
# Exercícios do app (base fixa)
# ---------------------------------------------------------------------------
BANCO = {
    "sem_bola": {
        "titulo": "Físico sem bola",
        "tip": "Ideal para apartamento. Só o corpo, pouco espaço.",
        "items": [
            {"nome": "Mobilidade de tornozelo", "desc": "Círculos com os pés", "tempo": 50,
             "steps": ["Levante um joelho", "Faça círculos com o pé", "Troque o lado"]},
            {"nome": "Marcha no lugar", "desc": "Joelhos elevados", "tempo": 50,
             "steps": ["No mesmo lugar", "Eleve os joelhos", "Balance os braços"]},
            {"nome": "Agachamento na parede", "desc": "Isometria a 90°", "tempo": 40,
             "steps": ["Costas na parede", "Desça até 90°", "Segure respirando"]},
            {"nome": "Afundo reverso", "desc": "Passo para trás alternado", "tempo": 45,
             "steps": ["Passo longo para trás", "Joelho quase no chão", "Volte e alterne"]},
            {"nome": "Prancha frontal", "desc": "Corpo reto nos antebraços", "tempo": 35,
             "steps": ["Antebraços no chão", "Corpo alinhado", "Não deixe cair o quadril"]},
            {"nome": "Passos laterais", "desc": "Deslocamento curto e rápido", "tempo": 40,
             "steps": ["Base baixa", "Passos laterais", "Sem cruzar as pernas"]},
            {"nome": "Dead bug", "desc": "Braço e perna opostos", "tempo": 40,
             "steps": ["Deite de costas", "Estenda braço + perna oposta", "Alterne"]},
            {"nome": "Simulação de chute", "desc": "Movimento completo sem bola", "tempo": 40,
             "steps": ["Uma perna de apoio", "Movimento de chute", "Equilíbrio. Alterne"]},
            {"nome": "Alongamento posterior", "desc": "Perna estendida", "tempo": 40,
             "steps": ["Perna à frente", "Incline o tronco", "20s cada lado"]},
            {"nome": "Respiração", "desc": "Inspire 4s expire 6s", "tempo": 45,
             "steps": ["Mão na barriga", "Inspire 4s", "Expire 6s"]},
        ],
    },
    "com_bola": {
        "titulo": "Físico com bola",
        "tip": "Use uma bola (mesmo de plástico). Espaço mínimo 2x2m.",
        "items": [
            {"nome": "Toques no lugar", "desc": "Domínio com ambas as pernas", "tempo": 60,
             "steps": ["Bola no pé", "Toques alternados", "Cabeça erguida"]},
            {"nome": "Condução em 8", "desc": "Conduza em formato de oito", "tempo": 50,
             "steps": ["Marque 2 pontos", "Conduza em 8", "Troque de pé"]},
            {"nome": "Passe na parede", "desc": "Passe e receba na parede", "tempo": 60,
             "steps": ["1-2m da parede", "Passe firme", "Controle e devolva"]},
            {"nome": "Controle orientado", "desc": "Receba e vire o corpo", "tempo": 50,
             "steps": ["Passe na parede", "Controle com sola/interior", "Vire 180°"]},
            {"nome": "Finalização na parede", "desc": "Chute preciso na parede", "tempo": 50,
             "steps": ["3-5m de distância", "Chute com precisão", "Ambas as pernas"]},
            {"nome": "Drible estacionário", "desc": "Fintas no lugar", "tempo": 45,
             "steps": ["Bola nos pés", "Corte seco", "Troca de direção"]},
        ],
    },
    "tatico": {
        "titulo": "Tático",
        "tip": "Decisão e posicionamento.",
        "items": [
            {"nome": "Posicionamento em base", "desc": "Base baixa, visão de campo", "tempo": 45},
            {"nome": "Desmarque curto", "desc": "2-3 passos de desmarque e volte", "tempo": 50},
            {"nome": "Pressão simulada", "desc": "Aproxime rápido e contenha", "tempo": 45},
            {"nome": "Transição rápida", "desc": "Defesa → ataque em 3s", "tempo": 50},
            {"nome": "Tomada de decisão", "desc": "Passe, conduza ou chute", "tempo": 45},
        ],
    },
    "forca": {
        "titulo": "Força",
        "tip": "Força funcional para futebol.",
        "items": [
            {"nome": "Agachamento livre", "desc": "Agache controlado", "tempo": 45},
            {"nome": "Afundo caminhando", "desc": "Afundos no lugar/curto", "tempo": 50},
            {"nome": "Ponte de glúteo", "desc": "Elevação de quadril", "tempo": 40},
            {"nome": "Prancha + elevação", "desc": "Prancha e eleva braço/perna", "tempo": 35},
            {"nome": "Elevação de panturrilha", "desc": "Na ponta dos pés", "tempo": 40},
            {"nome": "Superman", "desc": "Eleva braços e pernas", "tempo": 35},
        ],
    },
    "agilidade": {
        "titulo": "Agilidade",
        "tip": "Mudanças de direção em pouco espaço.",
        "items": [
            {"nome": "Skipping alto", "desc": "Joelhos altos no lugar", "tempo": 35},
            {"nome": "Passos laterais rápidos", "desc": "Lateral em 1-1,5m", "tempo": 40},
            {"nome": "Mudança 1-2 passos", "desc": "2 passos cada lado", "tempo": 40},
            {"nome": "Shuffle + sprint curto", "desc": "Lateral e acelere 2m", "tempo": 40},
            {"nome": "Giro 180° + aceleração", "desc": "Gire e acelere", "tempo": 35},
            {"nome": "Pés rápidos no lugar", "desc": "Contato rápido com o chão", "tempo": 30},
        ],
    },
    "descanso": {
        "titulo": "Descanso ativo",
        "tip": "Recuperação. Não force.",
        "items": [
            {"nome": "Caminhada no lugar", "desc": "Ritmo bem leve", "tempo": 60},
            {"nome": "Mobilidade de quadril", "desc": "Círculos e aberturas", "tempo": 50},
            {"nome": "Alongamento global", "desc": "Pernas, costas, ombros", "tempo": 60},
            {"nome": "Respiração profunda", "desc": "4s inspira, 6s expira", "tempo": 60},
        ],
    },
}

POSICAO_DICAS = {
    "goleiro": "Agilidade lateral, explosão e core. Use Agilidade + Força + Sem bola.",
    "zagueiro": "Força, deslocamento lateral e tático. Força + Agilidade + Tático.",
    "lateral": "Mudança de direção e velocidade curta. Priorize Agilidade.",
    "volante": "Core, força e transição. Força + Tático + Sem bola.",
    "meia": "Controle e decisão. Com bola + Tático + Agilidade.",
    "atacante": "Explosão, finalização e desmarque. Agilidade + Com bola.",
}

# Fatos iniciais (podem ser expandidos via --ingest / --add-fact)
DEFAULT_FACTS = [
    {"title": "Espaço mínimo", "text": "Treinos sem bola cabem em cerca de 1,5m × 1,5m. Com bola, ideal 2m × 2m.", "tags": ["espaco", "apartamento"]},
    {"title": "Frequência", "text": "Não treine pesado todos os dias. Use descanso ativo 1–2x por semana. O corpo evolui na recuperação.", "tags": ["frequencia", "descanso"]},
    {"title": "Dor", "text": "Dor aguda ou articular: pare o exercício. Troque para mobilidade. Se persistir 2–3 dias, procure profissional de saúde.", "tags": ["dor", "lesao", "seguranca"]},
    {"title": "Hidratação", "text": "Beba água antes, durante e depois. Em apartamento o suor pode ser menos perceptível.", "tags": ["agua", "hidratacao"]},
    {"title": "Horário", "text": "O melhor horário é o que você mantém. Final da tarde/noite costuma ter o corpo mais aquecido.", "tags": ["horario"]},
    {"title": "Aquecimento", "text": "3–5 min de marcha + mobilidade de tornozelo/quadril antes do treino principal reduz risco de lesão.", "tags": ["aquecimento", "mobilidade"]},
    {"title": "Técnica em casa", "text": "Com bola: toques, condução em 8, passe na parede. Tático: decisão. Sem bola: simulação de chute. Qualidade > quantidade.", "tags": ["tecnica"]},
    {"title": "Progressão Soccer90", "text": "A intensidade segue as estrelas de qualidade técnica. Na 2ª metade do plano o app adiciona mais um exercício.", "tags": ["plano", "intensidade", "progressao"]},
]


# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(text: str) -> str:
    text = (text or "").lower()
    table = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc")
    return text.translate(table)


def tokenize(text: str) -> list[str]:
    text = normalize(text)
    text = re.sub(r"[^\w\s]", " ", text)
    stop = {"que", "para", "com", "uma", "por", "nao", "sim", "como", "mais", "menos", "muito", "sobre"}
    return [w for w in text.split() if len(w) > 2 and w not in stop]


def similarity(a: str, b: str) -> float:
    ta, tb = set(tokenize(a)), set(tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def load_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[aviso] não leu {path.name}: {e}", file=sys.stderr)
    return default


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Memória (Q&A) + Conhecimento (fatos)
# ---------------------------------------------------------------------------
def load_memory() -> list[dict]:
    return load_json(MEMORY_FILE, [])


def save_memory(mem: list[dict]) -> None:
    save_json(MEMORY_FILE, mem)


def load_knowledge() -> list[dict]:
    facts = load_json(KNOWLEDGE_FILE, None)
    if facts is None:
        facts = [dict(f, id=f"F{i}", source="default", createdAt=now_iso()) for i, f in enumerate(DEFAULT_FACTS)]
        save_json(KNOWLEDGE_FILE, facts)
    return facts


def save_knowledge(facts: list[dict]) -> None:
    save_json(KNOWLEDGE_FILE, facts)


def find_best_qa(mem: list[dict], question: str) -> tuple[dict | None, float]:
    best, best_s = None, 0.0
    for e in mem:
        s = similarity(question, e.get("q", ""))
        s += min((e.get("score") or 0) * 0.08, 0.35)
        s += min((e.get("uses") or 0) * 0.012, 0.12)
        if s > best_s:
            best_s, best = s, e
    return best, best_s


def find_best_facts(facts: list[dict], question: str, top: int = 3) -> list[dict]:
    scored = []
    for f in facts:
        blob = f"{f.get('title', '')} {f.get('text', '')} {' '.join(f.get('tags') or [])}"
        s = similarity(question, blob)
        # boost se tag aparece na pergunta
        tq = normalize(question)
        for tag in f.get("tags") or []:
            if normalize(tag) in tq:
                s += 0.15
        if s > 0.12:
            scored.append((s, f))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:top]]


def learn_qa(mem: list[dict], question: str, answer: str, score_delta: int = 0, source: str = "chat") -> list[dict]:
    qn = normalize(question)
    for e in mem:
        if normalize(e.get("q", "")) == qn or similarity(e.get("q", ""), question) > 0.72:
            e["uses"] = e.get("uses", 0) + 1
            e["score"] = e.get("score", 0) + score_delta
            if score_delta > 0 or source in ("import", "add", "train"):
                e["a"] = answer
            e["updatedAt"] = now_iso()
            e["source"] = e.get("source") or source
            save_memory(mem)
            return mem
    mem.append({
        "q": question.strip(),
        "a": answer.strip(),
        "score": score_delta if score_delta else 1,  # import/add já nasce útil
        "uses": 1,
        "source": source,
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    })
    if len(mem) > 500:
        mem.sort(key=lambda x: (x.get("score", 0) + x.get("uses", 0)), reverse=True)
        mem = mem[:350]
    save_memory(mem)
    return mem


def add_fact(facts: list[dict], title: str, text: str, tags: list[str] | None = None, source: str = "manual") -> list[dict]:
    title, text = title.strip(), text.strip()
    if not text:
        return facts
    # evita duplicata muito parecida
    for f in facts:
        if similarity(f.get("text", ""), text) > 0.85:
            f["text"] = text
            f["title"] = title or f.get("title")
            f["tags"] = list(set((f.get("tags") or []) + (tags or [])))
            f["updatedAt"] = now_iso()
            save_knowledge(facts)
            return facts
    facts.append({
        "id": f"F{int(datetime.now().timestamp()*1000)}",
        "title": title or text[:40],
        "text": text,
        "tags": tags or tokenize(title + " " + text)[:8],
        "source": source,
        "createdAt": now_iso(),
    })
    save_knowledge(facts)
    return facts


# ---------------------------------------------------------------------------
# Import / ingest (treino)
# ---------------------------------------------------------------------------
def extract_qa_pairs(data: Any) -> list[tuple[str, str, int]]:
    """Aceita vários formatos de JSON e devolve (q, a, score)."""
    pairs: list[tuple[str, str, int]] = []

    def push(q, a, score=1):
        if q and a:
            pairs.append((str(q).strip(), str(a).strip(), int(score or 1)))

    if isinstance(data, dict):
        # formato export HTML Soccer90
        if "entries" in data and isinstance(data["entries"], list):
            for e in data["entries"]:
                push(e.get("q") or e.get("question"), e.get("a") or e.get("answer"), e.get("score", 1))
        if "fineTuneFormat" in data and isinstance(data["fineTuneFormat"], list):
            for item in data["fineTuneFormat"]:
                msgs = item.get("messages") or []
                user = next((m["content"] for m in msgs if m.get("role") == "user"), None)
                asst = next((m["content"] for m in msgs if m.get("role") == "assistant"), None)
                push(user, asst, (item.get("meta") or {}).get("score", 1))
        # um único par
        push(data.get("q") or data.get("question"), data.get("a") or data.get("answer"), data.get("score", 1))
        # mapa simples {"pergunta": "resposta"}
        for k, v in data.items():
            if k in ("entries", "fineTuneFormat", "app", "version", "exportedAt", "total", "positive", "meta"):
                continue
            if isinstance(v, str) and len(k) > 3:
                push(k, v, 1)
    elif isinstance(data, list):
        for e in data:
            if isinstance(e, dict):
                push(e.get("q") or e.get("question") or e.get("prompt"),
                     e.get("a") or e.get("answer") or e.get("completion") or e.get("response"),
                     e.get("score", 1))
            elif isinstance(e, (list, tuple)) and len(e) >= 2:
                push(e[0], e[1], 1)
    return pairs


def import_file(path: Path, mem: list[dict], facts: list[dict]) -> tuple[int, int]:
    """Importa .json (Q&A) ou .txt/.md (fatos). Retorna (qa_count, fact_count)."""
    path = Path(path)
    if not path.exists():
        print(f"Arquivo não encontrado: {path}")
        return 0, 0

    qa_n, fact_n = 0, 0
    suffix = path.suffix.lower()

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        pairs = extract_qa_pairs(data)
        for q, a, score in pairs:
            mem = learn_qa(mem, q, a, score_delta=max(score, 1), source=f"import:{path.name}")
            qa_n += 1
        # se for lista de fatos
        if isinstance(data, list) and data and isinstance(data[0], dict) and "text" in data[0]:
            for f in data:
                facts = add_fact(facts, f.get("title", ""), f.get("text", ""), f.get("tags"), source=f"import:{path.name}")
                fact_n += 1
        print(f"  JSON {path.name}: +{qa_n} Q&A, +{fact_n} fatos")
        return qa_n, fact_n

    if suffix in (".txt", ".md", ".markdown"):
        raw = path.read_text(encoding="utf-8")
        # blocos separados por linha em branco = fatos
        blocks = re.split(r"\n\s*\n", raw.strip())
        for block in blocks:
            block = block.strip()
            if len(block) < 15:
                continue
            # formato Q: ... \n A: ...
            mq = re.search(r"^(?:q|p|pergunta)\s*[:\-]\s*(.+)", block, re.I | re.M)
            ma = re.search(r"^(?:a|r|resposta)\s*[:\-]\s*(.+)", block, re.I | re.M | re.S)
            if mq and ma:
                mem = learn_qa(mem, mq.group(1).strip(), ma.group(1).strip(), 1, source=f"ingest:{path.name}")
                qa_n += 1
                continue
            # título na primeira linha
            lines = block.split("\n")
            title = lines[0].lstrip("#").strip() if lines else path.stem
            text = "\n".join(lines[1:]).strip() if len(lines) > 1 else block
            if not text:
                text = title
            facts = add_fact(facts, title[:80], text, source=f"ingest:{path.name}")
            fact_n += 1
        print(f"  TXT/MD {path.name}: +{qa_n} Q&A, +{fact_n} fatos")
        return qa_n, fact_n

    print(f"  Ignorado (tipo não suportado): {path.name}")
    return 0, 0


def ingest_path(target: Path, mem: list[dict], facts: list[dict]) -> None:
    target = Path(target)
    total_qa = total_f = 0
    if target.is_dir():
        files = sorted(list(target.glob("*.json")) + list(target.glob("*.txt")) + list(target.glob("*.md")))
        print(f"Ingerindo pasta {target} ({len(files)} arquivos)...")
        for f in files:
            q, fc = import_file(f, mem, facts)
            total_qa += q
            total_f += fc
            mem = load_memory()
            facts = load_knowledge()
    else:
        q, fc = import_file(target, mem, facts)
        total_qa, total_f = q, fc
    print(f"✓ Total: {total_qa} Q&A + {total_f} fatos")


def seed_from_bank_if_present(mem: list[dict]) -> list[dict]:
    if BANK_FILE.exists():
        print(f"Importando {BANK_FILE.name}...")
        import_file(BANK_FILE, mem, load_knowledge())
        return load_memory()
    return mem


# ---------------------------------------------------------------------------
# Motor de resposta
# ---------------------------------------------------------------------------
def find_exercise(question: str) -> tuple[dict, str] | None:
    t = normalize(question)
    best, best_tipo, best_hit = None, None, 0
    for tipo, bank in BANCO.items():
        for ex in bank["items"]:
            nome = normalize(ex["nome"])
            hit = 0
            if nome in t:
                hit = 10
            else:
                for w in nome.split():
                    if len(w) > 3 and w in t:
                        hit += 1
            if hit > best_hit:
                best_hit, best, best_tipo = hit, ex, tipo
    if best and best_hit >= 1:
        return best, best_tipo  # type: ignore
    return None


def rule_reply(question: str, profile: dict | None, treino: dict | None, facts: list[dict]) -> str:
    t = normalize(question)
    nome = (profile or {}).get("nome", "atleta")
    if isinstance(nome, str) and " " in nome:
        nome = nome.split()[0]
    pos = (profile or {}).get("posicao", "jogador")
    stars = int((profile or {}).get("qualidadeTecnica") or (profile or {}).get("qualidade") or 3)

    # fatos relevantes
    top_facts = find_best_facts(facts, question, top=2)

    if re.search(r"treino de hoje|meu treino|o que fazer hoje|treino atual", t):
        if not treino:
            return f"{nome}, abra o dia atual no app para eu detalhar o treino."
        exs = treino.get("exercicios") or []
        if exs and isinstance(exs[0], dict):
            lista = "\n".join(f"{i+1}. {e.get('nome')} ({e.get('tempo', '?')}s)" for i, e in enumerate(exs))
        else:
            lista = "\n".join(f"{i+1}. {e}" for i, e in enumerate(exs))
        return (
            f"{nome}, treino de hoje:\n{treino.get('titulo', 'Treino')}\n"
            f"{treino.get('intens', '')} · {treino.get('duracao', '')}\n\n{lista}\n\n💡 {treino.get('tip', '')}"
        ).strip()

    if re.search(r"posicao|posição|para mim|minha pos|goleiro|zagueiro|lateral|volante|meia|atacante|o que treinar|treino para", t):
        for p in POSICAO_DICAS:
            if p in t:
                pos = p
                break
        dica = POSICAO_DICAS.get(pos, "Varie Força, Agilidade e Tático na semana.")
        return f"{nome}, como {pos}:\n{dica}\n\nQualidade técnica: {'★' * stars}."

    found = find_exercise(question)
    if found:
        ex, tipo = found
        steps = ex.get("steps") or []
        steps_txt = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        return (
            f"{ex['nome']} · {BANCO[tipo]['titulo']}\n\n"
            f"{ex.get('desc', '')}\nTempo: {ex.get('tempo', '?')}s\n\n"
            f"Como fazer:\n{steps_txt or '(veja a demonstração no app)'}"
        )

    # usa fatos do conhecimento
    if top_facts and (similarity(question, top_facts[0].get("text", "")) > 0.2 or any(
        normalize(tag) in t for tag in (top_facts[0].get("tags") or [])
    )):
        parts = [f.get("text", "") for f in top_facts]
        return "\n\n".join(parts)

    # regras clássicas
    rules = [
        (r"todo dia|todos os dias|diario|frequencia", f"Não treine pesado todos os dias, {nome}. Use Descanso 1–2x por semana."),
        (r"bola|preciso de bola|sem bola", "Não precisa de bola. Sem bola, Força, Agilidade, Tático e Descanso bastam (~1,5m × 1,5m)."),
        (r"dor|lesao|lesão|machuquei|doi|doendo", "Pare o exercício que dói. Prefira Descanso/mobilidade. Se continuar 2–3 dias, procure um profissional."),
        (r"intensidade|mais dificil|mais facil|cansado", f"Intensidade segue suas estrelas ({'★' * stars}). Reduza exercícios ou mude o tipo do dia se precisar."),
        (r"tecnica|técnica|melhorar|evoluir|drible|passe|chute", "Em casa: Com bola + Tático + simulação de chute. 15–20 min focados > 40 min distraído."),
        (r"horario|horário|quando treinar|manha|noite", "O melhor horário é o que você mantém. Muitos preferem final da tarde/noite."),
        (r"espaco|espaço|apartamento|quarto", "Maioria dos treinos: ~1,5m × 1,5m. Com bola: ~2m × 2m."),
        (r"tipos de treino|que tipos|modos", "Tipos: Sem bola · Com bola · Tático · Força · Agilidade · Descanso."),
    ]
    for pat, ans in rules:
        if re.search(pat, t):
            return ans

    if top_facts:
        return top_facts[0].get("text", "")

    return (
        f"Sou o treinador Soccer90 (Python), {nome}.\n"
        "Pergunte sobre treino, posição, exercício, dor, intensidade, técnica.\n"
        "Para me treinar: python3 soccer90_ai.py --add \"pergunta\" \"resposta\" "
        "ou --ingest arquivo.txt"
    )


def ollama_available() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def ollama_reply(question: str, profile: dict | None, treino: dict | None, mem: list[dict], facts: list[dict]) -> str | None:
    hints_qa = []
    for e in sorted(mem, key=lambda x: x.get("score", 0), reverse=True)[:8]:
        hints_qa.append(f"P: {e.get('q')}\nR: {e.get('a')}")
    hints_f = [f"- {f.get('title')}: {f.get('text')}" for f in find_best_facts(facts, question, 5)]
    ctx = SYSTEM_PROMPT
    ctx += f"\nPerfil: {json.dumps(profile or {}, ensure_ascii=False)}"
    if treino:
        ctx += f"\nTreino: {json.dumps(treino, ensure_ascii=False)}"
    if hints_f:
        ctx += "\n\nFatos:\n" + "\n".join(hints_f)
    if hints_qa:
        ctx += "\n\nQ&A treinadas:\n" + "\n---\n".join(hints_qa)
    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": ctx},
            {"role": "user", "content": question},
        ],
    }
    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.loads(r.read().decode("utf-8"))
        return (out.get("message") or {}).get("content")
    except Exception as e:
        print(f"[ollama] {e}", file=sys.stderr)
        return None


class Soccer90AI:
    def __init__(self, use_ollama: bool = False):
        self.use_ollama = use_ollama
        self.mem = load_memory()
        self.facts = load_knowledge()
        # auto-import export do HTML se existir
        if BANK_FILE.exists() and not self.mem:
            self.mem = seed_from_bank_if_present(self.mem)
        # auto-ingest pasta conhecimento/
        if KNOWLEDGE_DIR.exists():
            before = len(self.facts)
            ingest_path(KNOWLEDGE_DIR, self.mem, self.facts)
            self.mem = load_memory()
            self.facts = load_knowledge()
            if len(self.facts) > before:
                print(f"[Soccer90 AI] Pasta conhecimento/ carregada")
        print(f"[Soccer90 AI] Q&A: {len(self.mem)} | Fatos: {len(self.facts)}")
        if use_ollama:
            print(f"[Soccer90 AI] Ollama: {'OK' if ollama_available() else 'offline'}")

    def answer(self, question: str, profile: dict | None = None, treino: dict | None = None) -> dict:
        question = (question or "").strip()
        if not question:
            return {"reply": "Faça uma pergunta sobre treino.", "src": "python"}

        best, score = find_best_qa(self.mem, question)
        if best and score > 0.42 and (best.get("score") or 0) >= 1:
            best["uses"] = best.get("uses", 0) + 1
            save_memory(self.mem)
            return {"reply": best["a"], "src": "memória treinada", "model": "memory"}

        if self.use_ollama and ollama_available():
            text = ollama_reply(question, profile, treino, self.mem, self.facts)
            if text:
                # não grava automaticamente respostas genéricas longas demais sem score
                return {"reply": text, "src": "ollama local", "model": OLLAMA_MODEL}

        if best and score > 0.5:
            best["uses"] = best.get("uses", 0) + 1
            save_memory(self.mem)
            return {"reply": best["a"], "src": "memória", "model": "memory"}

        text = rule_reply(question, profile, treino, self.facts)
        if "para me treinar:" not in text.lower():
            self.mem = learn_qa(self.mem, question, text, 0, source="rules")
        return {"reply": text, "src": "treinador python", "model": "rules+knowledge"}

    def rate(self, question: str, answer: str, up: bool) -> None:
        self.mem = learn_qa(self.mem, question, answer, 1 if up else -1, source="rate")


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def make_handler(ai: Soccer90AI):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print(f"[http] {args[0]}")

        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self):
            if self.path in ("/", "/health"):
                body = json.dumps({
                    "ok": True,
                    "qa": len(ai.mem),
                    "facts": len(ai.facts),
                    "ollama": ai.use_ollama and ollama_available(),
                }).encode()
                self.send_response(200)
                self._cors()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path not in ("/chat", "/api/chat", "/train", "/add"):
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                data = {}

            if self.path in ("/train", "/add"):
                q = data.get("q") or data.get("question") or ""
                a = data.get("a") or data.get("answer") or ""
                if q and a:
                    ai.mem = learn_qa(ai.mem, q, a, 1, source="api")
                    result = {"ok": True, "qa": len(ai.mem)}
                else:
                    result = {"ok": False, "error": "q e a obrigatórios"}
            else:
                result = ai.answer(
                    data.get("message") or data.get("q") or "",
                    data.get("profile"),
                    data.get("treino"),
                )

            body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

    return Handler


def run_server(ai: Soccer90AI, host: str, port: int) -> None:
    server = HTTPServer((host, port), make_handler(ai))
    print(f"\n✅ http://{host}:{port}  |  Q&A={len(ai.mem)} fatos={len(ai.facts)}")
    print("   POST /chat  {\"message\":\"...\"}")
    print("   POST /train {\"q\":\"...\", \"a\":\"...\"}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
        server.server_close()


def run_cli(ai: Soccer90AI) -> None:
    print("=" * 52)
    print("  Soccer90 IA  |  :mem  :facts  :add  :quit")
    print("=" * 52)
    while True:
        try:
            q = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté mais!")
            break
        if not q:
            continue
        if q in (":q", ":quit", "sair", "exit"):
            break
        if q == ":mem":
            print(f"Q&A: {len(ai.mem)}")
            for e in ai.mem[-10:]:
                print(f"  [{e.get('score', 0):+d}|{e.get('uses', 0)}u] {e.get('q', '')[:70]}")
            continue
        if q == ":facts":
            print(f"Fatos: {len(ai.facts)}")
            for f in ai.facts[-10:]:
                print(f"  • {f.get('title')}: {str(f.get('text', ''))[:70]}")
            continue
        if q.startswith(":add "):
            # :add pergunta || resposta
            body = q[5:]
            if "||" in body:
                qq, aa = body.split("||", 1)
                ai.mem = learn_qa(ai.mem, qq.strip(), aa.strip(), 1, source="cli")
                print("✓ Q&A adicionada")
            else:
                print("Use: :add pergunta || resposta")
            continue
        out = ai.answer(q)
        print(f"\nTreinador ({out.get('src')}):\n{out['reply']}")


def print_stats(mem: list[dict], facts: list[dict]) -> None:
    pos = sum(1 for e in mem if (e.get("score") or 0) > 0)
    print(f"Q&A na memória : {len(mem)} ({pos} com score > 0)")
    print(f"Fatos          : {len(facts)}")
    print(f"Arquivos       : {MEMORY_FILE.name}, {KNOWLEDGE_FILE.name}")
    if mem:
        print("\nTop Q&A:")
        for e in sorted(mem, key=lambda x: x.get("score", 0), reverse=True)[:8]:
            print(f"  [{e.get('score', 0):+d}] {e.get('q', '')[:60]}")
    if facts:
        print("\nAlguns fatos:")
        for f in facts[:6]:
            print(f"  • {f.get('title')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global OLLAMA_MODEL
    p = argparse.ArgumentParser(
        description="Soccer90 Treinador IA (Python local, treinável)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de treino:
  python3 soccer90_ai.py --add "Preciso de tênis?" "Sim, com amortecimento."
  python3 soccer90_ai.py --import soccer90-learning-bank.json
  python3 soccer90_ai.py --ingest conhecimento.txt
  python3 soccer90_ai.py --ingest ./conhecimento/
  python3 soccer90_ai.py --add-fact "Joelho" "Dor no joelho: pare agachamentos profundos e procure avaliação."
  python3 soccer90_ai.py --stats
        """,
    )
    p.add_argument("--server", action="store_true", help="Servidor HTTP local")
    p.add_argument("--ollama", action="store_true", help="Usar Ollama se disponível")
    p.add_argument("--host", default=HOST)
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--model", default="llama3.2")
    p.add_argument("--import", dest="import_path", help="Importar JSON de Q&A / export do app")
    p.add_argument("--ingest", dest="ingest_path", help="Ingerir .txt/.md/.json ou pasta")
    p.add_argument("--add", nargs=2, metavar=("PERGUNTA", "RESPOSTA"), help="Adicionar 1 Q&A")
    p.add_argument("--add-fact", nargs=2, metavar=("TITULO", "TEXTO"), help="Adicionar 1 fato")
    p.add_argument("--stats", action="store_true", help="Ver memória e fatos")
    args = p.parse_args()
    OLLAMA_MODEL = args.model

    mem = load_memory()
    facts = load_knowledge()

    # comandos de treino (não precisam subir o chat)
    did_train = False
    if args.import_path:
        import_file(Path(args.import_path), mem, facts)
        mem, facts = load_memory(), load_knowledge()
        did_train = True
    if args.ingest_path:
        ingest_path(Path(args.ingest_path), mem, facts)
        mem, facts = load_memory(), load_knowledge()
        did_train = True
    if args.add:
        mem = learn_qa(mem, args.add[0], args.add[1], 1, source="add")
        print(f"✓ Q&A adicionada. Total: {len(mem)}")
        did_train = True
    if args.add_fact:
        facts = add_fact(facts, args.add_fact[0], args.add_fact[1], source="add-fact")
        print(f"✓ Fato adicionado. Total: {len(facts)}")
        did_train = True
    if args.stats:
        print_stats(mem, facts)
        did_train = True

    if did_train and not args.server and not args.ollama:
        # só treinou — não abre chat a menos que peça server
        if not any([args.server]):
            return

    ai = Soccer90AI(use_ollama=args.ollama)
    if args.server:
        run_server(ai, args.host, args.port)
    else:
        run_cli(ai)


if __name__ == "__main__":
    main()
