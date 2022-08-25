import argparse
import pandas as pd
import os
from santan2ledger.parser import Parser
from santan2ledger.selector import Selector
from santan2ledger.xact import Xact
import santan2ledger.colors as colors

# TODO: Add matching also according to amounts
# TODO: Add title page
# TODO: Polish UI
# TODO: Package for installation and portability
# TODO: Add README.md


MODULE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../santan2ledger")
)
ROOT_PATH = os.path.dirname(MODULE_PATH)


def main(statement_file_name: str, account_key: str, date_after: str) -> None:
    try:
        # Define objects used for printing, selecting and parsing
        selector = Selector(
            data_dir=MODULE_PATH + "/data"
        )  # Initiate account selector object
        parser = Parser(account_key=account_key, config_path=ROOT_PATH + "/config.json")
        # Backup ledger and accounts file
        parser.make_backup()
        # Get list of previously defined accounts from accounts.ledger
        prev_accounts = parser.get_account_list()
        source_account = selector.autocomplete_prompt(
            items=prev_accounts, message="Source Account: "
        )
        selector.prev_xact_df = selector.prev_xact_df.loc[
            selector.prev_xact_df["source_account"] == source_account
        ]
        default_commodity = selector.autocomplete_prompt(
            items=["GBP", "CHF"], message="Default commodity: "
        )
        # Read in statements from .txt file
        statement_file_path = parser.statements_dir + statement_file_name
        # Also reverse the order, so that earliest transactions appear first
        statement_df = parser.txt_to_df(file_path=statement_file_path).iloc[::-1]
        if date_after:
            statement_df = statement_df.loc[
                statement_df["Date"]
                > pd.to_datetime(date_after.replace("-", "/"), format="%d/%m/%Y")
            ]
        elif not selector.prev_xact_df.empty:
            last_recorded_date = (  # TODO: Use last row matching instead of date matching
                pd.to_datetime(
                    selector.prev_xact_df.loc[
                        selector.prev_xact_df["source_account"] == source_account
                    ]["date_str"],
                    format="%Y/%m/%d",
                )
                .tail(1)
                .item()
            )
            print(f"Last recorded date: {colors.magenta(str(last_recorded_date))}")
            # Only consider transactions entered after last_recorded_date
            statement_df = statement_df.loc[statement_df["Date"] > last_recorded_date]

        if statement_df.empty:
            print(colors.red("No (new) statements found!"))
            return None
        # Get list of already defined accounts
        print(f"{colors.green(str(statement_df.shape[0]))} transactions found...")
        new_xacts = []

        idx = 0
        while True:
            os.system("clear")
            print(selector.prev_xact_df.tail(5))
            row = statement_df.iloc[idx]
            xact = Xact(
                source_account=source_account,
                amount=row["Amount"],
                description=row["Description"],
                date_str=str(row["Date"].date()),
                commodity=row["Commodity"] if row["Commodity"] else default_commodity,
            )
            input_str = selector.get_target_account(
                xact=xact,
                prev_account_list=prev_accounts,
                progress=f"Account No. {idx + 1} / {statement_df.shape[0]}",
            )
            if input_str == "k":
                if idx > 0:
                    idx -= 1
                    new_xacts.pop()
                else:
                    idx = 0

                selector.prev_xact_df = selector.prev_xact_df[:-1]  # Remove last row
                continue
            else:
                xact.target_account = input_str
                selector.append_xact_to_prev_df(xact)
                new_xacts.append(xact)
                idx += 1

                if idx == statement_df.shape[0]:
                    print("Finished!")
                    break  # TODO: Add keybinding to quit

        selector.update_prev_xact_file()

        parser.append_xacts_to_ledger_file(new_xacts)
        # Only add accounts not originally in accounts.ledger
        parser.append_accounts_to_file(
            list(
                selector.new_accounts.difference(set(prev_accounts)).difference(
                    {"", "k", "p"}
                )
            )
        )
    except KeyboardInterrupt:
        print("Detected KeyboardInterrupt, quitting...")
        while True:
            save_progress = input(
                f"Save progress? [{colors.green('y')}]/[{colors.red('n')}]: "
            )
            if save_progress not in ("y", "n"):
                print(f"{save_progress} is not a valid option! Please type y or n...")
                continue
            elif save_progress == "y":
                selector.update_prev_xact_file()

                parser.append_xacts_to_ledger_file(new_xacts)
                # Only add accounts not originally in accounts.ledger
                parser.append_accounts_to_file(
                    list(
                        selector.new_accounts.difference(set(prev_accounts)).difference(
                            {"", "k", "p"}
                        )
                    )
                )
                print(f"Progress saved! {colors.green('FINISHED')}...")
                break
            else:
                print(f"Exiting! Progress {colors.red('NOT')} saved!")
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()  # For command line args

    parser.add_argument(
        "statements_file_name",
        help="Santander exported txt file to parse.",
    )
    parser.add_argument(
        "-d",
        "--date-after",
        dest="date_after",
        help="Date to start parsing transactions after.",
    )
    parser.add_argument(
        "account_key",
        help="Key corresponding to account for ledger and accounts files from config.json",
    )
    args = parser.parse_args()

    main(
        statement_file_name=args.statements_file_name,
        account_key=args.account_key,
        date_after=args.date_after,
    )

    # For testing
    # statement_file_name = "Statements09012964141909.txt"
    # main(statement_file_name)
