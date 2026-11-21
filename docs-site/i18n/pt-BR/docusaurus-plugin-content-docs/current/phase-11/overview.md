# Fase 11 — Visão geral

**Pedido do Zé:** _"Como eu sei que ninguém mexeu no que a gente roda?"_

:::info Situação
**Em andamento** (desde 21/11/2026). Veja o [roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 11 entrega

- **Tudo o que rodamos é fixado.** Cada passo do pipeline aponta para um commit exato, e cada
  imagem base para um digest exato, então uma tag movida por outra pessoa não muda o que
  construímos. O Dependabot propõe as atualizações, agrupadas.
- **Um lugar para relatar uma vulnerabilidade** em particular
  ([`SECURITY.md`](https://github.com/SenatoreTeam/SlicePizza/blob/main/SECURITY.md)), um código de conduta e modelos de issue. A varredura
  de segredos do GitHub bloqueia um push com segredo.
- **Buscadores ficam de fora** da API e do painel da cozinha.
- **Quem revisa o quê** ([`CODEOWNERS`](https://github.com/SenatoreTeam/SlicePizza/blob/main/.github/CODEOWNERS)): uma mudança no pipeline,
  nas imagens, nos arquivos do servidor ou nas versões pede a revisão de nós dois; uma
  mudança no login, no limite de pedidos ou no banco pede a do Ettore.

## Planejado

- **Um login da cozinha mais seguro** ([ADR 0024](/adr/0024-kitchen-login-in-the-api),
  [#98](https://github.com/SenatoreTeam/SlicePizza/issues/98)): uma página de login no lugar
  da janela do navegador, 15 minutos bloqueado depois de 5 senhas erradas de um endereço, e
  uma sessão que termina em 12 horas, com botão Sair.
- **Confirmar a segurança do próprio servidor** e **trocar todos os segredos uma vez**, para
  provar que a rotina do [`SECRETS.md`](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/SECRETS.md) funciona
  ([#99](https://github.com/SenatoreTeam/SlicePizza/issues/99),
  [#103](https://github.com/SenatoreTeam/SlicePizza/issues/103)).
