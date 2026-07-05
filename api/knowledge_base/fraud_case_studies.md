Historical Fraud Case Reference Log

Internal Reference — Illustrative Case Studies for Transaction Investigation

Note: The cases below are composite, illustrative scenarios constructed for training and reference purposes. They do not represent real customer data or real institutions, but reflect commonly observed fraud patterns in retail banking transaction monitoring.


Case 001: Full Account Drain via Unauthorized Transfer

Pattern summary: Account takeover leading to complete balance withdrawal.

A customer's account, with a historical average balance of approximately 12,000, received no unusual activity for several months. Within a single 24-hour window, a TRANSFER of the full account balance (98,400) was initiated to a previously unseen recipient account, reducing the origin balance to zero. The receiving account had been opened only three days prior and had no transaction history before this inbound transfer.

Outcome: Flagged by rule-based monitoring (full balance drain + new destination account). Escalated to human analyst within 2 hours of the transaction. Confirmed as account takeover following customer contact — the customer had not initiated the transfer. Funds were partially recovered by freezing the destination account before onward movement.

Key indicators present: Full origin balance drain, destination account newly created, transaction inconsistent with account's historical behavior, no prior relationship between origin and destination accounts.


Case 002: Mule Account Pass-Through (TRANSFER → CASH_OUT Chain)

Pattern summary: Multi-hop laundering via a linked TRANSFER followed by immediate CASH_OUT.

A dormant account with a near-zero balance received an inbound TRANSFER of 340,000 from a compromised account. Within the same processing window (step), the recipient account initiated a CASH_OUT of the full received amount, leaving the account at zero balance again. Individually, neither transaction scored highly on a single-transaction fraud model: the TRANSFER appeared as a large but plausible transfer, and the CASH_OUT appeared as a routine withdrawal of an existing balance.

Outcome: The pattern was only identified when a human analyst reviewed both transactions together as a linked pair, noting the recipient account had no other transaction history and returned to zero balance immediately after the CASH_OUT. Retroactively classified as mule account activity.

Key indicators present: Recipient account balance near-zero both before and after the transaction pair, minimal time gap between inbound and outbound transaction, transaction amounts nearly identical (little to no funds retained).

Lesson for automated systems: Transaction-level models without access to linked-transaction or account-history context are structurally unable to detect this pattern reliably. This category of fraud requires either account-level feature engineering (e.g., tracking balance-in vs balance-out within short windows) or a rules layer specifically designed to flag rapid full pass-through activity.


Case 003: Large CASH_OUT Misclassified Due to Ambiguous Destination Balance

Pattern summary: A high-value CASH_OUT where the destination account already held a substantial pre-existing balance, causing a fraud model to under-score a transaction that rule-based monitoring flagged as high-risk.

An origin account with a balance of approximately 1,270,000 was fully drained via a CASH_OUT transaction. The destination account, however, already held a balance of over 1,000,000 prior to this transaction — meaning the post-transaction destination balance did not cleanly reflect a simple pass-through of the transferred funds. The transaction-level fraud model scored this transaction at a relatively low probability, likely because engineered features comparing expected versus actual balance changes (analogous to "difference from expected balance" features) suggested the transaction was less anomalous than a typical mule pattern, where destination balances usually sit near zero both before and after.

Outcome: Despite the low model score, rule-based monitoring flagged the transaction for three reasons: the origin account was fully emptied, the transaction represented over 90% of the sender's balance, and the transaction amount exceeded standard high-value thresholds. The case was escalated to a human analyst, who noted the discrepancy between the model's low score and the strength of the rule-based signals as itself worth investigating — the destination account's pre-existing balance made it plausible this was either a legitimate business account or a more sophisticated mule account that intentionally maintains a buffer balance to avoid near-zero-balance detection heuristics.

Key indicators present: Full origin balance drain, high-value threshold breach, model probability significantly lower than rule-based risk assessment would suggest — a divergence pattern that should itself be treated as noteworthy.

Lesson for automated systems: When SHAP-derived feature attributions and rule-based flags disagree with the model's raw probability output, this divergence should be explicitly surfaced to the reviewing analyst rather than resolved silently in favor of either signal. Some mule account operators may deliberately maintain non-zero destination balances specifically to evade detection heuristics premised on near-zero balances — a form of adversarial adaptation that transaction-level models trained on historical data may not yet reflect.


Case 004: Structuring via Multiple Sub-Threshold Transfers

Pattern summary: A single intended large transfer broken into several smaller transactions to avoid triggering high-value monitoring thresholds.

Over a six-hour window, an account initiated seven separate TRANSFER transactions, each ranging between 28,000 and 31,000 — each individually below the institution's 200,000 high-value review threshold used in single-transaction rule checks. Cumulatively, the seven transactions totaled approximately 205,000, exceeding the threshold that would have triggered review had it occurred as a single transaction.

Outcome: No individual transaction in the sequence triggered rule-based or model-based flags in isolation. The pattern was only identified during a periodic velocity review that aggregated transaction counts and cumulative amounts per account over rolling time windows.

Key indicators present: Multiple transactions just below a known reporting or review threshold, repeated similar amounts, short time window, same origin account across all transactions.

Lesson for automated systems: Structuring cannot be detected through single-transaction scoring alone, regardless of model sophistication. Effective detection requires velocity-based monitoring — tracking transaction frequency and cumulative amount per account within rolling time windows — as a complement to per-transaction fraud scoring.


Case 005: Legitimate Large Withdrawal Correctly Approved

Pattern summary: A large transaction with surface-level similarity to fraud patterns, correctly identified as legitimate after review.

A long-standing customer account with a stable high balance initiated a CASH_OUT of approximately 450,000, reducing the account to a low but non-zero balance. The transaction amount exceeded the standard high-value review threshold, triggering a rule-based flag.

Outcome: Upon review, the transaction was associated with a documented, pre-notified large purchase (property transaction), consistent with the customer's historical account activity and prior communication with the bank. No further action was taken; transaction was approved.

Key indicators present: High-value threshold breach (rule-flagged) but consistent with account's historical pattern, customer-initiated with prior notice, non-zero remaining balance.

Lesson for automated systems: Not every rule-flagged transaction is fraudulent. Rule-based flags are designed to maximize sensitivity (catching potential fraud) at the cost of some false positives; human review remains necessary to distinguish true fraud from legitimate high-value activity, particularly for established accounts with consistent historical behavior.


Summary Table of Case Patterns

CasePatternModel ScoreRule FlagsCorrect Classification001Account takeover, full drainHighYesFraud002Mule pass-through, multi-hopLow (per-transaction)PartialFraud (only visible when linked)003High-value CASH_OUT, ambiguous destination balanceLowYesEscalated — inconclusive, requires review004Structuring via sub-threshold transfersLow (per-transaction)No (per-transaction)Fraud (only visible via velocity aggregation)005Large legitimate withdrawalN/AYesLegitimate

Cross-case observation: In four of the five cases above, single-transaction fraud probability alone was an unreliable standalone signal — either under-scoring true fraud (Cases 002, 003, 004) or over-flagging legitimate activity (Case 005) at the rule level. This reinforces that layered detection — combining model scoring, rule-based checks, and in some cases account-level or velocity-based context — consistently outperforms any single method in isolation.
