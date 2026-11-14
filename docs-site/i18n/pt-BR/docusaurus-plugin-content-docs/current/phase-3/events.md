# Fase 3 — Eventos e a fila

A API avisa o resto do sistema o que acontece com um pedido publicando **eventos**. Esta página
explica a ideia; o raciocínio e as alternativas estão no
[ADR 0004](/adr/0004-order-events-outbox-rabbitmq).

## O problema: dois lugares para escrever

Quando um cliente faz um pedido, a API precisa salvá-lo no PostgreSQL **e** avisar o RabbitMQ.
São dois sistemas diferentes, então um pode dar certo enquanto o outro falha:

- Salvar e depois publicar: se a publicação falhar, o pedido existe, mas ninguém é avisado.
- Publicar e depois salvar: se o salvamento falhar, todos são avisados de um pedido que não
  existe.

## A solução: uma outbox transacional

```
POST /orders ─► uma transação no banco:
                  1. insere o pedido
                  2. insere uma linha "order.created" em order_events
                ─► o cliente recebe a resposta

thread de repasse (na API) ─► lê as linhas não enviadas ─► publica ─► marca como enviadas
```

Como o pedido e o seu evento são gravados **na mesma transação**, ou os dois existem ou nenhum
existe. Uma pequena thread de repasse dentro da API publica então os eventos guardados no
RabbitMQ e marca cada um como enviado. Se o RabbitMQ estiver fora do ar, os eventos ficam na
tabela e saem quando ele voltar.

Detalhes que importam:

- **Pelo menos uma vez.** Uma queda entre publicar e marcar pode publicar um evento duas vezes,
  então todo evento leva um id único e quem consome ignora repetições.
- **Sem perda silenciosa.** As mensagens são persistentes, o repasse espera a confirmação do
  RabbitMQ, e uma mensagem que nenhuma fila aceita fica guardada na tabela em vez de ser
  descartada.
- **Um só publicador.** Um advisory lock do PostgreSQL garante que apenas um processo da API
  execute o repasse por vez.

## O que é publicado

Um exchange do tipo topic, `slicepizza.events`, com dois tipos de evento:

| Routing key | Quando |
|---|---|
| `order.created` | um pedido é feito |
| `order.status_changed` | o status dele muda |

Cada evento é um pequeno documento JSON com o id do pedido, o status novo e o anterior, e o que
uma notificação precisa (o nome do cliente, as pizzas e o total). O endereço de entrega e o
telefone ficam de fora da fila de propósito. A API funciona mesmo sem o RabbitMQ configurado: os
eventos então ficam esperando na tabela.

A [referência da API](https://github.com/SenatoreTeam/SlicePizza/blob/main/api/README.md) lista as configurações, e o
[README do worker](https://github.com/SenatoreTeam/SlicePizza/blob/main/worker/README.md) mostra como inspecionar as filas.
