# Política de Privacidade (RASCUNHO)

> **RASCUNHO. NÃO PUBLICAR** antes de: (1) a revisão de um advogado ou do encarregado; (2) a resposta de Miguel às perguntas da [#81](https://github.com/SenatoreTeam/SlicePizza/issues/81) (logs, backups, Cloudflare, local do servidor); (3) o nome e o contato reais da pizzaria. Os trechos entre **[colchetes]** estão em aberto. Base: mapa de dados v1 ([`data-map.md`](data-map.md)). Não é aconselhamento jurídico.

**Versão:** rascunho 1 · **Data:** 21/11/2026

Esta política explica como a **[NOME DA PIZZARIA]** trata os dados pessoais de quem faz pedidos pelo nosso site, em linguagem simples.

## 1. Quem é responsável pelos seus dados

A **[NOME DA PIZZARIA]**, **[CNPJ]**, **[endereço]**, é a controladora: decide como e por que usar seus dados.
**Contato para assuntos de privacidade:** **[nome ou "Encarregado de dados"]**, **[e-mail]**, **[telefone/WhatsApp]**.

## 2. Quais dados coletamos e para quê

| Dado | Para quê | Base legal (LGPD, Art. 7º) |
|---|---|---|
| **Nome, telefone e endereço de entrega** (que você digita no pedido) | Receber, preparar e entregar o seu pedido; falar com você se houver problema na entrega | V: execução do contrato (o pedido) |
| **Itens e valor do pedido, data e situação** | O mesmo, e as contas da pizzaria | V: execução do contrato |
| **Código do seu chat no Telegram** (só se você tocar em "Acompanhar no Telegram" e iniciar o bot) | Avisar você de cada etapa do pedido | I: seu consentimento. Você pode parar a qualquer momento enviando `/stop` ao bot |
| **Endereço IP, horário e página acessada** (registros do servidor) | Manter o site funcionando e protegê-lo de abusos | IX: legítimo interesse da pizzaria em segurança **[confirmar teste de legítimo interesse]** |

Não coletamos dados sensíveis (saúde, religião e similares). Não usamos cookies de rastreamento, nem analytics, nem publicidade. O site guarda no seu navegador apenas o código do seu último pedido, para você reencontrá-lo.
**[Crianças e adolescentes: o site não é voltado a menores de 18 anos. Se um pedido for feito por menor, tratamos os dados só para entregar o pedido e nunca para marketing.]**

## 3. Com quem compartilhamos

- **Nossa cozinha**: vê nome, telefone e endereço para preparar e entregar.
- **Telegram**: recebe os avisos que enviamos (o nome do cliente e o código do pedido) e guarda o código do chat de quem escolheu acompanhar. O Telegram é um serviço à parte, com política própria, e **fica fora do Brasil** **[confirmar o mecanismo de transferência]**.
- **Provedor do servidor e quem o administra**: guardam os dados do sistema. **[Nome do provedor; local do servidor: confirmar (#81). Se fora do Brasil, dizer aqui.]**
- **[Cloudflare]**, só se **[confirmar: apenas DNS, ou passa o tráfego]**.
- Não vendemos seus dados e não os usamos para propaganda de terceiros.

## 4. Por quanto tempo guardamos

- **Nome, telefone e endereço de um pedido: 12 meses** depois que o pedido termina (entregue ou cancelado). Depois, são **substituídos** por `[removed]`; ficam só os itens e valores, sem identificar você.
- **Código do seu chat no Telegram: 7 dias** depois que o pedido termina.
- **Registros do servidor (IP, horário, página): [prazo; confirmar com o dono do servidor, #81]**.
- **Cópias de segurança do servidor** podem guardar dados antigos por **[prazo; confirmar, #81]**, e depois são apagadas.

## 5. Seus direitos

Você pode, a qualquer momento e sem custo, pedir: **confirmar** se tratamos seus dados; **acessar** o que temos; **corrigir**; **apagar** (anonimizar) dados desnecessários ou tratados com consentimento; saber **com quem compartilhamos**; **revogar o consentimento** (Telegram: `/stop`); e **reclamar à ANPD** (Autoridade Nacional de Proteção de Dados).
Peça pelo contato da seção 1, por qualquer canal. Respondemos de imediato ao que for simples e **em até 15 dias** a uma resposta completa. Para sua segurança, **confirmamos que é você** ligando ou escrevendo para o telefone do pedido (nunca pedimos documento).

## 6. Segurança

Usamos conexão protegida (HTTPS), acesso à cozinha com senha, limite de pedidos por endereço para barrar abusos, varreduras de segurança antes de publicar novas versões e apagamento automático dos dados antigos. Nenhum sistema é perfeito: se houver um incidente que possa lhe causar dano, avisaremos você e a ANPD nos termos da lei.

## 7. Mudanças nesta política

Quando mudarmos esta política, publicaremos a nova versão aqui, com a data. O código do site e o histórico de mudanças são públicos: <https://github.com/SenatoreTeam/SlicePizza>.

---

## Para a revisão (não publicar esta parte)

- [ ] Nome, CNPJ, endereço e contato do encarregado preenchidos (Art. 41: indicação do encarregado, salvo dispensa para pequeno porte pela ANPD).
- [ ] Bases legais conferidas por advogado (principalmente IX para os registros de acesso, e I para o Telegram).
- [ ] Transferência internacional (Art. 33): Telegram e, se for o caso, o servidor: mecanismo confirmado e dito acima.
- [ ] Prazos de logs e de backups preenchidos com a resposta de Miguel (#81).
- [ ] O prazo de 12 meses foi aprovado (ADR 0023).
- [ ] Texto sobre menores (ECA Digital) revisto.
- [ ] A página é linkada no formulário do pedido e no rodapé, e a versão em inglês confere.
- [ ] Os valores de retenção do código (`RETENTION_MONTHS`, `RETENTION_CHAT_DAYS`) batem com a seção 4.
