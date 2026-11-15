# Fase 3 — Visão geral

**Pedido do Zé:** _"Os clientes querem saber quando a pizza está a caminho."_

Na Fase 3, cada mudança de status vira uma mensagem: para o chat do Telegram da pizzaria
quando um pedido chega, e para os clientes que pedirem, conforme o pedido avança. A cozinha
também ganha uma tela para tocar os pedidos.

:::info Situação
Tudo nesta fase está construído e passa nas verificações automáticas, inclusive o objetivo da
fase (derrubar o worker sem perder nenhuma mensagem). O painel da cozinha já está no ar; a fila,
o worker e as mensagens no Telegram entram no ar quando o bot, o RabbitMQ e o worker forem
configurados no servidor. A [Fase 2](/docs/phase-2/overview) está concluída.
:::

## O que a Fase 3 entrega

- O **RabbitMQ** como fila de mensagens, e uma **outbox** na API para que um pedido e o seu
  evento sejam sempre salvos juntos. Veja [Eventos e a fila](/docs/phase-3/events).
- Um **worker de notificações** que lê a fila e envia mensagens no Telegram, para o chat da
  pizzaria e para os clientes que tocarem em **Follow on Telegram**. Veja
  [Notificações no Telegram](/docs/phase-3/notifications).
- Um **painel da cozinha** em `/kitchen`, protegido por login, onde a cozinha move os pedidos
  adiante. Veja [O painel da cozinha](/docs/phase-3/kitchen).

## Por que uma fila

A API poderia chamar o Telegram diretamente quando um status muda. Aí, um Telegram lento ou
fora do ar deixaria o pedido do cliente lento ou faria ele falhar, e uma reinicialização na hora
errada perderia uma mensagem. Com uma fila, a API só registra o que aconteceu e responde na
hora. Um worker separado faz a parte lenta, no seu próprio ritmo, e as mensagens esperam em
segurança enquanto ele está parado.

## O problema que esta fase cria

Agora são quatro serviços (API, site, fila, worker) e vários segredos, todos atualizados com um
merge na `main` e esperando o servidor. Cada mudança é conferida à mão, e nada diz se o sistema
no ar está saudável. As Fases 4 e 5 (automação e observabilidade) respondem a isso.
