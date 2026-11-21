# Fase 9 — Visão geral

**Pedido do Zé:** _"Uma cliente perguntou o que vocês fazem com o telefone dela."_

:::info Situação
**Em andamento** (desde 21/11/2026). Quase tudo está no ar desde a versão 1.5.0; a
política de privacidade espera uma revisão jurídica e respostas do dono do servidor. Veja o
[roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md).
:::

## O que a Fase 9 entrega

- **Um mapa dos dados pessoais que guardamos** (em [`.lgpd/`](https://github.com/SenatoreTeam/SlicePizza/blob/main/.lgpd/data-map.md)):
  nome, telefone e endereço de cada pedido, e o chat do Telegram de quem acompanha um pedido.
  Ele achou dois problemas, resolvidos abaixo.
- **Sem Google Fonts.** As páginas mandavam o endereço de cada visitante ao Google para
  carregar as fontes; agora as fontes vêm do nosso próprio domínio.
- **O link do pedido não mostra dados pessoais.** Quem tem o link vê as pizzas e a
  situação, não quem pediu nem onde ([ADR 0022](/adr/0022-order-link-without-personal-data)).
- **Dados antigos somem sozinhos.** 12 meses depois do fim do pedido, nome, telefone e
  endereço são substituídos; os vínculos com o Telegram saem em 7 dias
  ([ADR 0023](/adr/0023-retention-of-personal-data)).
- **Um cliente pode pedir para ver ou apagar seus dados.** Um comando responde, com um
  [passo a passo](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/PRIVACY-REQUESTS.pt-BR.md).

## Falta

- **A política de privacidade** está rascunhada em português e inglês, mas não está no site:
  precisa de revisão jurídica, dos dados reais da pizzaria e de respostas sobre os logs e
  backups do servidor ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)).
