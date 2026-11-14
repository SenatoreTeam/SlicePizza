# Fase 3 — O painel da cozinha

A cozinha precisa de uma tela para ver os pedidos abertos e movê-los adiante. Esta página explica
como ela funciona e por que foi construída assim; o raciocínio completo está no
[ADR 0007](/adr/0007-kitchen-login), e as configurações estão no [DEPLOY.md](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/DEPLOY.md).

## O painel

Em **`/kitchen/`** a cozinha vê três colunas: **New** (novos), **In the oven** (no forno) e
**On the way** (a caminho). Cada pedido é uma comanda que mostra há quanto tempo ele espera
(vermelho depois de 30 minutos), o que fazer e para quem é. Um botão leva a comanda para a
próxima etapa; pedidos novos também podem ser cancelados, depois de uma confirmação. O painel se
atualiza a cada poucos segundos, avisa a cozinha se outra tela já mudou um pedido, e continua
mostrando os últimos pedidos carregados se o sistema ficar inacessível.

## Mantendo privado

Até esta fase, qualquer pessoa que soubesse o id de um pedido podia mudar o status dele, e uma
mudança de status agora envia uma mensagem no Telegram ao cliente. Uma lista de todos os pedidos
também expõe telefones e endereços. As duas coisas agora são só da cozinha.

```
cozinha ──/kitchen/ (usuário + senha)──► Caddy ──► os arquivos do painel
cozinha ──/kitchen/api/orders (mesmo login)──► Caddy ──► API
                  o Caddy troca o login por "Authorization: Bearer <token>"
qualquer outra pessoa ──/api/orders, PATCH /api/orders/{id}/status──► API: 401
```

Duas camadas, cada uma fazendo o que sabe fazer bem:

- **O Caddy** pede usuário e senha (guarda-se um hash bcrypt, nunca a senha). Sem um hash
  configurado, o `/kitchen` não existe (404).
- **A API** só aceita as requisições da cozinha com um token secreto, que o Caddy adiciona
  depois do login. O token fica só no servidor, então o navegador nunca o vê.

Os clientes não são afetados: eles continuam lendo o próprio pedido pelo id.

## O que isso ainda não faz

É **um login compartilhado**. Todos na cozinha usam a mesma senha, não há papéis e nada registra
quem mudou o quê. Isso basta para uma pizzaria e evita construir gerenciamento de usuários, e o
[ADR 0007](/adr/0007-kitchen-login) diz o que mudaria para dar suporte a contas individuais.
Limitar tentativas repetidas de senha errada fica para a fase de segurança.
