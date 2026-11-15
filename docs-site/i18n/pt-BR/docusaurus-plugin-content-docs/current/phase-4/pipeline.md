# Fase 4 — O pipeline

Todo Pull Request e todo merge na `main` rodam um único workflow do GitHub Actions, o
**Pipeline** ([`ci.yml`](https://github.com/SenatoreTeam/SlicePizza/blob/main/.github/workflows/ci.yml)).
Esta página explica as etapas e por que elas estão nessa ordem; o raciocínio está no
[ADR 0008](/adr/0008-one-gated-pipeline).

## As etapas

```
lint ──► testes ────┐   API no SQLite e no Postgres, worker com RabbitMQ,
                    │   Telegram de ponta a ponta, smoke test do docker compose
lock files ─────────┴─► imagens (api, web, worker) ──► pipeline passed
```

1. **Lint.** O [ruff](https://docs.astral.sh/ruff/) lê o código Python (API, worker e scripts
   do CI) e o shellcheck lê os scripts de shell, procurando erros que uma máquina encontra sem
   rodar nada: um import sem uso, um nome que não existe, uma exceção engolida por engano. Leva
   segundos, então roda primeiro.
2. **Testes**, todos em paralelo: os testes da API no SQLite e em um Postgres de verdade, os
   testes do worker com um RabbitMQ de verdade, um cliente acompanhando um pedido no Telegram de
   ponta a ponta, e a stack inteira subindo com `docker compose`. Ao lado deles, uma verificação
   de que os lock files batem com os arquivos `.in`.
3. **Imagens.** Só quando tudo acima passou as três imagens são geradas: `api`, `web` e
   `worker`, todas do mesmo commit.
4. **pipeline passed**: uma última verificação que só fica verde se todas as etapas ficaram. É
   a verificação que a proteção da branch exige, então um Pull Request com uma etapa vermelha não
   pode receber merge.

## Pull Request ou main

| | Pull Request | `main` |
|---|---|---|
| Lint e testes | Rodam | Rodam |
| Imagens | Geradas, para provar que funcionam | Geradas **e publicadas** no GHCR |
| Tags | — | `sha-<commit>` e `latest` |

Um merge cujo pipeline falha não publica nada, e o servidor continua rodando a última versão
boa. As execuções na `main` são uma de cada vez, então uma execução mais antiga nunca publica o
`latest` depois de uma mais nova.

Toda segunda-feira o pipeline também roda sozinho na `main` e publica as imagens de novo, para
que as correções de segurança que as imagens oficiais do Python e do Caddy recebem sob a mesma
tag cheguem ao servidor.

## Qual versão está rodando?

O pipeline gera cada imagem com o commit de onde ela veio (`GIT_COMMIT`):

- a API informa em `/api/health`: `{"status":"ok","database":"ok","version":"<commit>"}`
- o contêiner web responde em `/version`
- o worker escreve na primeira linha do log: `Starting version <commit> ...`

Geradas na sua máquina, elas dizem `unknown`. O deploy usa isso para conferir que a versão que
acabou de entregar é a que está respondendo.

## Rodando o lint você mesmo

O ruff é instalado com as dependências de desenvolvimento da API e do worker. Na raiz do
repositório:

```bash
ruff check .          # o que o pipeline roda
ruff check --fix .    # corrige o que der (ordem dos imports, sintaxe antiga...)
```

As regras estão em [`ruff.toml`](https://github.com/SenatoreTeam/SlicePizza/blob/main/ruff.toml).
Elas procuram prováveis bugs, não estilo: não há formatador para discutir.
