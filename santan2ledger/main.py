import argparse
import os
from santan2ledger.parser import Parser
from santan2ledger.selector import Selector
from santan2ledger.xact import Xact

MODULE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../santan2ledger")
)


def main(statement_file_name: str) -> None:
    # Define objects used for printing, selecting and parsing
    selector = Selector(
        data_dir=MODULE_PATH + "/data"
    )  # Initiate account selector object
    parser = Parser()
    # Read in statements from .txt file
    statement_file_path = parser.statements_dir + statement_file_name
    statement_df = parser.txt_to_df(file_path=statement_file_path)
    # Get list of already defined accounts
    account_list = parser.get_account_list()
    print("Select source account: ")
    source_account = selector.autocomplete_prompt(items=account_list)
    default_commodity = selector.autocomplete_prompt(
        items=["GBP", "CHF"], message="Default commodity: "
    )

    idx = 0
    while True:
        row = statement_df.iloc[idx]
        xact = Xact(
            source_account=source_account,
            amount=row["Amount"],
            description=row["Description"],
            date_str=str(row["Date"].date()),
            commodity=row["Commodity"] if row["Commodity"] else default_commodity,
        )
        prompt_input = selector.get_target_account(
            xact=xact,
            prev_account_list=account_list,
            progress=f"Account No. {idx + 1} / {statement_df.shape[0]}",
        )
        if prompt_input == "k" or prompt_input == "p":
            idx -= 2  # Go to previous transaction
        else:
            xact.target_account = prompt_input

        selector.append_xact(xact)
        idx += 1
        if idx == statement_df.shape[0]:
            print("Finished!")
            break  # TODO: Add keybinding to quit

    selector.update_prev_xact_file()

    parser.append_xacts_to_ledger_file(selector.new_xacts)
    parser.append_accounts_to_file(list(selector.new_accounts))


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
