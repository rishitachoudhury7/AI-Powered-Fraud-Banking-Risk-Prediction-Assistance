# Historical Fraud Case Reference Log
## Internal Reference — Illustrative Case Studies for Transaction Investigation

**Note:** The cases below are composite, illustrative scenarios constructed for training and reference purposes. They do not represent real customer data or real institutions, but reflect commonly observed fraud patterns in retail banking transaction monitoring.

---

## Case 001: Full Account Drain via Unauthorized Transfer

**Pattern summary:** Account takeover leading to complete balance withdrawal.

A customer's account, with a historical average balance of approximately 12,000, received no unusual activity for several months. Within a single 24-hour window, a TRANSFER of the full account balance (98,400) was initiated to a previously unseen recipient account, reducing the origin balance to zero. The receiving account had been opened only three days prior and had no transaction history before this inbound transfer.

**Outcome:** Flagged by rule-based monitoring (full balance drain + new destination account). Escalated to human analyst within 2 hours of the transaction. Confirmed as account takeover following customer contact — the customer had not initiated the transfer. Funds were partially recovered by freezing the destination account before onward movement.

**Key indicators present:** Full origin balance drain, destination account newly created, transaction inconsistent with account's historical behavior, no prior relationship between origin and destination accounts.

---

## Case 002: Mule Account Pass-Through (TRANSFER → CASH_OUT Chain)

**Pattern summary:** Multi-hop laundering via a linked TRANSFER followed by immediate CASH_OUT.

A dormant account with a near-zero balance received an inbound TRANSFER of 340,000 from a compromised account. Within the same processing window (step), the recipient account initiated a CASH_OUT of the full received amount, leaving the account at zero balance again. Individually, neither transaction scored highly on a single-transaction fraud model: the TRANSFER appeared as a large but plausible transfer, and the CASH_OUT appeared as a routine withdrawal of an existing balance.

**Outcome:** The pattern was only identified when a human analyst reviewed both transactions together as a linked pair, noting the recipient account had no other transaction history and returned to zero balance immediately after the CASH_OUT. Retroactively classified as mule account activity.

**Key indicators present:** Recipient account balance near-zero both before and after the transaction pair, minimal time gap between inbound and outbound transaction, transaction amounts nearly identical (little to no funds retained).

**Lesson for automated systems:** Transaction-level models without access to linked-transaction or account-history context are structurally unable to detect this pattern reliably. This category of fraud requires either account-level feature engineering (e.g., tracking balance-in vs balance-out within short windows) or a rules layer specifically designed to flag rapid full pass-through activity.

---

## Case 003: Large CASH_OUT Misclassified Due to Ambiguous Destination Balance

**Pattern summary:** A high-value CASH_OUT where the destination account already held a substantial pre-existing balance, causing a fraud model to under-score a transaction that rule-based monitoring flagged as high-risk.

An origin account with a balance of approximately 1,270,000 was fully drained via a CASH_OUT transaction. The destination account, however, already held a balance of over 1,000,000 prior to this transaction — meaning the post-transaction destination balance did not cleanly reflect a simple pass-through of the transferred funds. The transaction-level fraud model scored this transaction at a relatively low probability, likely because engineered features comparing expected versus actual balance changes (analogous to "difference from expected balance" features) suggested the transaction was less anomalous than a typical mule pattern, where destination balances usually sit near zero both before and after.

**Outcome:** Despite the low model score, rule-based monitoring flagged the transaction for three reasons: the origin account was fully emptied, the transaction represented over 90% of the sender's balance, and the transaction amount exceeded standard high-value thresholds. The case was escalated to a human analyst, who noted the discrepancy between the model's low score and the strength of the rule-based signals as itself worth investigating — the destination account's pre-existing balance made it plausible this was either a legitimate business account or a more sophisticated mule account that intentionally maintains a buffer balance to avoid near-zero-balance detection heuristics.

**Key indicators present:** Full origin balance drain, high-value threshold breach, model probability significantly lower than rule-based risk assessment would suggest — a divergence pattern that should itself be treated as noteworthy.

**Lesson for automated systems:** When SHAP-derived feature attributions and rule-based flags disagree with the model's raw probability output, this divergence should be explicitly surfaced to the reviewing analyst rather than resolved silently in favor of either signal. Some mule account operators may deliberately maintain non-zero destination balances specifically to evade detection heuristics premised on near-zero balances — a form of adversarial adaptation that transaction-level models trained on historical data may not yet reflect.

---

## Case 004: Structuring via Multiple Sub-Threshold Transfers

**Pattern summary:** A single intended large transfer broken into several smaller transactions to avoid triggering high-value monitoring thresholds.

Over a six-hour window, an account initiated seven separate TRANSFER transactions, each ranging between 28,000 and 31,000 — each individually below the institution's 200,000 high-value review threshold used in single-transaction rule checks. Cumulatively, the seven transactions totaled approximately 205,000, exceeding the threshold that would have triggered review had it occurred as a single transaction.

**Outcome:** No individual transaction in the sequence triggered rule-based or model-based flags in isolation. The pattern was only identified during a periodic velocity review that aggregated transaction counts and cumulative amounts per account over rolling time windows.

**Key indicators present:** Multiple transactions just below a known reporting or review threshold, repeated similar amounts, short time window, same origin account across all transactions.

**Lesson for automated systems:** Structuring cannot be detected through single-transaction scoring alone, regardless of model sophistication. Effective detection requires velocity-based monitoring — tracking transaction frequency and cumulative amount per account within rolling time windows — as a complement to per-transaction fraud scoring.

---

## Case 005: Legitimate Large Withdrawal Correctly Approved

**Pattern summary:** A large transaction with surface-level similarity to fraud patterns, correctly identified as legitimate after review.

A long-standing customer account with a stable high balance initiated a CASH_OUT of approximately 450,000, reducing the account to a low but non-zero balance. The transaction amount exceeded the standard high-value review threshold, triggering a rule-based flag.

**Outcome:** Upon review, the transaction was associated with a documented, pre-notified large purchase (property transaction), consistent with the customer's historical account activity and prior communication with the bank. No further action was taken; transaction was approved.

**Key indicators present:** High-value threshold breach (rule-flagged) but consistent with account's historical pattern, customer-initiated with prior notice, non-zero remaining balance.

**Lesson for automated systems:** Not every rule-flagged transaction is fraudulent. Rule-based flags are designed to maximize sensitivity (catching potential fraud) at the cost of some false positives; human review remains necessary to distinguish true fraud from legitimate high-value activity, particularly for established accounts with consistent historical behavior.

---

## Case 006: Routine PAYMENT Transaction Correctly Scored Low

**Pattern summary:** Transaction type: PAYMENT, amount: moderate. A merchant payment with no fraud indicators, included to anchor the model's expected baseline for this transaction type.

A customer account with a stable balance history made a PAYMENT of approximately 8,500 to a known merchant category, reducing the origin balance by exactly the payment amount. The destination balance fields were unpopulated (as is standard for PAYMENT transactions in this system, where the counterparty is a merchant rather than a tracked account).

**Outcome:** No rule flags triggered. Model score was low, consistent with expectations. Transaction processed normally with no analyst review.

**Key indicators present:** Origin balance reduced by exactly the payment amount, no destination account balance fields, amount consistent with typical spending pattern for the account.

**Lesson for automated systems:** PAYMENT transactions are structurally different from TRANSFER/CASH_OUT — funds leave the institution's tracked account graph entirely rather than moving to another monitored account. Fraud is rare in this category, but a low model score here should not be over-interpreted as a strong "safe" signal for other transaction types; it reflects PAYMENT's low base rate, not general model reliability. Analysts should be aware the model has very little fraud-labeled PAYMENT data to learn from, so a genuinely fraudulent PAYMENT (e.g., a hijacked recurring billing setup) may go under-scored simply because the model has rarely seen a positive example of this type.

---

## Case 007: CASH_IN Deposit With No Outbound Risk

**Pattern summary:** Transaction type: CASH_IN, amount: large. An inbound deposit, included to document why CASH_IN alone is not a meaningful fraud signal in this system.

An account received a CASH_IN deposit of approximately 60,000, increasing its balance accordingly. No outbound activity followed within the observed window.

**Outcome:** No rule flags triggered (the rules engine is designed around outbound balance depletion, which does not apply here). Model score was low.

**Key indicators present:** Inbound-only balance change, no corresponding outbound transaction in the same window.

**Lesson for automated systems:** CASH_IN transactions on their own do not move funds out of the institution and so carry minimal standalone fraud risk. However, a CASH_IN should not be evaluated in isolation from what follows it — a large CASH_IN immediately followed by a CASH_OUT or TRANSFER of a similar amount is the signature of the mule pass-through pattern already described in Case 002, just from the deposit side. This case exists in the knowledge base specifically so the model/analyst distinguishes "CASH_IN as a standalone, low-risk event" from "CASH_IN as the first leg of a linked pass-through," rather than treating every CASH_IN as automatically benign.

---

## Case 008: Small DEBIT Transaction, Escalated Only Due to Account Context

**Pattern summary:** Transaction type: DEBIT, amount: small. A low-value DEBIT transaction that would normally be ignored, but was escalated because of surrounding account behavior rather than the transaction's own size.

An account with no prior DEBIT activity in its history initiated a DEBIT of approximately 4,000 shortly after two failed login attempts and a change to the account's registered contact details.

**Outcome:** The transaction amount itself was far below any value-based threshold and would not have triggered a rule flag on its own. It was escalated only because the account-monitoring layer flagged the preceding credential/contact-detail changes as a possible precursor to account takeover, and the DEBIT was treated as corroborating activity. Confirmed as early-stage account takeover; DEBIT reversed before further transactions occurred.

**Key indicators present:** Transaction amount alone is not suspicious, first-ever transaction of this type for the account, temporal proximity to account credential changes.

**Lesson for automated systems:** DEBIT transactions are typically small ATM-style withdrawals and are almost never fraudulent by amount alone, which means a purely transaction-level or amount-based model will consistently under-score them. Meaningful DEBIT fraud detection depends on account-context signals (login anomalies, profile changes, first-time transaction type) that live outside the transaction record itself. This is the same structural blind spot as Cases 002 and 004 — the fraud signal lives in context the per-transaction model cannot see — but manifests here at very low dollar amounts, which is easy to deprioritize if analysts only triage by transaction size.

---

## Case 009: Account Takeover via Staged Sub-Threshold Withdrawals (Evades Full-Drain Detection)

**Pattern summary:** Account takeover where the attacker deliberately avoids the exact signature that caught Case 001 — instead of one full-balance transfer, funds are removed via several smaller CASH_OUT transactions that each stay under the high-value review threshold, with a residual balance intentionally left behind.

An account with a stable balance of approximately 180,000 had its registered mobile number and password changed within a 20-minute window, following two failed login attempts from an unrecognized device — the same precursor pattern seen in Case 008. Over the following 90 minutes, four CASH_OUT transactions were initiated in sequence, each between 35,000 and 42,000, moving a cumulative 152,000 out of the account. No single transaction breached the 200,000 high-value threshold, and the account was left with a residual balance of roughly 28,000 rather than zero — avoiding both the "full balance drain" signature from Case 001 and the single-transaction high-value flag.

**Outcome:** No individual CASH_OUT triggered a rule-based flag on amount or full-drain grounds. The pattern was only caught because the account-context layer had already flagged the credential and contact-detail changes preceding the withdrawals (per the Case 008 pattern), which prompted a velocity review of the account's transactions in the following hours — surfacing four same-day CASH_OUTs from an account with no prior CASH_OUT history. Confirmed as account takeover; remaining balance frozen, three of four destination accounts identified as known mule accounts from prior cases.

**Key indicators present:** Credential/contact-detail change immediately preceding transaction activity, multiple same-type transactions in a short window each individually below review thresholds, deliberately non-zero residual balance, first-ever occurrence of this transaction type/velocity for the account.

**Lesson for automated systems:** This case demonstrates adversarial adaptation directly analogous to Case 003 — once a full-drain or single-large-transaction rule is known (or can be inferred through trial and error), an attacker with valid session access can restructure the same theft to resemble Case 004's structuring pattern instead. A rules layer that only checks "was the account fully drained" or "did any single transaction exceed the threshold" will miss this variant entirely. Effective detection requires combining account-context signals (credential/profile changes, new-device login) with velocity monitoring (transaction count and cumulative amount per account per rolling window) rather than relying on any single-transaction property — the same conclusion as Case 004, but arrived at from the account-takeover side rather than the laundering side.

---

## Summary Table of Case Patterns

| Case | Pattern | Model Score | Rule Flags | Correct Classification |
|---|---|---|---|---|
| 001 | Account takeover, full drain | High | Yes | Fraud |
| 002 | Mule pass-through, multi-hop | Low (per-transaction) | Partial | Fraud (only visible when linked) |
| 003 | High-value CASH_OUT, ambiguous destination balance | Low | Yes | Escalated — inconclusive, requires review |
| 004 | Structuring via sub-threshold transfers | Low (per-transaction) | No (per-transaction) | Fraud (only visible via velocity aggregation) |
| 005 | Large legitimate withdrawal | N/A | Yes | Legitimate |
| 006 | Routine PAYMENT, no fraud indicators | Low | No | Legitimate |
| 007 | CASH_IN deposit, standalone vs. linked context | Low | No | Legitimate (standalone) / context-dependent |
| 008 | Small DEBIT, escalated via account context only | N/A (amount too low to score meaningfully) | Yes (context-based) | Fraud (account takeover precursor) |
| 009 | Account takeover, staged sub-threshold withdrawals | Low (per-transaction) | No (per-transaction) | Fraud (only visible via account-context + velocity combined) |

**Cross-case observation:** In seven of the nine cases above, single-transaction fraud probability alone was an unreliable standalone signal — either under-scoring true fraud (Cases 002, 003, 004, 008, 009) or over-flagging legitimate activity (Case 005) at the rule level, or reflecting a low base rate rather than genuine model confidence (Cases 006, 007). This reinforces that layered detection — combining model scoring, rule-based checks, account-context signals, and velocity-based aggregation — consistently outperforms any single method in isolation. Case 009 in particular shows that a rules layer designed around one known fraud signature (full drain, per Case 001) can be deliberately evaded once an attacker adapts to it, reinforcing the same adversarial-adaptation lesson first raised in Case 003.
