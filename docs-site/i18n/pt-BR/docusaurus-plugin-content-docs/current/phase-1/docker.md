# Fase 1 — Docker

A Fase 1 roda tudo com Docker Compose: o contêiner da API e um contêiner PostgreSQL
16. Os comandos passo a passo estão no
[README da raiz](https://github.com/SenatoreTeam/SlicePizza#running-the-system-phase-1); esta página explica
o que acontece por trás deles.

## Iniciando a stack

```bash
cp .env.example .env
docker compose up --build -d --wait
```

O Compose inicia os contêineres em ordem:

1. O **Postgres** sobe primeiro. Seu healthcheck (`pg_isready`) fica saudável
   assim que ele aceita conexões.
2. **A API** só sobe depois disso, por causa de
   `depends_on: condition: service_healthy`. Ao iniciar, ela cria as tabelas,
   popula o cardápio e só então abre a porta 8000.

Sem `--wait`, o `up -d` retorna assim que o contêiner da API foi *iniciado*,
enquanto ela ainda pode estar criando tabelas ou populando o cardápio, então um `curl`
imediato pode falhar. O `--wait` só retorna quando o healthcheck da própria API passa.

Confira se a API está no ar e consegue acessar o banco de dados:

```bash
curl http://localhost:8000/health
# {"status":"ok","database":"ok"}
```

## Portas

| Serviço | Na sua máquina | Configurável com |
|---|---|---|
| API | `127.0.0.1:8000` | — |
| Postgres | `127.0.0.1:5432` | `POSTGRES_HOST_PORT` no `.env` |

Ambas ficam presas a `127.0.0.1`, então não são expostas à sua rede.
Se você já roda o PostgreSQL na sua máquina, o `docker compose up` falha com
**"port is already allocated"**: defina outra porta no `.env`, por exemplo
`POSTGRES_HOST_PORT=5433`.

## Persistência

Os dados do banco ficam no volume nomeado `slicepizza_pgdata` (o Compose coloca o nome do projeto,
`slicepizza`, como prefixo do volume `pgdata`). Por isso, parar a stack **sem** `-v`
mantém os pedidos:

```bash
docker compose down
docker compose up -d --wait
```

Para inspecionar o volume: `docker volume inspect slicepizza_pgdata`.

`docker compose down -v` apaga o volume e, com ele, todos os dados. Você precisa dele
quando o esquema do banco muda: a API cria as tabelas que faltam na inicialização,
mas nunca altera uma tabela que já existe.

## Seed

Na inicialização, a API popula o cardápio apenas se a tabela `pizzas` estiver vazia,
então reiniciar a stack não duplica pizzas.
