# Shopping list

Add groceries by messaging the shopping channel, display them, request organization, and start a new list while retaining history.

## Sub-features

- Each nonblank line in a human message adds one trimmed item.
- Bot messages, other channels, empty text, and messages starting with `!` or `[ ! ]` add nothing.
- `/lista` shows the current list ID and items, or the empty-list message.
- `/ordenar` returns a categorized list using GPT-4, handles an empty list, and reports API failure.
- `/zerar` advances the current list ID and retains old item rows.

## How to get to it (user POV)

Send ordinary multiline text to channel `1328396042689052682`. Select `/lista`, `/ordenar`, or `/zerar` in the Discord slash picker. Slash callbacks themselves are not channel-restricted.

## Driving it with Discord computer use

Use a dedicated disposable database and approved channel. Capture `/lista` before changes and query `shopping_state` and `shopping_items` read-only. Paste `verify-house-bot arroz` and `verify-house-bot leite` as two lines, submit once, capture the message, and invoke `/lista`. Both items must appear once in insertion order with the same list ID. Query committed rows from a new database connection, not the write session.

Send `!verify-house-bot ignored` and `[ ! ] verify-house-bot ignored`, then repeat `/lista` and the query. Neither should add rows. For the other-channel branch use an agreed test channel; do not spam unrelated channels. Bot-message filtering requires an existing authorized bot-message source; do not replace a human submission with a synthetic callback and claim live proof.

Invoke `/ordenar` and capture its thinking state and `Sorted Shopping List` reply. Original item names must survive in the output. Compare database rows before/after; sorting only renders a response and does not reorder or replace persisted rows.

Invoke `/zerar`, assert the reply announces old ID plus one, then invoke `/lista` and assert it is empty with that new ID. Confirm old rows still exist. Invoke `/ordenar` on the empty list and expect the empty-list response with no OpenAI request. API-error coverage belongs to a boundary integration test unless an actual failure is observed.

## Gotchas

- Ordinary shopping additions have no confirmation reply; persistence plus `/lista` proves success.
- Duplicates are permitted. Do not assume de-duplication.
- `/lista` can initialize shopping state if missing, so it is not a strictly read-only doctor.
- `/ordenar` calls OpenAI with model `gpt-4` only when the list is nonempty.
- Shared-list changes cannot be undone through an item-removal command. Reset preserves history and is not cleanup.
