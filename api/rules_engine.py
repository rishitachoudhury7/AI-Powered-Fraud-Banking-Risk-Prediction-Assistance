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
