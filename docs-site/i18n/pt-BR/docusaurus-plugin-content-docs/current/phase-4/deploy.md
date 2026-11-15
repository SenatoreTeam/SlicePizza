# Fase 4 — O deploy

Depois que [o pipeline](/docs/phase-4/pipeline) publica as imagens de uma versão, ele faz o
deploy delas: **primeiro no staging, e em produção só se o staging funcionou**. Esta página
explica como; o raciocínio está no [ADR 0009](/adr/0009-staging-then-production), e a
configuração do servidor no
[DEPLOY.md](https://github.com/SenatoreTeam/SlicePizza/blob/main/docs/DEPLOY.md#staging).

## Dois ambientes

| | Staging | Produção |
|---|---|---|
| Endereço | `staging.slicepizza.senatore.tech` | `slicepizza.senatore.tech` |
| Quem usa | O pipeline, e quem quiser testar uma mudança de verdade | Clientes e a cozinha |
| Tag da imagem | `staging` | `latest` |
| Dados | Só pedidos de teste | Pedidos reais |
| Telegram | Nenhum (o worker escreve as mensagens no log) | O bot da pizzaria |

Os dois rodam as mesmas imagens a partir do mesmo arquivo compose
([`infra/dokploy/docker-compose.yml`](https://github.com/SenatoreTeam/SlicePizza/blob/main/infra/dokploy/docker-compose.yml)),
cada um com seu próprio banco de dados, fila e segredos.

## Do merge à produção

```
imagens sha-<commit> publicadas
   │
   ├─► :staging aponta para sha-<commit>  ─► webhook do staging ─► o Dokploy faz o deploy
   │     espera o staging informar <commit>, depois faz um pedido e
   │     o move no painel da cozinha
   │
   └─► só se isso passou:
       :latest aponta para sha-<commit>   ─► webhook da produção ─► o Dokploy faz o deploy
         espera a produção informar <commit>, depois verificações só de leitura
```

- **Mover uma tag não gera nada de novo.** A produção recebe exatamente as imagens que
  acabaram de funcionar no staging.
- **O webhook de deploy** é uma URL secreta que o Dokploy dá para cada serviço. Ela só pode
  refazer o deploy daquele serviço, então é um segredo muito menor do que a senha do servidor
  ou uma chave SSH. Ela fica em um **environment** do GitHub (`staging`, `production`), que só os
  jobs que fazem deploy ali conseguem ler.
- **As verificações** esperam (até 10 minutos) que `/version` e `/api/health` informem o novo
  commit: um deploy leva um tempinho, e a versão antiga responde enquanto isso. Depois conferem
  o site, o cardápio e que as rotas privadas continuam privadas. Só o staging recebe um pedido;
  a produção nunca é alterada.
- **Uma etapa que falha para a linha.** Se o staging falha, a produção fica com a versão que
  já tem, e a execução no GitHub mostra o que deu errado.

## Voltando uma versão

Se mesmo assim uma versão se comportar mal em produção, o workflow **Roll back production**
(aba Actions → Run workflow) recebe o commit de uma versão boa anterior, aponta o `latest` de
volta para as imagens dele, faz o deploy e confere. Depois corrija ou reverta a mudança antes
de fazer outro merge, porque o próximo merge faz o deploy para a frente de novo.

## Onde olhar

- A execução do pipeline na `main` termina com **deploy (staging)** e **deploy (production)**,
  cada um com um link para o seu ambiente.
- **Deployments**, na página do repositório no GitHub, lista o que foi para cada ambiente, e
  quando.
- `https://slicepizza.senatore.tech/version` diz qual commit está no ar.
