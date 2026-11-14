# Fase 3 — Notificações no Telegram

Um serviço separado, o **worker**, lê os eventos do RabbitMQ e envia as mensagens no Telegram.
Esta página explica como ele se comporta; os passos de configuração estão no
[README do worker](https://github.com/SenatoreTeam/SlicePizza/blob/main/worker/README.md), e as decisões estão no
[ADR 0005](/adr/0005-notification-worker) e no
[ADR 0006](/adr/0006-customer-telegram-opt-in).

## Quem recebe o quê

- **O chat da pizzaria** recebe uma mensagem quando um pedido chega e quando o status dele muda.
- **Os clientes** só recebem mensagens se pedirem. Na página do pedido, **Follow on Telegram**
  abre o bot com o id do pedido, e ao apertar _Start_ aquele chat fica ligado ao pedido. O
  comando `/stop` desfaz a ligação. Ninguém recebe mensagem sem fazer isso.

O botão só aparece quando o site conhece o nome de usuário do bot (`TELEGRAM_BOT_USERNAME`), e
só enquanto o pedido ainda está a caminho.

## A fila protege as mensagens

O worker lê de uma **quorum queue** durável chamada `notifications`. Uma mensagem só é removida
**depois** que o Telegram a aceitou, e o worker pega uma mensagem por vez. Assim:

- **Worker parado:** as mensagens esperam na fila e são enviadas quando ele volta. Esse é o
  objetivo da fase, e um teste no CI prova isso: para o worker, faz um pedido, liga o worker e
  confere que a mensagem chega.
- **Telegram lento ou falhando:** o worker espera e tenta de novo, respeitando os pedidos de
  "retry after" do Telegram.
- **Configuração errada** (um token de bot inválido, por exemplo): o worker mantém a mensagem e
  continua tentando em vez de jogá-la fora, então corrigir a configuração basta.
- **Uma mensagem que nunca poderá ser entregue** (rejeitada pelo Telegram) vai para uma
  **dead-letter queue**, onde pode ser inspecionada, em vez de travar a fila.
- **Um cliente que bloqueou o bot** é ignorado e desligado.

Cada mensagem é enviada no máximo uma vez por evento e por chat, mesmo que o RabbitMQ entregue
o evento duas vezes.

## De quem são os dados

A API, e não o worker, guarda quais chats seguem quais pedidos (uma tabela
`telegram_subscriptions`). O worker pergunta à API por uma pequena rota interna protegida por
um segredo compartilhado, o `INTERNAL_API_TOKEN`; o Caddy nunca repassa essas rotas para a
internet. Cada evento leva então a lista de chats a avisar, e o worker não precisa de banco de
dados próprio.

Sem um token de bot, o worker continua rodando e apenas **registra no log** o que enviaria, que
é como funcionam o desenvolvimento local e as verificações automáticas. Os nomes dos clientes
aparecem nesses logs, então esse modo não serve para produção.
