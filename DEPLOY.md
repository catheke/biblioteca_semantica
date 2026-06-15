# Implantar o BASI online (GitHub + Render)

Este guia explica como pôr o **Semantic Academic Hub (BASI)** a funcionar na
Internet, de forma gratuita, usando o **GitHub** para o código e o **Render**
para correr os serviços (base de dados, Fuseki, backend e frontend).

> **Resumo da arquitectura na nuvem**
> - **PostgreSQL** (Render gerido) — utilizadores, documentos, metadados.
> - **Apache Jena Fuseki** — grafo RDF + SPARQL (ontologia e inferência).
> - **Backend FastAPI** — a API.
> - **Frontend Next.js** — a interface web.
>
> Tudo é descrito no ficheiro [`render.yaml`](render.yaml), que o Render lê
> automaticamente.

---

## 1. Pré-requisitos

- Uma conta no [GitHub](https://github.com) (gratuita).
- Uma conta no [Render](https://render.com) (gratuita; pode entrar com o GitHub).
- O `git` instalado no computador.

---

## 2. Enviar o projecto para o GitHub

A partir da pasta do projecto:

```bash
git init
git add .
git commit -m "BASI — biblioteca académica semântica"
git branch -M main
git remote add origin https://github.com/<o-teu-utilizador>/semantic-academic-hub.git
git push -u origin main
```

> O ficheiro `.gitignore` já impede o envio de segredos (`.env`), da pasta
> `.venv`, de `node_modules` e dos dados locais. **Nunca** envies o `.env`.

---

## 3. Criar tudo no Render com o Blueprint

1. Entra em <https://dashboard.render.com>.
2. Clica em **New +** → **Blueprint**.
3. Liga a tua conta do GitHub e escolhe o repositório `semantic-academic-hub`.
4. O Render detecta o `render.yaml` e mostra os serviços que vai criar:
   `basi-db`, `basi-fuseki`, `basi-backend` e `basi-frontend`.
5. Clica em **Apply**. O Render começa a construir (demora alguns minutos).

A base de dados, a chave JWT e a palavra-passe do Fuseki são geradas
automaticamente. Faltam apenas **quatro variáveis** que dependem dos URLs que o
Render só atribui depois de criar os serviços (passo seguinte).

---

## 4. Preencher os URLs entre serviços

Depois do primeiro build, cada serviço web fica com um URL público do tipo
`https://basi-xxxx.onrender.com`. Anota o URL do **backend**, do **frontend** e
do **fuseki** (vês todos no painel do Render).

### 4.1. No serviço `basi-backend` → separador **Environment**

| Variável | Valor a colocar |
|---|---|
| `FUSEKI_QUERY_ENDPOINT`  | `https://<url-do-fuseki>/basi/query`  |
| `FUSEKI_UPDATE_ENDPOINT` | `https://<url-do-fuseki>/basi/update` |
| `FUSEKI_DATA_ENDPOINT`   | `https://<url-do-fuseki>/basi/data`   |
| `CORS_ORIGINS`           | `https://<url-do-frontend>`           |

### 4.2. No serviço `basi-frontend` → separador **Environment**

| Variável | Valor a colocar |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<url-do-backend>/api/v1` |

> Como o Next.js fixa este valor **durante a compilação**, depois de o definires
> tens de carregar em **Manual Deploy → Clear build cache & deploy** no frontend.

Guarda as alterações. O Render volta a arrancar os serviços afectados.

---

## 5. Verificar

- **Backend:** abre `https://<url-do-backend>/docs` — deve aparecer o Swagger.
- **Saúde:** `https://<url-do-backend>/health` devolve `{"estado":"ok",...}`.
- **Frontend:** abre `https://<url-do-frontend>` — deve carregar a biblioteca.
- **Login de demonstração:** `admin@basi.ao` / `password123`.

No primeiro arranque, o backend (com `BOOTSTRAP_ON_STARTUP=1`) semeia a base de
dados e carrega a ontologia no Fuseki automaticamente — não é preciso correr
scripts à mão.

---

## 6. Notas sobre o plano gratuito

- **Adormecimento:** os serviços gratuitos param após ~15 min sem tráfego e
  acordam no pedido seguinte (o primeiro acesso pode demorar ~30 s).
- **Grafo do Fuseki efémero:** no plano gratuito o Fuseki não tem disco
  persistente. Se reiniciar, o grafo fica vazio até o backend o recarregar. Os
  dados **relacionais** (PostgreSQL) são persistentes. Mesmo sem Fuseki, a
  pesquisa semântica continua a funcionar, porque o backend tem um grafo
  `rdflib` em memória de reserva (com a mesma inferência `eSubtemaDe*`).
- **Base de dados gratuita:** a Postgres gratuita do Render expira ao fim de
  ~30 dias. Para uso prolongado, passa para um plano pago ou cria uma nova.
- **Persistência total do grafo:** associa um **disco pago** ao serviço
  `basi-fuseki` (montado em `/fuseki`) para o grafo sobreviver a reinícios.

---

## 7. Actualizar a aplicação

Basta enviar novas alterações para o GitHub:

```bash
git add .
git commit -m "descrição da alteração"
git push
```

O Render detecta o `push` e reconstrói automaticamente os serviços.

---

## Alternativa: só o frontend no Vercel?

O **Vercel** só corre o frontend (Next.js). Não consegue correr o FastAPI, o
PostgreSQL nem o Fuseki. Se quiseres usar o Vercel para o frontend, terás à
mesma de alojar o backend, a base de dados e o Fuseki noutro sítio (ex.: Render)
e apontar o `NEXT_PUBLIC_API_URL` para esse backend. Por simplicidade, este guia
mantém **tudo no Render**.
