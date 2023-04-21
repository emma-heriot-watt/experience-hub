import itertools
from pathlib import Path

from loguru import logger


if __name__ == "__main__":
    # Get the path to the CSV file
    feedback_csv = Path("src/emma_experience_hub/constants/simbot/feedback_rules.csv")

    # Load all the lines from the CSV
    all_lines_from_csv: list[str] = [line for line in feedback_csv.read_text().split("\n") if line]

    header_row = all_lines_from_csv[0]
    rule_rows = list(set(all_lines_from_csv[1:]))

    logger.info(f"Loaded {len(rule_rows)} rules from the CSV")

    # Sort all the rules by their condition
    sorted_rule_rows = sorted([line.split(",") for line in rule_rows], key=lambda row: row[0])

    # Group lines by their condition
    rule_groups = [
        [",".join(line) for line in lines]
        for _, lines in itertools.groupby(sorted_rule_rows, lambda line: line[0])
    ]

    logger.info(f"Total {len(rule_groups)} groupings of rules")

    # Write all the rules to the file with spaces between them
    with open(feedback_csv, "w") as feedback_csv_file:
        # Add the header row in
        feedback_csv_file.write(header_row)
        feedback_csv_file.write("\n")

        for rule_group in rule_groups:
            for rule in rule_group:
                feedback_csv_file.write(rule)
                feedback_csv_file.write("\n")

            # Add a blank line after each chunk of rules
            feedback_csv_file.write("\n")

    logger.info("Done!")
