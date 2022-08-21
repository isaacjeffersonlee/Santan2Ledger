import chardet
import pandas as pd
import unicodedata
import re


def get_encoding(file_path: str) -> str:
    """
    Return the encoding type of the input file.

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


def file_contents_to_str(file_path: str) -> str:
    """
    Read file at file_path and return contents as a single string.

    Parameters
    ----------
    file_path : str
        File path of file to read in

    Returns
    -------
    str
        Contents of the file, encoded in utf-8
    """
    with open(file_path, "r", encoding=get_encoding(file_path)) as f:
        file_contents = f.read()
    # Remove chars such as \xa0 from non utf-8 encoding
    file_contents = unicodedata.normalize("NFKD", file_contents)
    return file_contents


def txt_to_df(file_path: str, field_sep: str = ":") -> pd.DataFrame:
    """
    Convert .txt file found at file_path to Pandas DataFrame and return result.

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
    f_str = file_contents_to_str(file_path)
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
        amount_commodity_df = df["Amount"].str.split(" ", expand=True).drop(0, axis=1)
        df["Amount"] = amount_commodity_df[1].astype(float)
        df["Commodity"] = amount_commodity_df[2].astype(str)
        # Balance column
        balance_commodity_df = df["Balance"].str.split(" ", expand=True).drop(0, axis=1)
        df["Balance"] = balance_commodity_df[1].astype(float)
        # Convert Date column to Pandas datetime series
        df["Date"] = pd.to_datetime(df["Date"])
    except KeyError:
        pass

    return df


def get_account_list(accounts_file: str) -> list[str]:
    """Read accounts.ledger and return list of account names.

    Parameters
    ----------
    accounts_file : str
        Path to accounts.ledger containing account names

    Returns
    -------
    list[str]
        List of account strings, E.g
        ["Expenses:Food", "Assets:Cash", ...]
    """
    # TODO: Write function body
    pass


def clean_text(text: str, extra_to_remove: list[str]) -> str:
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
    text = re.sub(r"gbp", r"", text)
    return text


if __name__ == "__main__":
    txt_file = "Statements09012964141909.txt"
    f = file_contents_to_str(txt_file)
    print(txt_to_df(file_path=txt_file))
