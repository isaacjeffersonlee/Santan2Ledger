from typing import Union
from pyfzf.pyfzf import FzfPrompt
from fuzzywuzzy import fuzz  # fuzz.ratio(s1, s2)
from xact import Xact
import pandas as pd
import os


class Selector:

    """Account selector object."""

    def __init__(self, data_dir: str = "data"):
        """Initialize selector attributes and create previous transaction df.

        Checks if {data_dir}/prev_xact.pkl exists, and if not create it

        Parameters
        ----------
        data_dir : str
            The directory to store the .pkl file
            E.g for "data" => pickle file is located at "data/prev_xact.pkl"
        """
        self._data_dir = data_dir
        self._prev_xact_df_path = data_dir + "/prev_xact.pkl"
        if not os.path.exists(self._prev_xact_df_path):
            pd.DataFrame(
                columns=[
                    "date_str",
                    "description",
                    "from_account",
                    "to_account",
                    "amount",
                    "commodity",
                ]
            ).to_pickle(self._prev_xact_df_path)
        self.prev_xact_df = pd.read_pickle(self._prev_xact_df_path)

    def fzf_select(self, items: list[str]) -> Union[str, None]:
        """Fuzzy select an item from items list using fzf and return result.

        Returns None if no item is selected, i.e fzf prompt is escaped.

        Parameters
        ----------
        items : list[str]
            List of strings to select from

        Returns
        -------
        str
            Selected item
        """
        fzf = FzfPrompt()
        selected = fzf.prompt(
            choices=items,
            fzf_options="-i --border=sharp --margin=20%",
        )
        return selected[0] if selected else None

    def get_best_desc_match_idx(
        self, desc_to_match: str, min_ratio: int = 10
    ) -> Union[int, None]:
        """Get index of row with best match.

        Get the index of the row from self.prev_xact_df with the most similar
        description to desc_to_match.

        More specifically, calculate fuzz.ratio(account_to_match, s) for all s
        in self.prev_xact_df["description"] and find idx of row with max match

        If self.prev_xact_df is empty, or there isn't a match with fuzz.ratio
        above min_ratio, return None

        Parameters
        ----------
        desc_to_match : str
            Transaction description string to find matches with from the df.

        Returns
        -------
        Union[int, None]
            Index of row with highest scoring match, if no sufficient matches
            found, or df is empty, return None
        """
        # TODO: Write function body
        pass

    def append_xact(self, xact: Xact) -> None:
        """Append xact to self.prev_xact_df.

        Parameters
        ----------
        xact : Xact
            Transaction object, whose attributes are used as values in the dict
            which gets appended to self.prev_xact_df
        """
        xact_dict = {
            "from_account": [xact.from_account],
            "to_account": [xact.to_account],
            "amount": [xact.amount],
            "description": [xact.description],
            "date_str": [xact.date_str],
            "commodity": [xact.commodity],
        }
        self.prev_xact_df = pd.concat([self.prev_xact_df, pd.DataFrame(xact_dict)])

    def update_prev_xact_file(self) -> None:
        """Export current self.prev_xact_df to pickle file."""
        self.prev_xact_df.to_pickle(self._prev_xact_df_path)


if __name__ == "__main__":

    selector = Selector()

    example_accounts = [
        "Expenses:Spending:Food",
        "Expenses:Spending:Sesh",
        "Expenses:Groceries",
    ]

    example_xact = Xact(
        from_account="Assets:Santander:Spending",
        amount=-420.00,
        description="CARD PAYMENT TO TFL TRAVEL CH,1.65 GBP, RATE 1.00/GBP ON 01-08-2022",
        date_str="04/08/2022",
        commodity="GBP",
    )

    example_xact.to_account = selector.fzf_select(example_accounts)
    print(example_xact.to_ledger_str())
    # print(selector.prev_xact_df)
    # print(selector.append_xact(xact=example_xact))
    # print(selector.prev_xact_df)
