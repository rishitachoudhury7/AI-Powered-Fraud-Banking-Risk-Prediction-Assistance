def check_rules(transaction: dict) -> list[str]:
    flags = []

    amount = transaction["amount"]
    old_orig = transaction["oldbalanceOrg"]
    new_orig = transaction["newbalanceOrig"]
    old_dest = transaction["oldbalanceDest"]
    new_dest = transaction["newbalanceDest"]
    txn_type = transaction["type"]

    # Only flag full drain if the balance was meaningfully large (not near-zero accounts)
    if old_orig > 1000 and new_orig == 0 and amount > 0:
        flags.append("Origin account fully emptied in this transaction")

    # Raise the relative threshold — 90% is too common; require near-total drain AND meaningful size
    if old_orig > 1000 and amount >= old_orig * 0.98:
        flags.append("Transaction amount is 98%+ of sender's entire balance")

    # Destination balance didn't move as expected (money vanishing)
    if txn_type in ["CASH_OUT", "TRANSFER"] and old_dest == 0 and new_dest == 0 and amount > 0:
        flags.append("Destination balance shows no change despite transfer — possible mule account")

    # Raise the high-value threshold significantly, or better: make it a soft signal, not a hard flag alone
    if txn_type in ["CASH_OUT", "TRANSFER"] and amount > 500000:
        flags.append(f"High-value {txn_type} transaction (>500,000)")

    return flags

def check_chain_rules(transactions: list[dict]) -> list[str]:
    """Detect patterns that only emerge across a sequence of linked transactions."""
    flags = []

    if len(transactions) < 2:
        return flags

    total_amount = sum(t["amount"] for t in transactions)

    # Full pass-through: money enters and leaves an account in the same chain
    for i in range(len(transactions) - 1):
        current = transactions[i]
        nxt = transactions[i + 1]
        if (current["type"] == "TRANSFER" and nxt["type"] == "CASH_OUT"
                and abs(current["amount"] - nxt["amount"]) < 1.0):
            flags.append(f"Hop {i+1}→{i+2}: TRANSFER immediately followed by CASH_OUT of nearly identical amount — classic mule pass-through pattern")

    # Structuring: many similar-sized transactions
    if len(transactions) >= 4:
        amounts = [t["amount"] for t in transactions]
        avg = sum(amounts) / len(amounts)
        similar = sum(1 for a in amounts if abs(a - avg) / avg < 0.15) if avg > 0 else 0
        if similar >= 4:
            flags.append(f"{similar} transactions of similar size detected in this chain — possible structuring pattern")

    # Rapid full drain across the chain
    if transactions[0]["oldbalanceOrg"] > 0 and transactions[-1]["newbalanceDest"] >= 0:
        if transactions[0]["oldbalanceOrg"] - transactions[0].get("newbalanceOrig", 0) >= transactions[0]["oldbalanceOrg"] * 0.9:
            flags.append("Chain originates from a near-total balance drain in the first hop")

    flags.extend(check_cycle(transactions))
    flags.extend(check_currency_mismatch(transactions))
    
    return flags


from datetime import datetime

def _parse_timestamp(ts: str):
    if not ts:
        return None
    for fmt in ("%Y/%m/%d %H:%M", "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except (ValueError, TypeError):
            continue
    return None

def check_cycle(transactions: list[dict]) -> list[str]:
    """Detect A -> B -> A round-trip cycles using account identity and timing."""
    flags = []

    accounts_seen = {}
    for i, txn in enumerate(transactions):
        orig = txn.get("nameOrig")
        dest = txn.get("nameDest")
        if not orig or not dest:
            continue

        if dest in accounts_seen:
            earlier_idx, earlier_txn = accounts_seen[dest]
            if earlier_txn.get("nameDest") == orig:
                amt_diff = abs(txn["amount"] - earlier_txn["amount"])
                same_amount = amt_diff < max(1.0, earlier_txn["amount"] * 0.01)

                t1 = _parse_timestamp(earlier_txn.get("timestamp"))
                t2 = _parse_timestamp(txn.get("timestamp"))
                gap_note = ""
                if t1 and t2:
                    gap_days = (t2 - t1).days
                    gap_note = f" ({gap_days} day(s) apart)"

                amount_note = "identical amount" if same_amount else "differing amount (possible fee/conversion skim)"
                flags.append(
                    f"Cycle detected: Account {orig} → {dest} (hop {earlier_idx+1}) then {dest} → {orig} (hop {i+1}), {amount_note}{gap_note}"
                )

        accounts_seen[orig] = (i, txn)

    return flags

def check_currency_mismatch(transactions: list[dict]) -> list[str]:
    """Flag transactions where paid and received currencies differ across a chain."""
    flags = []
    for i, txn in enumerate(transactions):
        pay_cur = txn.get("payment_currency")
        recv_cur = txn.get("receiving_currency")
        if pay_cur and recv_cur and pay_cur != recv_cur:
            flags.append(f"Hop {i+1}: currency conversion detected ({pay_cur} → {recv_cur}) — common in cross-border layering")
    return flags
