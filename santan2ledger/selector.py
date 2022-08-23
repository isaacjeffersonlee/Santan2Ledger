import re
from fuzzywuzzy import fuzz  # fuzz.ratio(s1, s2)
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.application.current import get_app
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame, TextArea
from xact import Xact
import pandas as pd
import os

# TODO: Fix date string parsing being the wrong way around
# TODO: Fix duplication of accounts from accounts.ledger when adding new accounts
# TODO: Add pickup where left off according to last date recorded
# TODO: Add weighting for matches with higher freq
# TODO: Polish UI


# https://ansi.gabebanks.net/
def red(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[31;1m"
    return escape_code + text + "\033[0m"


def green(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[32;1m"
    return escape_code + text + "\033[0m"


def yellow(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[33;1m"
    return escape_code + text + "\033[0m"


def blue(text: str) -> str:
    """Color the text using ansi escapes."""
    escape_code = "\033[34;1m"
    return escape_code + text + "\033[0m"


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
                    "source_account",
                    "target_account",
                    "amount",
                    "commodity",
                ]
            ).to_pickle(self._prev_xact_df_path)
        self.prev_xact_df = pd.read_pickle(self._prev_xact_df_path)
        self.new_xacts = []
        self.new_accounts = set()

    def autocomplete_prompt(
        self,
        items: list[str],
        default: str = "",
        message: str = "> ",
        toolbar_str: str = "",
    ) -> str:
        """Prompt for input with fuzzy autocompletion and vi-mode.

        Parameters
        ----------
        items : list[str]
            List of strings to use for fuzzy completion suggestions
        default : str
            Default value to suggest. If <Enter> is hit, i.e
            an empty string is entered, then the default value
            will be selected.
        message : str
            Prompt message to display on the RHS of the prompt line
        toolbar_str : str
            String to display in the bottom toolbar

        Returns
        -------
        str
            User entered input
        """

        bindings = KeyBindings()
        items_completer = FuzzyWordCompleter(items)

        def bottom_toolbar():
            """Display the current input mode."""
            if get_app().editing_mode == EditingMode.VI:
                return f"{toolbar_str} [F4] Vi "
            else:
                return f"{toolbar_str} [F4] Emacs "

        @bindings.add("f4")
        def _(event):
            """Toggle between Emacs and Vi mode."""
            if event.app.editing_mode == EditingMode.VI:
                event.app.editing_mode = EditingMode.EMACS
            else:
                event.app.editing_mode = EditingMode.VI

        @bindings.add("c-y")
        def _(event):
            """Insert default value."""
            event.app.current_buffer.insert_text(default)

        selected = prompt(
            message=message,
            completer=items_completer,
            complete_while_typing=True,
            # default=default,
            key_bindings=bindings,
            bottom_toolbar=bottom_toolbar,
            vi_mode=True,
        )

        if not selected:
            return default  # We can just hit <Enter> to select default
        else:
            return selected

    def _clean_text(self, text: str, extra_to_remove: list[str] = []) -> str:
        """Simplify the text and return cleaned string.

        Remove all non-alpha chars also all strings
        from extra_to_remove and lowercase

        Parameters
        ----------
        text : str
            Text to clean
        extra_to_remove : list[str]
            List of extra words to remove from text

        Returns
        -------
        str
            Cleaned string
        """
        text = re.sub(r"[^a-zA-Z\s]", "", text.lower())
        text = re.sub(r"(gbp|card|payment|samsung|on)", r"", text)
        return text

    def _get_matching_account_name(
        self, desc_to_match: str, min_ratio: int = 10
    ) -> str:
        """Get the account name of the closest matching prev transaction.

        Calculates fuzz.ratio(account_to_match, s) for all s
        in self.prev_xact_df["description"] and return account name from
        row with max ratio

        If self.prev_xact_df is empty, or there isn't a match with fuzz.ratio
        above min_ratio, return '', empty string

        Parameters
        ----------
        desc_to_match : str
            Transaction description string to find matches with from the df

        Returns
        -------
        str
            Name of matched account, E.g
                'Expenses:Spending:Food'
            If no sufficient matches found, or df is empty,
            return empty string, ''
        """
        if self.prev_xact_df.empty:
            return ""
        else:
            df = self.prev_xact_df.copy()
            df["fuzz_ratio"] = df["description"].apply(
                lambda desc: fuzz.ratio(
                    self._clean_text(desc),
                    self._clean_text(desc_to_match),
                )
            )
            df.sort_values(by=["fuzz_ratio"], ascending=False, inplace=True)
            max_fuzz_ratio = df["fuzz_ratio"].head(1).item()
            # TODO: Add weighting for more frequency
            if max_fuzz_ratio < min_ratio:
                return ""
            else:
                return df["target_account"].head(1).item()

    def append_xact(self, xact: Xact) -> None:
        """Append xact to self.prev_xact_df and self.new_xacts.

        Parameters
        ----------
        xact : Xact
            Transaction object, whose attributes are used as values in the dict
            which gets appended to self.prev_xact_df and self.new_xacts
        """
        xact_dict = {
            "source_account": [xact.source_account],
            "target_account": [xact.target_account],
            "amount": [xact.amount],
            "description": [xact.description],
            "date_str": [xact.date_str],
            "commodity": [xact.commodity],
        }
        self.prev_xact_df = pd.concat([self.prev_xact_df, pd.DataFrame(xact_dict)])
        self.new_xacts.append(xact)

    def update_prev_xact_file(self) -> None:
        """Export current self.prev_xact_df to pickle file."""
        self.prev_xact_df.to_pickle(self._prev_xact_df_path)

    def get_target_account(
        self, xact: Xact, prev_account_list: list[str], progress: str
    ) -> str:
        """
        Prompt user for target account.

        Suggest smart suggestions using xact description matching.
        Also once target account is selected, updates new_accounts set
        with target_account.

        Parameters
        ----------
        xact : Xact
            Transaction to get target account of
        prev_account_list : list[str]
            List of accounts to use for fuzzy autocompletion
        progress : str
            String passed from main loop, giving indication of
            how many accounts have been processed

        Returns
        -------
        str
            Target account string. E.g
                "Expenses:Spending:Travel"
        """
        account_list = prev_account_list + list(self.new_accounts)
        desc_to_match = xact.description
        match = self._get_matching_account_name(desc_to_match)
        xact.target_account = "[Unknown]"
        print_container(
            Frame(
                TextArea(text=xact.to_ledger_str()),
                title=progress,
            )
        )
        if match:
            print("Suggested match: " + green(match))
        else:
            print(red("No similar transactions found!"))

        target_account = self.autocomplete_prompt(
            items=account_list,
            default=match,
            toolbar_str=progress + " Hit <Enter> to accept suggested match ",
            message="➜ ",
        )
        # Update new accounts set
        self.new_accounts = self.new_accounts.union({target_account})

        print(f"Input: {target_account}")
        return target_account


if __name__ == "__main__":

    selector = Selector()

    example_accounts = [
        "Expenses:Spending:Food",
        "Expenses:Spending:Sesh",
        "Expenses:Groceries",
    ]

    example_xact = Xact(
        source_account="Assets:Santander:Spending",
        amount=-420.00,
        description="CARD PAYMENT TO TFL TRAVEL CH,1.65 GBP, RATE 1.00/GBP ON 01-08-2022",
        date_str="04/08/2022",
        commodity="GBP",
    )
    print("Default value:", example_accounts[0])
    txt = selector.autocomplete_prompt(
        items=example_accounts, default=example_accounts[0]
    )
    print(txt, type(txt), bool(txt))
    # example_xact.target_account = selector.fzf_select(example_accounts)
    # print(example_xact.to_ledger_str())
    # print(selector.prev_xact_df)
    # print(selector.append_xact(xact=example_xact))
    # print(selector.prev_xact_df)
    # print(selector.fzf_select(items=["item_2", "item_1", "item 3"]))
