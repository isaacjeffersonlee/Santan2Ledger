import chardet
import pandas as pd
import unicodedata
import re
import json
from santan2ledger.xact import Xact


class Parser:

    """Object used to parse data."""

    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            credentials = json.load(f)
        self.ledger_dir = credentials["ledger_dir"]
        if self.ledger_dir[-1] != "/":
            self.ledger_dir += "/"
        self.ledger_file_path = credentials["ledger_file"]
        self.accounts_file_path = credentials["accounts_file"]
        self.statements_dir = self.ledger_dir + "Statements/"

    def _get_encoding(self, file_path: str) -> str:
        """Return the encoding type of the input file.

        Uses the chardet library to read in and determine the encoding of the
        input file located at file_path.

        Parameters
        ----------
        file_path : str
            Path to file to determine encoding of.

        Returns
        -------
        str
            Encoding type. E.g "utf-8"
        """
        with open(file_path, "rb") as f:
            encoding = chardet.detect(f.read())["encoding"]

        return encoding

    def _file_contents_to_str(self, file_path: str) -> str:
        """Read file at file_path and return contents as a single string.

        Parameters
        ----------
        file_path : str
            File path of file to read in

        Returns
        -------
        str
            Contents of the file, encoded in utf-8
        """
        with open(file_path, "r", encoding=self._get_encoding(file_path)) as f:
            file_contents = f.read()
        # Remove chars such as \xa0 from non utf-8 encoding
        file_contents = unicodedata.normalize("NFKD", file_contents)
        return file_contents

    def _append_text_to_file(self, text: str, file_path: str) -> None:
        """Append text str to file at file_path.

        Parameters
        ----------
        text : str
            String to add to end of file
        file_path : str
            File path of the file to write to
        """
        with open(file_path, "a") as f:
            f.write(text + "\n")

    def txt_to_df(self, file_path: str, field_sep: str = ":") -> pd.DataFrame:
        """Convert .txt file found at file_path to Pandas DataFrame and return result.

        Text file with regular entries, separated by field_sep, E.g

            Date: 09/08/2022
            Description: CARD PAYMENT TO eBay
            Amount: -182.42
            Balance: 29.43

        gets parsed and converted to a Pandas DataFrame with column names given
        by the keys, and rows given by the values.

        Parameters
        ----------
        file_path : str
            Path to the txt file
        field_sep : str
            key field_sep value. E.g ':'

        Returns
        -------
        pd.DataFrame
            Pandas DataFrame with columns given by the keys
        """
        f_str = self._file_contents_to_str(file_path)
        str_list = [
            item.replace("\t", "")
            for item in f_str.split("\n")
            if item != "\t\t\t\t\t\t" and item
        ]
        str_list.remove("")  # Weird bug where a single '' doesn't get removed
        key_val_list = [s.split(field_sep) for s in str_list]
        keys = [key_val[0] for key_val in key_val_list]
        df_dict = {key: [] for key in pd.Series(keys).unique()}
        for key, val in key_val_list:
            df_dict[key].append(val)

        # Exclude unwanted key: vals, such as title: TITLE
        max_list_len = max([len(val) for val in df_dict.values()])
        keys_to_remove = []
        for key in df_dict:
            if len(df_dict[key]) != max_list_len:
                keys_to_remove.append(key)

        # Note: Can't do this in the above loop, because we get
        # a: "Dictionary changed during runtime" error
        for key in keys_to_remove:
            df_dict.pop(key)

        try:
            df = pd.DataFrame.from_dict(df_dict)
            # Split Amount and Balance cols into float values and str commodity separate cols
            amount_commodity_df = (
                df["Amount"].str.split(" ", expand=True).drop(0, axis=1)
            )
            df["Amount"] = amount_commodity_df[1].astype(float)
            df["Commodity"] = amount_commodity_df[2].astype(str)
            # Balance column
            balance_commodity_df = (
                df["Balance"].str.split(" ", expand=True).drop(0, axis=1)
            )
            df["Balance"] = balance_commodity_df[1].astype(float)
            # Convert Date column to Pandas datetime series
            df["Date"] = pd.to_datetime(df["Date"], format=" %d/%m/%Y")
        except KeyError:
            pass

        return df

    def get_account_list(self) -> list[str]:
        """Read accounts.ledger and return list of account names.

        Returns
        -------
        list[str]
            List of account strings, E.g
            ["Expenses:Food", "Assets:Cash", ...]
        """
        accounts_str = self._file_contents_to_str(self.accounts_file_path)
        return [
            s.replace("account ", "")
            for s in re.findall(pattern="account.*", string=accounts_str)
        ]

    def append_xacts_to_ledger_file(self, xacts: list[Xact]) -> None:
        """Format xacts as newline separated string and write to ledger file.

        Parameters
        ----------
        xacts : list[Xact]
            List of Xact objects to write to file.
        """
        xacts_str = "\n"
        xacts_str += "\n\n".join([xact.to_ledger_str() for xact in xacts])
        self._append_text_to_file(text=xacts_str, file_path=self.ledger_file_path)

    def append_accounts_to_file(self, accounts: list[str]) -> None:
        """Format accounts as a string and write to accounts.ledger.

        Parameters
        ----------
        accounts : list[str]
            List of account names, E.g
            ["Expenses:Food", "Assets:Cash", ...]
        """
        if accounts:
            accounts_str = "account "
            accounts_str += "\naccount ".join(accounts)
            self._append_text_to_file(text=accounts_str, file_path=self.accounts_file_path)


if __name__ == "__main__":
    parser = Parser()
    # txt_file = "Statements09012964141909.txt"
    # print(txt_to_df(file_path=txt_file))
    # print(parser._append_text_to_file(text="Hello darkness my old friend...",
    #                                   file_path="/home/isaac/Documents/Track/Ledger/accounts.ledger"))

    # test_accounts = parser.get_account_list()
    # print(test_accounts)
    # parser.append_accounts_to_file(accounts=test_accounts)

    # test_xact_1 = Xact(
    #     source_account="Assets:Santander:Spending",
    #     target_account="Expenses:Spending:Food",
    #     amount=-420.00,
    #     description="CARD PAYMENT TO TFL TRAVEL CH,1.65 GBP, RATE 1.00/GBP ON 01-08-2022",
    #     date_str="04/08/2022",
    #     commodity="GBP",
    # )
    # test_xact_2 = Xact(
    #     source_account="Assets:Santander:Main",
    #     target_account="Expenses:TEST",
    #     amount=10.00,
    #     description="CARD PAYMENT TO TFL TRAVEL CH,1.65 GBP, RATE 1.00/GBP ON 01-08-2022",
    #     date_str="05/07/2022",
    #     commodity="GBP",
    # )

    # parser.append_xacts_to_ledger_file([test_xact_1, test_xact_2])
