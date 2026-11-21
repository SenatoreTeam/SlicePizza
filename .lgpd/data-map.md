# Mapa de dados pessoais: SlicePizza

**Versão:** v1 | **Situação:** Preliminar | **Data:** 21/11/2026
**Responsável técnico:** Ettore | **Contato de proteção de dados (controlador):** a ser definido pela pizzaria (9.2) | **Revisado por advogado:** não
**Método:** engenharia reversa do repositório (modelos, eventos, worker, servidor web, front-end), como no fluxo para sistemas existentes das skills. O que existe no próprio servidor cabe ao dono do servidor confirmar ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)).

> Não é aconselhamento jurídico. As bases legais abaixo são **propostas** para a revisão humana. Os artigos são da Lei 13.709/2018 (LGPD), salvo indicação.

## 1. Quem e o quê

- **Controlador:** a pizzaria que opera o sistema (neste projeto, a fictícia Pizzaria do Zé; em uma implantação real, o negócio real).
- **Titulares:** clientes que fazem pedidos (adultos; **menores não são excluídos**: não há verificação de idade, então se deve supor que alguns pedidos venham de adolescentes); a equipe da cozinha (um login compartilhado); quem estiver no chat do Telegram da pizzaria.
- **Dados sensíveis (Art. 5º, II):** nenhum coletado. Não há campos de saúde, alergia, religião ou similares.
- **Larga escala ou alto risco (Res. CD/ANPD 2/2022, Art. 4º):** preliminarmente **não**: volume pequeno, sem vigilância, sem perfilamento, sem tecnologia emergente. Rever se o sistema crescer.
- **Cookies, rastreadores, analytics:** nenhum. O único armazenamento no navegador está abaixo (A005). Não há scripts de terceiros; há uma **folha de estilo** de terceiro (A007).

## 2. Atividades de tratamento

### A001. Receber um pedido

| Campo | Valor |
|---|---|
| Finalidade (Art. 6º, I) | Receber, preparar e entregar o pedido que o cliente fez |
| Base legal proposta | Art. 7º, V: execução de contrato ou de procedimentos preliminares a pedido do titular |
| Titulares | Clientes |
| Dados | Nome, telefone, endereço de entrega, itens e total, situação e horários |
| Origem | Fornecidos pelo cliente no formulário do pedido |
| Onde | Postgres: tabelas `orders`, `order_items` |
| Quem vê | A cozinha (A004); quem tiver o link do pedido (A005); o dono do servidor (banco, backups) |
| Retenção | **12 meses depois que o pedido termina**; então nome, telefone e endereço viram `[removed]`; itens, totais e datas ficam ([ADR 0023](../docs/adr/0023-retention-of-personal-data.md), tarefa 9.3). **No ar desde a 1.5.0 (21/11/2026)**; os primeiros pedidos chegam a 12 meses no fim de 2027. Pedidos em aberto nunca são tocados |
| Risco | Telefone e endereço dizem onde a pessoa mora: tratar como dado a proteger, não como "só um bilhete de entrega" |

### A002. Eventos do pedido (outbox) e a fila

| Campo | Valor |
|---|---|
| Finalidade | Avisar a cozinha e o cliente de cada pedido novo e de cada mudança de situação, sem perder nenhum ([ADR 0004](../docs/adr/0004-order-events-outbox-rabbitmq.md)) |
| Base legal proposta | Art. 7º, V, como A001 |
| Dados | Id do pedido, **nome do cliente**, itens, situação e os ids dos chats do Telegram que acompanham o pedido. Telefone e endereço ficam **de fora de propósito** |
| Onde | Postgres `order_events.payload` (JSON); filas do RabbitMQ até o worker ler |
| Retenção | O nome do cliente em `order_events.payload` é substituído junto com o do pedido (ADR 0023); a fila esvazia em segundos. **No ar desde a 1.5.0 (21/11/2026)** |

### A003. Mensagens no Telegram

| Campo | Valor |
|---|---|
| Finalidade | (a) Avisar o chat da pizzaria de cada pedido novo; (b) avisar o cliente sobre o próprio pedido, **só se ele escolheu "Acompanhar no Telegram"** e iniciou o bot |
| Base legal proposta | (a) Art. 7º, V; (b) Art. 7º, I: consentimento, dado pela própria ação do cliente. Ele pode parar com o comando de parar do bot, e o chat é desvinculado |
| Dados | O id do chat do Telegram do cliente (tabela `telegram_subscriptions`), o código curto do pedido e o nome do cliente nos textos das mensagens |
| Terceiro | **Telegram**: recebe e guarda as mensagens e o id do chat. Papel jurídico a confirmar com o advogado (provável controlador independente do próprio serviço) |
| Transferência internacional | Sim: os servidores do Telegram ficam fora do Brasil. Mecanismo a confirmar (Art. 33; Res. CD/ANPD 19/2024). A política deve dizer |
| Retenção | Vínculos de chat: removidos **7 dias depois que o pedido termina** (ADR 0023, no ar desde a 1.5.0). Mensagens no Telegram: fora do nosso controle |
| Observações | O worker registra ids de chat (não os textos) em alguns casos; com o Telegram desligado, em desenvolvimento, registra a mensagem que enviaria (com nomes) |

### A004. O painel da cozinha

| Campo | Valor |
|---|---|
| Finalidade | Deixar a cozinha ver e atualizar os pedidos |
| Base legal proposta | Art. 7º, V |
| Dados | Os pedidos da A001 por inteiro (nome, telefone, endereço); o nome de usuário da cozinha |
| Acesso | Um login **compartilhado** (autenticação básica do Caddy, hash bcrypt) e um token entre os contêineres web e API. Sem limite de tentativas; não atribuível a uma pessoa ([`SECRETS.md`](../docs/SECRETS.md)) |
| Armazenamento no navegador | `localStorage`: a última versão das novidades que a cozinha viu (sem dado pessoal) |

### A005. A página do pedido, para o próprio cliente

| Campo | Valor |
|---|---|
| Finalidade | Deixar o cliente acompanhar o pedido |
| Dados mostrados | `GET /orders/<id>` devolve o andamento e os itens a **quem tiver o link** (um id aleatório impossível de adivinhar; sem login). **Corrigido, no ar desde a 1.5.0** (tarefa 9.7, [ADR 0022](../docs/adr/0022-order-link-without-personal-data.md)): antes devolvia também nome, telefone e endereço. **No ar desde a 1.5.0 (21/11/2026)** |
| Armazenamento no navegador | A chave `slicepizza:last-order` do `localStorage` guarda o id do pedido no aparelho do próprio cliente |
| Lacuna fechada | O link é um segredo ao portador, e links são encaminhados: a visão pública agora **não tem dado pessoal** (itens, situação, total) |

### A006. Logs de acesso e de segurança

| Campo | Valor |
|---|---|
| Finalidade | Operar e defender o serviço: achar erros, perceber abuso (o limite de pedidos, [ADR 0021](../docs/adr/0021-hardening.md)) |
| Base legal proposta | Art. 7º, IX: legítimo interesse (falta um teste curto); ver também o Marco Civil da Internet, Art. 15 (registros de acesso a aplicações, 6 meses), a conferir com o advogado |
| Dados | **Endereço IP**, horário, URL (as páginas de pedido contêm o id do pedido, então um IP pode ser ligado a um pedido), user agent, status. Log de acesso do contêiner web; log da API; os contadores do limitador (IP, só em memória, somem ao reiniciar); os logs do proxy do servidor |
| Onde | Logs dos contêineres no servidor; logs do proxy (Traefik) do servidor |
| Retenção | **Desconhecida**: depende das configurações de Docker e do proxy do servidor ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)) |

### A007. Fontes do Google

| Campo | Valor |
|---|---|
| O quê | As páginas do cardápio e da cozinha carregam fontes de `fonts.googleapis.com` e `fonts.gstatic.com` |
| Efeito | O **IP e os dados do navegador de cada visitante vão para o Google** (fora do Brasil) só por abrir a página, sem aviso e sem uma base que possamos defender |
| Correção | **Feita, no ar desde a 1.5.0** (tarefa 9.6, [#82](https://github.com/SenatoreTeam/SlicePizza/issues/82)): as fontes são servidas do nosso próprio domínio (`/fonts/`, Instrument Sans e Young Serif sob a Licença de Fonte Aberta SIL) e a Content-Security-Policy não permite mais o Google. **No ar desde a 1.5.0.** Desde a 1.5.0 a página não faz requisição a terceiros |

### A008. Backups e o servidor

| Campo | Valor |
|---|---|
| O quê | A VPS inteira tem backup feito pelo dono do servidor ([ADR 0018](../docs/adr/0018-server-backups.md)), então todas as tabelas acima estão nos backups |
| Consequência | Um cliente apagado ou anonimizado continua nos backups antigos até eles expirarem: a política deve dizer, e a retenção dos backups deve ser curta o bastante para ser razoável |
| Em aberto | Prazo de retenção, criptografia, localização da VPS e dos backups ([#81](https://github.com/SenatoreTeam/SlicePizza/issues/81)) |

## 3. Terceiros e seus papéis

| Terceiro | O que recebe | Papel proposto | Fora do Brasil? | Em aberto |
|---|---|---|---|---|
| Telegram | Ids de chat, nomes nas mensagens | Controlador independente (serviço próprio) | Sim | Confirmar papel e mecanismo |
| Google (Fontes) | IP e dados do navegador do visitante | Controlador independente | Sim | Removido no código (9.6); no ar desde a 1.5.0 |
| Provedor da VPS e o dono do servidor | Tudo que está guardado no servidor | Operador (Art. 39) | A confirmar (local da VPS) | #81; um contrato de tratamento entre a pizzaria e o dono do servidor |
| Cloudflare | Consultas de DNS; **todas as requisições, se houver proxy** | Operador | Sim | É só DNS ou proxy? (#81) |
| GitHub | O código, issues, logs de CI (sem dados de clientes) | n/a | Sim | Manter dados de clientes fora de issues e logs |

## 4. Achados, por ordem de importância

1. **Sem política de privacidade** e sem como o cliente ver o que guardamos: 9.2, 9.4.
2. **Sem retenção** (dados dos clientes para sempre, e o `order_events.payload` repetindo o nome): corrigido no código pela 9.3, no ar desde a 1.5.0.
3. **Fontes do Google** mandavam o IP de cada visitante ao Google: corrigido no código pela 9.6, no ar desde a 1.5.0.
4. **O link do pedido mostrava telefone e endereço** a quem o tivesse: corrigido no código pela 9.7, no ar desde a 1.5.0.
5. **Logs e backups desconhecidos** no servidor: #81. Uma política não pode prometer o que não confirmamos.
6. **Transferência internacional** (Telegram, a VPS): o Art. 33 deve ser tratado na política.
7. **Login compartilhado da cozinha**: ninguém responde por um vazamento; plano na Fase 11 (login da cozinha).
8. **Menores** podem pedir: uma linha na política, e nenhum uso dos dados para marketing.

## 5. Próximos passos

- Revisão de advogado ou encarregado das bases legais e do texto sobre a transferência.
- Tarefas 9.2 a 9.7 no [`docs/ROADMAP.md`](../docs/ROADMAP.md#phase-9-a-customer-asked-what-you-do-with-her-phone-number).
- Refazer este mapa sempre que entrar um campo novo, um terceiro novo ou um log novo.
