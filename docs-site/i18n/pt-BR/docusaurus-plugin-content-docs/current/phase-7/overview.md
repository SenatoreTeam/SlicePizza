# Fase 7 — Visão geral

**Pedido do Zé:** _"Sexta tem promoção de pizza a R$20."_

:::info Situação
Esta fase está **concluída** (19/11/2026). Duas partes dependem do dono do servidor: um contêiner
`redis` e o número de cópias da API. Veja o
[roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 7 entrega

- **Um teste de carga** com o [k6](https://k6.io) em `infra/loadtest/`: clientes lendo o cardápio,
  um em cada dez pedindo. O primeiro resultado foi uma surpresa: **10 vezes uma sexta normal já
  passava**, com 570 requisições por segundo no modo de estresse. Uma promoção de verdade fica bem
  abaixo disso.
- **Um cache do cardápio no Redis** ([ADR 0019](/adr/0019-redis-menu-cache)): desligado se não
  configurado, e feito para que o Redis fora do ar ou lento nunca piore a API (um teste mostrou que
  um Redis parado fazia uma requisição esperar 26 segundos, antes de corrigir). De 570 para 866
  requisições por segundo.
- **Várias cópias da API atrás do Caddy** ([ADR 0020](/adr/0020-api-replicas)): o Caddy encontra
  cada cópia pelo DNS do Docker e divide as requisições. 708 → 1212 → 1572 requisições por segundo
  com 1, 2 e 4 cópias. O relay da fila de eventos já era seguro para rodar mais de uma vez (um
  bloqueio no banco).
- **Notas de capacidade**: quanto uma VPS aguenta e o que fazer quando não basta.

## Sem Kubernetes

Em uma VPS, o Kubernetes acrescenta um plano de controle e nenhum hardware. A escala aqui vem do que
o Docker já oferece ([ADR 0017](/adr/0017-docker-only-infrastructure)).

## O que os números ensinam

Neste tamanho, as réplicas servem mais à **disponibilidade** (uma cópia pode reiniciar sem derrubar
requisições) do que à velocidade. E meça antes e depois: o cache ganhou 50% porque o teste mostrou
onde o tempo ia.
