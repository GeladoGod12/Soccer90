# Soccer90 ⚽

Treino de futebol para apartamento — app web 100% no navegador.

## Demo

Abra `index.html` ou publique com **GitHub Pages**.

## Arquivos do site (obrigatórios)

| Arquivo | Função |
|---------|--------|
| `index.html` | Criar perfil |
| `login.html` | Entrar |
| `soccer90.html` | App principal + Treinador IA |

## Como publicar no GitHub Pages

### 1. Criar repositório
1. Acesse [github.com/new](https://github.com/new)
2. Nome, ex: `soccer90`
3. Público → **Create repository**

### 2. Enviar os arquivos

**Opção A — pelo site do GitHub**
1. No repositório → **Add file** → **Upload files**
2. Arraste: `index.html`, `login.html`, `soccer90.html`
3. Commit

**Opção B — pelo terminal**
```bash
git clone https://github.com/SEU_USUARIO/soccer90.git
cd soccer90
# copie index.html, login.html, soccer90.html para esta pasta
git add .
git commit -m "Soccer90 app"
git push
```

### 3. Ativar Pages
1. Repo → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` (pasta `/root`)
4. Save

Em 1–2 minutos o site fica em:
`https://SEU_USUARIO.github.io/soccer90/`

Links diretos:
- Criar perfil: `.../soccer90/index.html`
- Login: `.../soccer90/login.html`
- App: `.../soccer90/soccer90.html`

## O que funciona online

- Criar perfil / login (localStorage do navegador)
- Treinos, timer, progresso, streak
- Treinador IA **em JavaScript** (offline, no próprio celular)
- Banco de aprendizado com 👍/👎
- Export do banco de aprendizado (JSON)

## Python (opcional, só no seu PC)

O arquivo `soccer90_ai.py` **não roda no GitHub**.  
É um treinador extra para usar na sua máquina:

```bash
python3 soccer90_ai.py --server
```

- Abrindo o HTML do **disco** ou em `localhost` → tenta o Python
- No **GitHub Pages** → usa só a IA JS (automático)

Com Ollama (IA maior local):
```bash
ollama pull llama3.2
python3 soccer90_ai.py --server --ollama
```

## Estrutura recomendada no repo

```
soccer90/
├── index.html
├── login.html
├── soccer90.html
├── soccer90_ai.py      (opcional)
├── README.md
└── README_IA.md        (opcional)
```

## Observações

- Dados ficam no **navegador** de cada pessoa (localStorage)
- Não há servidor/backend no GitHub Pages
- Para sincronizar entre celulares no futuro: backend (Supabase, Firebase, etc.)
