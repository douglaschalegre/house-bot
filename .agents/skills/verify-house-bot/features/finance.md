# Finance views

Read current or historical finance snapshots imported by Dindin.

## Sub-features

- `/dindin` renders the current month's salary, percentage, and contribution summary.
- `/historico month:3 year:24` renders March 2024 with required period options.
- `/detalhado` includes current-month expense rows and skips empty rows.
- Missing snapshots request `/sincronizar`; read failures produce an error reply.

## How to get to it (user POV)

Select a finance slash command in the configured guild. The callback has no channel restriction. Use an appropriate channel so private finance data is not posted to a wider audience.

## Driving it with Discord computer use

Confirm the target database has Dindin-owned finance tables. Choose an existing snapshot for historical proof and record its expected values with a read-only query. Invoke `/historico`, select month `3` and year `24` only if that snapshot exists, or choose another observed period. Capture the submitted option values and resulting `Sheet: Expenses MM/YY` reply.

Invoke `/dindin` and `/detalhado` for the current Brazil-time period. Compare names `Douglas`, `Luana`, `Total`, values, expense lines, and `_Última sincronização:` against the committed snapshot. The timestamp renders in America/Sao_Paulo time. Compare database rows before/after to establish these commands did not import finance data.

For an observed period with no snapshot, invoke `/historico` and require `Finance data is not synchronized for this period. Run /sincronizar first.` with Discord's code formatting around the command. A missing table is a different case and yields `An error occurred while reading finance data.`.

## Gotchas

- `year` is two-digit 0 through 99; month is 1 through 12. Discord owns option validation.
- Current month is calculated in America/Sao_Paulo, not the host's UTC date.
- Views use the database snapshot; the monthly automatic report instead reads Google Sheets.
- Do not seed finance rows via internal setters and call that an import proof. Use Dindin's normal import in a disposable environment.
