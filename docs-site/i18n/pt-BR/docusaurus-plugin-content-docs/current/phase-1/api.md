# Fase 1 — API

A API de pedidos é uma pequena aplicação FastAPI que conversa com o PostgreSQL por meio do
SQLAlchemy 2.0. Ela serve o cardápio e permite que os clientes façam pedidos que a
cozinha move por uma sequência fixa de status.

Esta página explica **como a API se comporta**. Para as rotas exatas, exemplos de requisição,
variáveis de ambiente e comandos de teste, veja a
[referência da API em `api/README.md`](https://github.com/SenatoreTeam/SlicePizza/blob/main/api/README.md), que fica junto
do código e é a fonte única desses detalhes (em inglês).

O FastAPI também publica uma documentação interativa de todas as rotas em `/docs`
(`/api/docs` atrás do Caddy, a partir da Fase 2):

![Swagger UI com as rotas da API](@site/static/img/screenshots/api-docs.png)

## Preços

Os preços vêm da tabela `pizzas`, nunca da requisição, e são guardados em
**centavos** para evitar erros de arredondamento de ponto flutuante. Cada item do pedido guarda um instantâneo do
preço unitário no momento em que o pedido foi feito, então mudar o cardápio depois
não altera os pedidos antigos.

## Fluxo de status

```
received ──► preparing ──► out_for_delivery ──► delivered
    │
    └──► cancelled
```

- Um pedido só pode ser cancelado enquanto ainda está `received`.
- `delivered` e `cancelled` são finais.
- Pular uma etapa, voltar ou alterar um pedido final retorna `409 Conflict`.
- Enviar o status atual de novo não faz nada e retorna `200`.
- Duas requisições que alteram o mesmo pedido ao mesmo tempo são tratadas uma depois
  da outra: a linha do pedido fica bloqueada enquanto o status é verificado e alterado.

## Erros

| Código | Quando |
|---|---|
| `404 Not Found` | O id do pedido ou um `pizza_id` não existe |
| `409 Conflict` | `POST /orders` com uma pizza indisponível, ou uma mudança de status que o fluxo não permite |
| `422 Unprocessable Entity` | Entrada inválida: id de pedido malformado, campos vazios, quantidade fora do intervalo, mais de 20 itens ou 50 pizzas, ou a mesma pizza duas vezes (use `quantity`) |
| `503 Service Unavailable` | A API não consegue acessar o banco de dados |

## Testes

A suíte de testes roda em um SQLite em memória (sem Docker), e o CI
também a executa no PostgreSQL. Veja [Tests em `api/README.md`](https://github.com/SenatoreTeam/SlicePizza/blob/main/api/README.md#tests).
