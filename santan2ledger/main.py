from rich.console import Console
import argparse
from santan2ledger.parser import Parser
from santan2ledger.selector import Selector
from santan2ledger.xact import Xact


def main(statement_file_name: str) -> None:
    console = Console()  # Initiate rich console for pretty printing
    selector = Selector()  # Initiate account selector object
    parser = Parser()
    statement_file_path = parser.statements_dir + statement_file_name
    statement_df = parser.txt_to_df(file_path=statement_file_path)
    source_account = selector.fzf_select_account()
    for row in statement_df.iterrows():
        xact = Xact(
            source_account=source_account,
            amount=row[1]["Amount"],
            description=row[1]["Description"],
            date_str=str(row[1]["Date"].date()),
            commodity=row[1]["Commodity"],
            target_account=selector.get_target_account(),
        )
        selector.append_xact(xact)

    selector.update_prev_xact_file()

    parser.append_xacts_to_ledger_file(selector.new_xacts)
    parser.append_accounts_to_file(selector.new_accounts)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()  # For command line args

    # parser.add_argument(
    #     "-f",
    #     "--input-file",
    #     dest="statements_file_name",
    #     help="Santander exported txt file to parse.",
    # )
    # args = parser.parse_args()

    # main(args.statements_file_name)

    statement_file_name = "Statements09012964141909.txt"
    main(statement_file_name)
