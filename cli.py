# cli.py
import sys

from parser import parse_sql, SQLParseError
from engine import QueryEngine, QueryExecutionError


def print_table(columns, rows):
    """
    Print rows as a simple table:
    col1 | col2
    ---- | ----
    v11  | v12
    """
    if not columns:
        print("(no columns)")
        return

    # Convert everything to string for printing
    str_rows = [
        ["" if row.get(c) is None else str(row.get(c)) for c in columns]
        for row in rows
    ]

    # Compute column widths
    widths = []
    for i, col in enumerate(columns):
        max_len = len(col)
        for r in str_rows:
            if len(r[i]) > max_len:
                max_len = len(r[i])
        widths.append(max_len)

    def format_row(values):
        return " | ".join(
            v.ljust(widths[i]) for i, v in enumerate(values)
        )

    # Header
    print(format_row(columns))
    print(format_row(["-" * w for w in widths]))

    # Rows
    for r in str_rows:
        print(format_row(r))


def main():
    if len(sys.argv) != 2:
        print("Usage: python cli.py path/to/table.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    engine = QueryEngine()
    try:
        table = engine.load_table_from_csv(csv_path)
    except QueryExecutionError as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)

    print(f"Loaded table '{table.name}' from '{csv_path}'")
    print("Enter SQL queries, or type 'exit', 'quit', or '\\q' to quit.")
    print(f"Remember: use FROM {table.name}")
    print()

    while True:
        try:
            line = input("sql> ")
        except EOFError:
            print()
            break

        if line is None:
            break

        stripped = line.strip()
        if stripped.lower() in ("exit", "quit", "\\q"):
            break
        if not stripped:
            continue

        try:
            parsed = parse_sql(stripped)
            columns, rows = engine.execute(parsed)
            print_table(columns, rows)
        except SQLParseError as e:
            print(f"[Syntax error] {e}")
        except QueryExecutionError as e:
            print(f"[Execution error] {e}")
        except Exception as e:
            # Catch-all to avoid crashing; helpful in evaluation
            print(f"[Unexpected error] {e}")

        print()  # blank line after each result

    print("Goodbye!")


if __name__ == "__main__":
    main()
