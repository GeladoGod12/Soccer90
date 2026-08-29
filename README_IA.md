# Soccer90 — IA em Python (local)

## Arquivos
- `soccer90_ai.py` — treinador local em Python
- `soccer90-learning-bank.json` — coloque aqui o export do app (opcional)
- `soccer90_memory.json` — criado automaticamente (memória do Python)

## 1. Chat no terminal

```bash
cd /caminho/da/pasta
python3 soccer90_ai.py
```

Comandos:
- pergunta normal → resposta do treinador
- `:mem` → mostra memória
- `:quit` → sair

## 2. Servidor para o app HTML

```bash
python3 soccer90_ai.py --server
```

No `soccer90.html`, altere:

```js
const AI_CHAT_ENDPOINT = 'http://127.0.0.1:8765/chat';
```

(Se o app estiver 100% local em JS, pode deixar vazio — o Python é opcional e mais forte.)

## 3. IA “de verdade” no PC (Ollama)

1. Instale: https://ollama.com
2. Baixe um modelo:

```bash
ollama pull llama3.2
```

3. Rode:

```bash
python3 soccer90_ai.py --server --ollama
# ou no terminal:
python3 soccer90_ai.py --ollama
```

## 4. Banco de aprendizado

1. No app HTML → aba IA → **Exportar**
2. Salve o arquivo como `soccer90-learning-bank.json` na mesma pasta do script
3. Ao iniciar, o Python importa esses aprendizados

O export já vem com `fineTuneFormat` pronto para treinar um modelo no futuro.

## Teste rápido da API

```bash
curl -X POST http://127.0.0.1:8765/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Como fazer prancha frontal?"}'
```
