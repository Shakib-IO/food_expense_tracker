
def compute_balance_message(totals: dict) -> str:
    """
    Compute who owes whom based on totals for the current view.
    """
    shakib_total = float(totals.get("Shakib", 0.0))
    junit_total = float(totals.get("Junit", 0.0))

    total_spent = shakib_total + junit_total
    if total_spent == 0:
        return "No expenses recorded for this period."

    equal_share = total_spent / 2.0
    diff = shakib_total - equal_share

    if abs(diff) < 1e-6:
        return "Both Shakib and Junit have spent equally. No one owes anything."

    if diff > 0:
        # Shakib paid more than his share
        return f"Junit owes Shakib {diff:.2f}$."
    else:
        # Junit paid more
        return f"Shakib owes Junit {(-diff):.2f}$."