# Fase 8 — Visão geral

**Pedido do Zé:** _"Ouvi dizer que hackers atacam pizzarias."_

:::info Situação
Esta fase está **concluída** (19/11/2026). Veja o
[roadmap](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/ROADMAP.md) e o
[ADR 0021](/adr/0021-hardening).
:::

## O que a Fase 8 entrega

- **Varredura de vulnerabilidades antes de publicar.** O [Trivy](https://trivy.dev) confere cada
  imagem atrás de vulnerabilidades graves conhecidas que tenham correção, e de segredos esquecidos
  dentro, **antes** de a imagem ser publicada. A primeira varredura já achou o que corrigir: as
  imagens levavam o `pip` e cópias de bibliotecas que nada usava em execução, então o `pip` foi
  removido. Dois achados dentro do Caddy ainda não têm correção; ficam aceitos em um arquivo, com
  motivo e **data de validade**, e a varredura volta a falhar se ninguém olhar.
- **Varredura de segredos em todo o histórico do Git.** O Gitleaks lê cada commit a cada mudança. A
  primeira execução só achou coisas parecidas (um token inventado de teste e uma senha padrão de
  demonstração), agora listadas com o motivo.
- **Um limite de pedidos.** Um endereço pode fazer 30 pedidos por minuto; depois disso a API
  responde "muitos" e diz quando tentar de novo. Cada pedido chega à cozinha e ao Telegram, então
  spam custa a atenção das pessoas, não só tempo de computador. Ler o cardápio nunca é limitado.
- **Sem root.** `api`, `worker`, `web` e `redis` rodam como usuários comuns. O Postgres e o
  RabbitMQ começam como root só para arrumar suas pastas e depois trocam de usuário, que é como as
  imagens oficiais deles funcionam.
- **Uma lista de todos os segredos.**
  [`docs/SECRETS.md`](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/SECRETS.md): o que
  cada um protege, onde fica, quanto poder tem e como trocá-lo.

## Bom saber

- O limite de pedidos confia no endereço do cliente enviado pelos proxies na frente. Se estivessem
  mal configurados e todos parecessem um só endereço, o limite valeria para todos juntos; por isso o
  guia de deploy diz como conferir.
- Nem tudo está neste repositório: as senhas, chaves SSH e backups do próprio servidor são do dono
  dele, então a revisão os lista como "a confirmar".
- Segurança é rotina, não um recurso: as datas de validade, as atualizações semanais de dependências
  e a troca anual de segredos é que a mantêm verdadeira.
