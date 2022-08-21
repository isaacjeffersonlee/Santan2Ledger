class Xact:

    """Transaction object."""

    def __init__(
        self,
        from_account: str,
        amount: float,
        description: str,
        date_str: str,
        commodity: str,
        to_account: str = ""
    ):
        """Initialize the transaction attributes.

        Parameters
        ----------
        from_account : str
            The account the money comes from, e.g a "Assets:Bank:Santander:Spending "
        amount : float
            The transaction amount
        date_str : str
            The date the transaction occured
        commodity : str
            The commodotity of the transaction, e.g 'GBP'
        """

        self.from_account = from_account
        self.to_account = to_account
        self.amount = amount
        self.description = description
        self.date_str = date_str
        self.commodity = commodity

    def to_ledger_str(self) -> str:
        """Format transaction attributes as a ledger transation and return str.

        Returns
        -------
        str
            E.g 05/08/2022 * TFL TRAVEL CH (VIA SAMSUNG PAY)
                  Expenses:Spending:Groceries                   20.79 GBP
                  Assets:Santander:Spending
        """
        return (
            f"{self.date_str} * {self.description}\n"
            + f"  {self.to_account}          {-1 * self.amount} {self.commodity}\n"
            + f"  {self.from_account}"
        )

    def _get_destination_account(self) -> None:
        pass


if __name__ == "__main__":
    xact = Xact(
        from_account="Assets:Santander:Spending",
        amount=-20.79,
        description="TFL TRAVEL CH (VIA SAMSUNG PAY)",
        date_str="05/08/2022",
        commodity="GBP",
    )
    xact.to_account = "Expenses:Spending:Groceries"
    print(xact.to_ledger_str())
