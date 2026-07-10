def check_rules(transaction: dict) -> list[str]:
    flags = []

    amount = transaction["amount"]
    old_orig = transaction["oldbalanceOrg"]
    new_orig = transaction["newbalanceOrig"]
    old_dest = transaction["oldbalanceDest"]
    new_dest = transaction["newbalanceDest"]
    txn_type = transaction["type"]

    # Account emptying — classic fraud signature
    if old_orig > 0 and new_orig == 0 and amount > 0:
        flags.append("Origin account fully emptied in this transaction")

    # Large transfer relative to balance
    if old_orig > 0 and amount >= old_orig * 0.9:
        flags.append("Transaction amount is 90%+ of sender's entire balance")

    # Destination balance didn't move as expected (money vanishing)
    if txn_type in ["CASH_OUT", "TRANSFER"] and old_dest == 0 and new_dest == 0 and amount > 0:
        flags.append("Destination balance shows no change despite transfer — possible mule account")

    # High-value CASH_OUT or TRANSFER
    if txn_type in ["CASH_OUT", "TRANSFER"] and amount > 200000:
        flags.append(f"High-value {txn_type} transaction (>200,000)")

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

    return flags
