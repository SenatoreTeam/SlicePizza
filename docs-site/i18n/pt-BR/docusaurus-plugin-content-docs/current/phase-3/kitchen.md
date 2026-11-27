# Fase 3 — O painel da cozinha

A cozinha precisa de uma tela para ver os pedidos abertos e movê-los adiante. Esta página explica
como ela funciona e por que foi construída assim; o raciocínio completo está no
[ADR 0007](/adr/0007-kitchen-login) e, para o login de hoje, no [ADR 0024](/adr/0024-kitchen-login-in-the-api), e as configurações estão no [DEPLOY.md](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/DEPLOY.md).

## O painel

Em **`/kitchen/`** a cozinha vê três colunas: **New** (novos), **In the oven** (no forno) e
**On the way** (a caminho). Cada pedido é uma comanda que mostra há quanto tempo ele espera
(vermelho depois de 30 minutos), o que fazer e para quem é. Um botão leva a comanda para a
próxima etapa; pedidos novos também podem ser cancelados, depois de uma confirmação. O painel se
atualiza a cada poucos segundos, avisa a cozinha se outra tela já mudou um pedido, e continua
mostrando os últimos pedidos carregados se o sistema ficar inacessível.

![O painel da cozinha com os pedidos em três colunas](@site/static/img/screenshots/kitchen-board.png)

## Mantendo privado

Até esta fase, qualquer pessoa que soubesse o id de um pedido podia mudar o status dele, e uma
mudança de status agora envia uma mensagem no Telegram ao cliente. Uma lista de todos os pedidos
também expõe telefones e endereços. As duas coisas agora são só da cozinha.

```
cozinha ──/kitchen/──► Caddy ──► os arquivos do painel (públicos, sem dados)
cozinha ──POST /kitchen/api/session {senha}──► Caddy ──► API: senha certa? cookie de sessão
cozinha ──/kitchen/api/orders + cookie──► Caddy ──► API: sessão válida? os pedidos
qualquer outra pessoa ──/api/orders, PATCH /api/orders/{id}/status──► API: 401
```

Como as partes dividem o trabalho (desde o [ADR 0024](/adr/0024-kitchen-login-in-the-api);
antes, o Caddy pedia a senha numa janela do navegador):

- **A página** pede a senha da cozinha. O login dura **12 horas** naquele aparelho, e o
  botão **Log out** encerra.
- **A API** confere a senha com um hash bcrypt (nunca a própria senha) e responde com um
  cookie de sessão que a página não consegue ler. Depois de **5 senhas erradas de um mesmo
  endereço, esse endereço espera 15 minutos**: um script não adivinha a senha, e outra
  pessoa não consegue trancar a cozinha de verdade.
- **O Caddy** manda as chamadas da cozinha para a API com o hash e um token secreto, que só
  existe no servidor. O `/api` público não adiciona nenhum dos dois, então o login e o
  cookie só funcionam na página da cozinha. Sem um hash configurado, o `/kitchen` não existe
  (404).

Os clientes não são afetados: eles continuam lendo o próprio pedido pelo id.

## O que isso ainda não faz

É **um login compartilhado**. Todos na cozinha usam a mesma senha, não há papéis e nada registra
quem mudou o quê. Isso basta para uma pizzaria e evita construir gerenciamento de usuários; o
[ADR 0024](/adr/0024-kitchen-login-in-the-api) deixa espaço para contas individuais depois.
