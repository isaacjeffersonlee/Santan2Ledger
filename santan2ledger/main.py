from rich.console import Console
import argparse
import json
import santan2ledger.parser as parser
from santan2ledger.selector import Selector
from santan2ledger.xact import Xact

with open("../config.json", "r") as f:
    credentials = json.load(f)

LEDGER_DIR = credentials["ledger_dir"]


def main(txt_file: str):
    console = Console()  # Initiate rich console for pretty printing
    selector = Selector()  # Initiate account selector object
    df = parser.txt_to_df(file_path=txt_file)
    console.print(df)
    console.print(LEDGER_DIR)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()  # For command line args

    # parser.add_argument(
    #     "-f",
    #     "--input-file",
    #     dest="txt_file",
    #     help="Santander exported txt file to parse.",
    # )
    # args = parser.parse_args()

    # main(args.txt_file)

    txt_file = "Statements09012964141909.txt"
    main(txt_file)
