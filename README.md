# NewFurniture

Plataforma web para design e produção de **móveis sob medida**, conectando três atores:
**Cliente** (publica a necessidade), **Designer/Arquiteto** (envia o desenho técnico) e
**Marceneiro** (fabrica as peças para automontagem).

Trabalho final de **PMR3304 – Sistemas de Informação (Poli-USP, 2026)** — Grupo E:
Erick Kamada Pesce de Oliveira · Lucas Hideki Toyofuku Turri · Rafael Tadao Mendes Serikawa · Victor Hugo de Ávila Ribeiro.

| Camada | Tecnologia |
|---|---|
| Backend / API | Python, **Django** + **Django REST Framework** |
| Banco de dados | **SQLite** |
| Autenticação | **Token** (`rest_framework.authtoken`) |
| Frontend | **React** (JavaScript) com **Vite**, consumindo a API REST |

---

## 1. Como rodar

Pré-requisitos: **Python 3.10+** e **Node.js 18+** (com npm).

### Jeito rápido (scripts)

**Windows** — dê dois cliques (ou rode no terminal, na pasta do projeto):

```bat
setup.bat      :: só na primeira vez: instala tudo, cria o banco e os dados de demonstração
iniciar.bat    :: abre o backend (porta 8000) e o frontend (porta 5173)
```

**Linux / macOS**:

```bash
./setup.sh     # só na primeira vez
./iniciar.sh
```

Depois acesse **http://localhost:5173**.

### Passo a passo manual

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations core
python manage.py migrate
python manage.py popular_dados          # dados de demonstração (senha: senha123)
python manage.py createsuperuser        # opcional, para o /admin
python manage.py runserver              # http://127.0.0.1:8000

# Frontend (terminal 2)
cd frontend
npm install
npm run dev                             # http://localhost:5173
```

O Vite repassa `/api` e `/media` para o Django (ver `frontend/vite.config.js`), então basta abrir a porta 5173.

**Um servidor só (opcional, bom para a apresentação):** rode `npm run build` dentro de `frontend/`;
o Django passa a servir o React compilado em **http://127.0.0.1:8000**.

**Recriar os dados de demonstração:** `python manage.py popular_dados --limpar`

### Verificar que está tudo certo

```bash
cd backend
python manage.py test core
```

Os testes automatizados percorrem o fluxo completo pela API (cadastro, login, NEC001 → … → ENT002,
recusa e redirecionamento, totalizações) — devem passar todos (`OK`).

---

## 2. Contas de demonstração

Senha de todas: **`senha123`** (também há botões de acesso rápido na tela de login).

| Conta | Perfil | O que dá para demonstrar |
|---|---|---|
| `ana@cliente.com` | Cliente | Cadastrar necessidade (NEC001); **Armário suspenso** com 2 propostas → aprovar e pagar (APR001); **Guarda-roupa** → escolher marceneiro; **Gabinete de banheiro** → avaliar entrega (ENT002); histórico; orçamentos |
| `bruno@cliente.com` | Cliente | Acompanhar projetos em usinagem; redirecionar uma ordem recusada |
| `carla@designer.com` | Designer | Mural de projetos disponíveis; **Estante para home office** / **Rack baixo** → enviar proposta (DES001); minhas propostas |
| `diego@designer.com` | Designer | Idem, com outro histórico de propostas |
| `eduardo@marceneiro.com` | Marceneiro | **Guarda-roupa** (proposta de execução enviada); **Painel de TV** em usinagem → finalizar (MAR002); **Cabeceira** finalizada → propor entrega (ENT001) |
| `fabio@marceneiro.com` | Marceneiro | **Sapateira** → iniciar usinagem ou recusar (MAR001); **Guarda-roupa** → enviar proposta de execução |

**Pagamento simulado:** qualquer cartão válido é aprovado; cartões terminados em **0000** são recusados
(demonstra o fluxo alternativo “Falha no pagamento” do APR001). No checkout há o botão “Preencher cartão de teste”.

### Roteiro sugerido para a apresentação (10 min, 4 integrantes)

1. **Visão geral e arquitetura** (~2 min): problema, 3 atores, Django REST + React, tela de login/cadastro com perfis.
2. **Cliente e designer** (~3 min): Ana cadastra uma necessidade (mostrar validações e o código de 8 dígitos);
   Carla envia uma proposta com lista de materiais; Ana compara as propostas, tenta pagar com cartão `…0000`
   (recusado) e depois aprova (as outras propostas são arquivadas e a OS é gerada).
3. **Marceneiro** (~3 min): Fábio envia proposta de execução; Ana escolhe e paga a mão de obra; Eduardo finaliza
   o Painel de TV e propõe a entrega; Ana pede alteração/aprova e confirma o recebimento (histórico).
4. **Entidade multidimensional** (~2 min): tela **Orçamentos** — indicadores, totalização por dimensão,
   cubo (ex.: *Mês × Tipo de material*), e o **Orçamento Final** de um projeto com a consolidação.

---

## 3. Requisitos da disciplina × implementação

| Requisito (Aula 01) | Onde está |
|---|---|
| Pelo menos dois tipos de usuário (atores) | **Cliente, Designer e Marceneiro** — `Usuario` + especializações `Cliente`, `Designer`, `Marceneiro` (`core/models.py`) |
| Autenticação e tela de autenticação | Login/cadastro (`frontend/src/pages/Login.jsx`, `Cadastro.jsx`); token REST (`/api/auth/...`); permissões por perfil (`core/permissions.py`) |
| Sistema de cadastro | Cadastro com escolha de perfil, cria a especialização correta |
| Relação **1 × n** | Cliente → Necessidades; Proposta técnica → Materiais; Ordem de serviço → Propostas de entrega |
| Relação **n × n** | Designer ↔ Necessidade via **PropostaTecnica**; Marceneiro ↔ Ordem de serviço via **PropostaMarcenaria** (entidades associativas do DER) |
| Entidade multidimensional | **OrcamentoFinal** (1:1 com a Ordem de Serviço), cruza materiais, mão de obra e comissão |
| Tela da entidade multidimensional com totalizações | **Orçamentos** (`/orcamentos`): indicadores, totalização por dimensão com linha de total, cubo *linhas × colunas* com totais; **Orçamento Final** (`/orcamentos/:id`) com subtotais por tipo de material e preço total |
| API + frontend com framework JavaScript | API REST em Django REST Framework; frontend em React consumindo-a via `fetch` (`frontend/src/api.js`) |

---

## 4. Casos de uso × telas × API

| Caso de uso | Tela (frontend) | Endpoint(s) |
|---|---|---|
| **NEC001** Cadastro de necessidade | Meus pedidos → “Adicionar novo pedido” | `POST /api/necessidades/` (multipart) |
| **DES001** Inclusão de desenho técnico | Projetos disponíveis → projeto → “Enviar proposta” | `GET /api/necessidades/?estado=ABERTA`, `POST /api/propostas-tecnicas/` |
| **APR001** Aprovar proposta (checkout) | Meus pedidos → pedido → “Aprovar e pagar” | `POST /api/propostas-tecnicas/{id}/aprovar/` |
| Concorrência entre marcenarias (DER) | Marceneiro: Projetos disponíveis → OS; Cliente: OS → “Escolher e pagar” | `POST /api/ordens/{id}/propor-execucao/`, `POST /api/ordens/{id}/escolher-marceneiro/` |
| **MAR001** Iniciar usinagem / recusar | Meus projetos → OS | `POST /api/ordens/{id}/iniciar-usinagem/`, `POST /api/ordens/{id}/recusar/`, `POST /api/ordens/{id}/redirecionar/` |
| **MAR002** Finalizar fabricação | Meus projetos → OS → “Finalizar fabricação” | `POST /api/ordens/{id}/finalizar/` |
| **ENT001** Propor método de entrega | Meus projetos → “Adicionar método de entrega” | `POST /api/ordens/{id}/propor-entrega/` |
| **ENT002** Avaliar método de entrega | OS → “Aprovar proposta” / “Solicitar alteração” | `POST /api/ordens/{id}/avaliar-entrega/` |
| Histórico (v1.3) | Histórico | `GET /api/ordens/?escopo=historico` |
| Notificações | Sino no cabeçalho | `GET /api/notificacoes/`, `POST /api/notificacoes/{id}/lida/` |

### Outros endpoints

| Método | URL | Descrição |
|---|---|---|
| POST | `/api/auth/registro/` | cadastro `{nome, email, senha, tipo, cidade}` → `{token, usuario}` |
| POST | `/api/auth/login/` | `{email, senha}` → `{token, usuario}` |
| POST | `/api/auth/logout/` | invalida o token |
| GET | `/api/auth/eu/` | usuário logado |
| GET | `/api/necessidades/{id}/` | detalhe + propostas recebidas |
| GET | `/api/propostas-tecnicas/` | propostas do designer / recebidas pelo cliente |
| GET | `/api/ordens/?escopo=disponiveis\|meus\|ativos\|historico` | ordens de serviço visíveis ao usuário |
| POST | `/api/ordens/{id}/confirmar-recebimento/` | conclui o projeto (estado *Entregue*) |
| GET | `/api/orcamentos/` e `/api/orcamentos/{id}/` | orçamentos finais |
| GET | `/api/orcamentos/totalizacao/?dimensao=...` | totais de todas as medidas por dimensão |
| GET | `/api/orcamentos/cubo/?linhas=...&colunas=...&medida=...` | tabela cruzada com totais |

Todas as rotas (exceto login/cadastro) exigem o cabeçalho `Authorization: Token <token>`.
A API também é navegável em `http://127.0.0.1:8000/api/` (login em `/api-auth/login/` usando o e-mail como usuário).

---

## 5. Modelo de dados (DER → Django)

```
Usuario (nome, email, senha, tipo, cidade)
 ├── Cliente ── 1:n ── Necessidade (código 8 dígitos, título, cidade, tipo de ambiente,
 │                                  largura, altura, profundidade, foto, esboço,
 │                                  observações, custo esperado, estado)
 ├── Designer ─ n:n (PropostaTecnica) ─ Necessidade
 │                    └── 1:n Material (tipo, descrição, quantidade, unidade, custo unitário)
 └── Marceneiro ─ n:n (PropostaMarcenaria: horas, valor-hora, prazo, status) ─ OrdemServico

PropostaTecnica 1:1 OrdemServico (estado, marceneiro, datas, motivo da recusa)
OrdemServico 1:n PropostaEntrega (modalidade, local, prazo, horários, instruções, estado)  [composição]
OrdemServico 1:1 OrcamentoFinal (qtde/custo de materiais, horas, valor-hora, mão de obra,
                                  comissão do designer, preço total)  [entidade multidimensional]
Pagamento (cliente, tipo: projeto | execução, valor, status, final do cartão)
Notificacao (usuário, mensagem, link, lida)
```

**Estados** (seção 2 da especificação de casos de uso):
- Necessidade: *Aberta → Resolvida*
- Proposta técnica: *Submetida → Aprovada | Arquivada*
- Ordem de serviço: *Pendente → Em usinagem → Finalizada → Entrega acordada → Entregue* (ou *Cancelada*)
- Pagamento: *Aguardando | Aprovado | Recusado | Reembolsado*

**Preço total do orçamento** = custo dos materiais (proposta técnica) + horas × valor-hora (proposta do
marceneiro escolhido) + comissão do designer. Enquanto nenhum marceneiro foi escolhido, a mão de obra é uma
**estimativa** (horas estimadas pelo designer × R$ 60/h) e é recalculada quando o cliente escolhe a marcenaria.

---

## 6. Decisões de implementação (para atualizar os documentos da entrega final)

A entrega final pede as versões atualizadas dos documentos anteriores. Pontos em que o sistema detalha ou
complementa a especificação v1.3 e o DER:

1. **Escolha do marceneiro.** O DER/diagrama de classes prevê várias `Proposta_Marcenaria` por ordem de serviço;
   o MAR001 fala em “ordem pendente direcionada ao marceneiro”. Implementado assim: após o APR001 a OS fica
   *Pendente* e visível para as marcenarias, que enviam propostas de execução; o cliente escolhe uma e paga a
   mão de obra; a OS segue *Pendente* (aguardando início) para o marceneiro escolhido, que inicia ou recusa.
2. **Dois pagamentos** (como no diagrama de classes, “cobrança do designer” e “cobrança do marceneiro”):
   no APR001 o cliente paga materiais + comissão do designer; ao escolher o marceneiro, paga a mão de obra.
   Na recusa (MAR001, fluxo alternativo), o pagamento da execução vira *Reembolsado* e o cliente pode
   **redirecionar** a OS para outras marcenarias sem perder o projeto técnico.
3. **Lista de materiais estruturada**: em vez de um texto livre, cada material tem tipo, descrição, quantidade,
   unidade e custo unitário — é o que permite as totalizações por tipo de material.
4. **Estado final “Entregue”**: após a *Entrega acordada*, o cliente confirma o recebimento e o projeto vai para a
   aba **Histórico** dos três atores (extensão da v1.3).
5. **Notificações** internas (sino no cabeçalho) implementam os passos “o sistema notifica …” dos casos de uso.
6. O código da necessidade é o número sequencial com 8 dígitos (ex.: `00000012`).
7. Formatos aceitos: foto do ambiente JPG/PNG; esboço e desenho técnico JPG/PNG/PDF (arquivos DWG devem ser
   exportados para PDF — fluxo alternativo do DES001).

---

## 7. Estrutura de pastas

```
newfurniture/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── newfurniture/          # settings.py, urls.py
│   └── core/
│       ├── models.py          # entidades do DER
│       ├── services.py        # regras de negócio de cada caso de uso
│       ├── serializers.py     # conversão modelo <-> JSON
│       ├── views.py           # endpoints REST (ViewSets)
│       ├── permissions.py     # acesso por perfil
│       ├── analitico.py       # totalizações / cubo da entidade multidimensional
│       ├── admin.py           # Django admin
│       ├── tests.py           # testes do fluxo completo
│       ├── seed/              # imagens usadas nos dados de demonstração
│       └── management/commands/popular_dados.py
└── frontend/
    ├── package.json, vite.config.js, index.html
    └── src/
        ├── main.jsx, App.jsx  # rotas e layout
        ├── api.js             # cliente da API (fetch + token)
        ├── auth.jsx           # contexto de autenticação
        ├── router.jsx         # roteador por hash (#/pedidos/12)
        ├── styles.css         # visual dos protótipos (cabeçalho caramelo, cards)
        ├── components/        # Navbar, Checkout, cards, modais…
        └── pages/             # uma página por tela
```

---

## 8. Git / GitHub

```bash
git init
git add .
git commit -m "NewFurniture: versão final"
git branch -M main
git remote add origin https://github.com/<usuario>/newfurniture.git
git push -u origin main
```

O `.gitignore` já exclui `db.sqlite3`, `media/`, `.venv/`, `node_modules/` e `dist/`.

---

## 9. Problemas comuns

| Sintoma | Solução |
|---|---|
| “Não foi possível conectar à API” | O backend precisa estar rodando (`python manage.py runserver`) |
| Erro ao rodar `migrate` sobre o usuário (`core.Usuario`) | Rode antes `python manage.py makemigrations core`. Se o banco ficou inconsistente, apague `backend/db.sqlite3` e repita |
| `npm` não encontrado | Instale o Node.js 18+ (LTS) |
| Porta 8000 ou 5173 ocupada | Feche o outro servidor ou use `runserver 8001` (e ajuste o proxy em `vite.config.js`) |
| Quero zerar tudo | Apague `backend/db.sqlite3` e `backend/media/` e rode o `setup` de novo |
