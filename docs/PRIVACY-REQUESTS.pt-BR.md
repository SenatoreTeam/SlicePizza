# Pedidos dos clientes sobre os seus dados

Para a equipe da pizzaria. Um cliente pode perguntar o que guardamos sobre ele, ou pedir que seja apagado (LGPD, Arts. 18 e 19). Esta página diz o que fazer, passo a passo. A ferramenta é [`api/app/dsar.py`](../api/app/dsar.py); o raciocínio está no [ADR 0023](adr/0023-retention-of-personal-data.md) e no [mapa de dados](../.lgpd/data-map.md). Inglês: [PRIVACY-REQUESTS.md](PRIVACY-REQUESTS.md).

> Isto é orientação operacional, **não aconselhamento jurídico**. Um advogado deve conferir os prazos e os textos antes de a pizzaria depender deles (as skills que seguimos dizem o mesmo).

## 1. Reconhecer um pedido

**Qualquer canal vale, e o prazo começa quando o pedido chega**: uma ligação, uma mensagem no WhatsApp, um bilhete no balcão, uma mensagem no Telegram da pizzaria. O cliente não precisa dizer "LGPD". "Apaga meus dados", "o que vocês têm de mim?", "parem de me mandar mensagem" são pedidos. Anote no mesmo dia (passo 2).

| O cliente diz | É |
|---|---|
| "O que vocês têm de mim?" | **Acesso** (Art. 18, I e II) |
| "Apaguem meus dados" / "apaguem meu endereço" | **Eliminação** (Art. 18, VI) |
| "Meu endereço está errado no sistema" | **Correção** (Art. 18, III): veja o 5 |
| "Parem de me mandar mensagem no Telegram" | **Revogar o consentimento**: peça que mande `/stop` para o bot, que desvincula o chat na hora; pronto |

## 2. Prazos e o registro

- **Confirmar ou dar uma resposta simples na hora**; uma **resposta completa** (o quê, de onde veio, para quê) **em até 15 dias** do pedido. Se a pizzaria se enquadrar como pequeno porte nas regras da ANPD, os prazos podem ser maiores: **conte com 15 dias** até um advogado dizer outra coisa.
- **Mantenha um registro dos pedidos, sem dado pessoal nele**: data de recebimento, canal, tipo (acesso, eliminação, outro), quem atendeu, data da resposta, resultado. Guarde por 3 a 5 anos, em lugar privado que **não seja este repositório** nem um grupo de conversa.

## 3. Conferir quem está pedindo

Pergunte na medida certa, e **nunca peça documento de identidade nem selfie**: nunca tivemos, e coletar mais dados para atender um pedido de privacidade contraria o propósito.

1. Responda pelo **telefone que está no pedido**: ligue ou mande mensagem para ele e confirme com algo que só o cliente sabe (o que pediu por último, mais ou menos quando).
2. Se escrever de outro número, não entregue nada: peça que peça do número com que fez o pedido.
3. Quem pede por outra pessoa (pai ou mãe por um filho, um representante) precisa de uma prova proporcional (a data de nascimento da criança e o vínculo do responsável, ou uma procuração específica). Na dúvida, pergunte ao titular.

## 4. Acesso ("o que vocês têm de mim?")

No servidor (ou em um terminal com acesso ao contêiner da API):

```bash
docker compose exec api python -m app.dsar export --phone "11 99999-0000"
```

Ele lista todos os pedidos com aquele telefone (nome, endereço, itens, valores, datas) e os ids de chat do Telegram ligados a eles. **A saída é dado pessoal**: envie só ao cliente, pelo número conferido, e não cole em conversas, issues nem e-mails para outras pessoas. Acrescente o que a política disser sobre **onde mais** os dados estão (Telegram, backups e logs do servidor) quando a política for publicada.

## 5. Eliminação e correção

```bash
docker compose exec api python -m app.dsar erase --phone "11 99999-0000"             # mostra o que mudaria
docker compose exec api python -m app.dsar erase --phone "11 99999-0000" --confirm   # faz
```

- Troca por `[removed]` o **nome, telefone e endereço** de todos os pedidos daquele número, nos pedidos e nos eventos deles, e remove os vínculos do Telegram. **Itens e valores ficam**: são os números da própria pizzaria e não identificam ninguém.
- **Recusa enquanto houver pedido em andamento** (a cozinha precisa do endereço). Termine ou cancele na cozinha e rode de novo.
- O que **não** alcança, e o cliente deve saber: cópias nos **backups** do servidor até expirarem; mensagens já enviadas ao **Telegram** do cliente (ele pode apagar a conversa; o Telegram é um serviço à parte); e qualquer coisa que a pizzaria guarde **fora deste sistema** (uma nota fiscal, um caderno de entregas), que pode ter motivo legal próprio para ficar (pergunte ao contador).
- **Corrigir** um pedido antigo raramente adianta (é histórico). Se o cliente pedir, ofereça a eliminação, ou corrija à mão só se o pedido ainda estiver aberto. Pedidos novos usam o que a pessoa digitar.

## 6. Responder ao cliente

Diga o que foi feito, o que não foi e por quê, e quando. Modelos curtos:

**Acesso:** "Olá, [primeiro nome]! Confirmamos que guardamos dados de [N] pedido(s) feitos com este telefone. Segue o que temos: [lista]. Os dados ficam só para entregar seu pedido e são trocados depois de 12 meses. Se quiser apagar agora, é só pedir."

**Eliminação:** "Olá, [primeiro nome]! Apagamos seu nome, telefone e endereço dos nossos pedidos em [data]. Ficam apenas os itens e valores, sem identificar você. Cópias de segurança do servidor podem guardar os dados antigos até [prazo, quando conhecido] e o Telegram guarda as mensagens que já enviamos: você pode apagar essa conversa por lá."

**Ainda não dá (pedido em andamento):** "Olá! Seu pedido [código] ainda está em andamento e precisamos do endereço para entregar. Assim que for entregue, apagamos seus dados, no máximo em [data]."

## 7. Nunca

- Não recuse com "tudo fica guardado por 5 anos": explique o que pode ser removido e o que não pode, e por quê.
- Não peça mais dados pessoais do que o pedido exige.
- Não ponha dados do cliente em issue, PR, grupo de conversa nem neste repositório.
- Não rode `erase` sem conferir quem pede (passo 3) e sem antes ver o que mudaria.
