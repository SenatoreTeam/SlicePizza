# Fase 4 — Versões e releases

A produção roda **versões numeradas**, nunca "o que a `main` tiver agora": um merge só chega à
produção quando acrescenta uma versão. Esta página explica como as versões são numeradas, onde
são escritas e onde aparecem; o raciocínio está no [ADR 0009](/adr/0009-numbered-versions) e no
[ADR 0010](/adr/0010-releases-file), e o lado do servidor no
[DEPLOY.md](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/DEPLOY.md#releasing-a-version).

## O número: `MAJOR.MINOR.PATCH`

[Versionamento Semântico](https://semver.org/lang/pt-BR/):

| Parte | Quando sobe | Exemplo |
|---|---|---|
| **MAJOR** | Algo que funcionava passa a funcionar diferente: muda uma rota ou o formato de um evento, ou o banco precisa de uma mudança à mão | 1.4.2 → **2.0.0** |
| **MINOR** | Algo novo, e tudo o que funcionava continua funcionando: uma rota, uma página, uma mensagem nova | 1.4.2 → **1.5.0** |
| **PATCH** | Uma correção, ou a atualização de uma imagem base ou dependência, sem nada novo para quem usa | 1.4.2 → **1.4.3** |

Quando o MINOR sobe, o PATCH volta a zero; quando o MAJOR sobe, os dois voltam.

## Onde fica escrita: `releases.toml`

O [`releases.toml`](https://github.com/SenatoreTeam/SlicePizza/blob/main/releases.toml), na raiz
do repositório, é a **fonte única** das versões. Uma versão nova entra no **topo**:

```toml
[[release]]
version = "1.5.0"
date = 2026-12-01
title.en = "Pizzas can be marked as sold out"          # opcional, uma frase
title.pt-br = "Pizzas podem ser marcadas como esgotadas"

[[release.item]]
kind = "new"                   # new | improvement | fix | security
area = "Menu"                  # Menu | Orders | Kitchen | Telegram | System
text.en = "The kitchen can mark a pizza as sold out, and the menu hides it until it is back."
text.pt-br = "A cozinha pode marcar uma pizza como esgotada, e o cardápio a esconde até ela voltar."

[[release.item]]
kind = "security"
area = "System"
source = "dependabot"          # proposta pelo Dependabot, com o Pull Request dela
pr = 52
text.en = "Libraries updated, with security fixes."
text.pt-br = "Bibliotecas atualizadas, com correções de segurança."
```

- Um item por mudança, **nas palavras de quem usa o sistema**: "O cardápio esconde as pizzas
  esgotadas", e não "Adicionada a coluna sold_out".
- Textos em inglês e português. A release do GitHub e as páginas usam os em inglês.
- As atualizações do Dependabot têm `source = "dependabot"` e o `pr` delas, para separar as
  mudanças do próprio projeto das do Dependabot.
- Uma correção de segurança diz que algo foi corrigido, nunca como explorar a falha.
- A linha `**Current version:**` do README diz a mesma versão.

O lint confere tudo isso: o formato, os tipos e as áreas, os dois idiomas, a mais nova primeiro e
cada versão maior que a de baixo, as datas e a linha do README. Num Pull Request ele também diz,
num aviso, se o merge publica uma versão.

## Do merge à produção

```
o PR acrescenta 1.5.0 no topo do releases.toml ──► revisado, merge
pipeline na main: lint ─► testes ─► imagens sha-<commit> ─► pipeline passed
job release: slicepizza-{api,web,worker}:1.5.0 (as mesmas imagens, nada gerado de novo)
             release v1.5.0 no GitHub: "1.5.0 – Pizzas can be marked as sold out"
                                       - **New · Menu:** The kitchen can mark…
                                       │
servidor, a cada 2 minutos ◄───────────┘  backup ─► :1.5.0 ─► deploy ─► verificações
                                       │
production check (GitHub) ◄────────────┘  espera a 1.5.0 no site e confere, só lendo
```

A execução do pipeline termina com o **production check**: verde quando a produção responde com a
versão nova e passa nas verificações, vermelho quando isso não acontece em 15 minutos
([ADR 0011](/adr/0011-production-check)). O servidor só avança quando as verificações dele passam,
então vermelho quer dizer "ainda não está no ar", e não "a produção quebrou".

Um merge que não acrescenta versão não muda nada na produção: vários merges podem sair juntos numa
versão.

## Onde ela aparece

| Onde | O quê |
|---|---|
| O site do cardápio | "Version 1.5.0 · what changed" no rodapé, com link para a release no GitHub |
| O painel da cozinha | A versão no rodapé, e o **What's new**: cada versão com os itens dela. Depois de uma atualização, um aviso diz que há versão nova até o What's new ser aberto naquele navegador |
| `/api/health` | `release` (a versão) e `version` (o commit) |
| `/api/docs` | A versão, ao lado do nome da API |
| O log do worker | `Starting version 1.5.0 (commit …)` ao iniciar |
| GitHub | As [releases](https://github.com/SenatoreTeam/SlicePizza/releases), uma por versão, as tags das imagens no GHCR, o **production check** da execução que publicou a versão, e **Deployments** (cada versão que entrou no ar) |

As páginas leem o `/releases.json`, que a imagem do web gera a partir do `releases.toml` no build;
a API e o worker recebem a versão do pipeline.
