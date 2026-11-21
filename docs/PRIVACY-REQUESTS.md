# Customers' requests about their data

For the pizzeria's staff. A customer can ask what we keep about them, or ask for it to be erased (LGPD, Arts. 18 and 19). This page says what to do, step by step. The tool is [`api/app/dsar.py`](../api/app/dsar.py); the reasoning is in [ADR 0023](adr/0023-retention-of-personal-data.md) and the [data map](../.lgpd/data-map.en.md). Portuguese: [PRIVACY-REQUESTS.pt-BR.md](PRIVACY-REQUESTS.pt-BR.md).

> This is operational guidance, **not legal advice**. A lawyer should check the deadlines and wording before the pizzeria relies on them (the skills we follow say the same).

## 1. Recognize a request

**Any channel counts, and the clock starts when it arrives**: a phone call, a WhatsApp message, a note on the counter, a message to the pizzeria's Telegram. The customer does not have to say "LGPD". "Delete my data", "what do you have about me?", "stop messaging me" are requests. Write it down the same day (step 2).

| The customer says | It is |
|---|---|
| "What do you have about me?" | **Access** (Art. 18, I and II) |
| "Delete my data" / "erase my address" | **Erasure** (Art. 18, VI) |
| "My address is wrong in your system" | **Correction** (Art. 18, III): see 5 |
| "Stop sending me Telegram messages" | **Revoke consent**: tell them to send `/stop` to the bot, which unlinks their chat at once; done |

## 2. Deadlines and the log

- **Confirm or give a simple answer immediately**; a **complete answer** (what, where from, why) **within 15 days** of the request. If the pizzeria qualifies as a small business under the ANPD's rules the deadlines may be longer: **plan on 15 days** until a lawyer says otherwise.
- **Keep a log of requests, with no personal data in it**: date received, channel, type (access, erasure, other), who handled it, date answered, result. Keep it for 3 to 5 years, in a private place that is **not this repository** and not a chat group.

## 3. Check who is asking

Ask in proportion, and **never ask for an ID document or a selfie**: we never had one, and collecting more data to answer a privacy request defeats the purpose.

1. Answer through the **phone number on the order**: call it, or message it, and confirm with something only the customer knows (what they ordered last, roughly when).
2. If they write from a different number, do not give anything out: ask them to ask from the number they ordered with.
3. Someone asking for another person (a parent for a child, a representative) needs a proportionate proof (the child's date of birth and the guardian's relation, or a specific power of attorney). When in doubt, ask the data subject.

## 4. Access ("what do you have about me?")

On the server (or a terminal with access to the API container):

```bash
docker compose exec api python -m app.dsar export --phone "11 99999-0000"
```

It lists every order with that phone number (name, address, items, totals, dates) and the Telegram chat ids linked to them. **The output is personal data**: send it to the customer only, through the verified number, and do not paste it in chats, issues or e-mails to others. Add what the policy says about **where else** it lives (Telegram, the server's backups and logs) once the policy is published.

## 5. Erasure and correction

```bash
docker compose exec api python -m app.dsar erase --phone "11 99999-0000"             # shows what would change
docker compose exec api python -m app.dsar erase --phone "11 99999-0000" --confirm   # does it
```

- It replaces the **name, phone and address** of every order of that number with `[removed]`, in the orders and in their events, and removes the Telegram chat links. **Items and totals stay**: they are the pizzeria's own numbers and identify no one.
- It **refuses while an order is still in progress** (the kitchen needs the address). Finish or cancel it in the kitchen, then run it again.
- What it does **not** reach, and the customer should be told: copies in **backups** of the server until they expire; messages already sent to the customer's **Telegram** (they can delete their chat; Telegram is a separate service); anything the pizzeria keeps **outside this system** (a fiscal note, a delivery notebook), which may have its own legal reason to stay (ask the accountant).
- **Correction** of an old order is rarely useful (it is history). If the customer asks, offer erasure, or correct it by hand only if the order is still open. New orders use whatever they type.

## 6. Answer the customer

Say what was done, what was not and why, and when. Short templates (Portuguese first, the customers' language):

**Access, pt-BR:** "Olá, [primeiro nome]! Confirmamos que guardamos dados de [N] pedido(s) feitos com este telefone. Segue o que temos: [lista]. Os dados ficam só para entregar seu pedido e são trocados depois de 12 meses. Se quiser apagar agora, é só pedir."

**Erasure, pt-BR:** "Olá, [primeiro nome]! Apagamos seu nome, telefone e endereço dos nossos pedidos em [data]. Ficam apenas os itens e valores, sem identificar você. Cópias de segurança do servidor podem guardar os dados antigos até [prazo, quando conhecido] e o Telegram guarda as mensagens que já enviamos: você pode apagar essa conversa por lá."

**Can't do it yet (open order), pt-BR:** "Olá! Seu pedido [código] ainda está em andamento e precisamos do endereço para entregar. Assim que for entregue, apagamos seus dados, no máximo em [data]."

## 7. Never

- Do not refuse with "everything is kept for 5 years": explain what can be removed and what cannot, and why.
- Do not ask for more personal data than the request needs.
- Do not put the customer's data in an issue, a PR, a chat group or this repository.
- Do not run `erase` without checking who is asking (step 3) and without the dry run first.
