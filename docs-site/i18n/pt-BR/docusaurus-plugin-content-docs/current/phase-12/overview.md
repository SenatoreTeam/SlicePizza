# Fase 12 — Visão geral

**Pedido do Zé:** _"Quebrou às 7 da noite de sexta."_

:::info Situação
**Em andamento** (desde 21/11/2026). Veja o [roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 12 entrega

- **O health check avisa sobre pedidos travados** (no ar desde a versão 1.6.0).
  O `/api/health` agora diz `"outbox":"late"` quando uma atualização de pedido espera mais
  de 5 minutos para sair para o Telegram, para um monitor avisar antes de os clientes notarem.
  Ele continua respondendo "saudável", de propósito: um problema no Telegram ou no RabbitMQ
  não deve fazer o servidor voltar a versão nem reiniciar a API, o que não resolveria.

## Planejado

- **Quebrar uma versão de propósito** e cronometrar como o servidor volta para a anterior, e
  **restaurar um backup com nossos dados**, com o dono do servidor
  ([#103](https://github.com/SenatoreTeam/SlicePizza/issues/103)).
- **Runbooks** para uma noite ruim: a cozinha não vê os pedidos, o Telegram ficou mudo, o
  site está lento ([#100](https://github.com/SenatoreTeam/SlicePizza/issues/100)).
- **Docs para pessoas**: um início rápido, um glossário, perguntas frequentes e um manual curto
  da cozinha em português ([#102](https://github.com/SenatoreTeam/SlicePizza/issues/102)).
