# engine.py
import csv
import os
from typing import List, Dict, Any


class QueryExecutionError(Exception):
    """Basic error type for data loading / execution problems."""
    pass


class Table:
    """
    Represents a simple in-memory table loaded from a CSV file.

    - name: table name (derived from filename without extension)
    - rows: list of dictionaries, one per row
    - columns: list of column names
    """

    def __init__(self, name: str, rows: List[Dict[str, Any]]) -> None:
        self.name = name
        self.rows = rows
        self.columns = list(rows[0].keys()) if rows else []

    @classmethod
    def from_csv(cls, path: str) -> "Table":
        """
        Load a CSV file into a Table.

        Uses csv.DictReader so each row is a dict:
        {column_name: value_as_string}
        """
        if not os.path.exists(path):
            raise QueryExecutionError(f"CSV file not found: {path}")

        base = os.path.basename(path)
        name, _ = os.path.splitext(base)

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        return cls(name=name, rows=rows)


if __name__ == "__main__":
    # Small manual test for step 1.2
    csv_path = "data/people.csv"  # make sure this path exists

    try:
        table = Table.from_csv(csv_path)
    except QueryExecutionError as e:
        print(f"Error: {e}")
    else:
        print(f"Loaded table '{table.name}' with columns: {table.columns}")
        print("First 3 rows:")
        for row in table.rows[:3]:
            print(row)

# engine.py
import csv
import os
from typing import List, Dict, Any, Tuple, Optional

from parser import ParsedQuery, WhereClause, Aggregate, SQLParseError, parse_sql


class QueryExecutionError(Exception):
    """Raised for semantic/runtime errors during query execution."""
    pass


class Table:
    """
    Represents a simple in-memory table loaded from a CSV file.

    - name: table name (derived from filename without extension)
    - rows: list of dictionaries, one per row
    - columns: list of column names
    """

    def __init__(self, name: str, rows: List[Dict[str, Any]]) -> None:
        self.name = name
        self.rows = rows
        self.columns = list(rows[0].keys()) if rows else []

    @classmethod
    def from_csv(cls, path: str) -> "Table":
        """
        Load a CSV file into a Table.

        Uses csv.DictReader so each row is a dict:
        {column_name: value_as_string}
        """
        if not os.path.exists(path):
            raise QueryExecutionError(f"CSV file not found: {path}")

        base = os.path.basename(path)
        name, _ = os.path.splitext(base)

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        return cls(name=name, rows=rows)


class QueryEngine:
    """
    In-memory query engine that can execute a ParsedQuery on loaded tables.
    For now we support a single table at a time.
    """

    def __init__(self) -> None:
        self.tables: Dict[str, Table] = {}

    def load_table_from_csv(self, path: str) -> Table:
        table = Table.from_csv(path)
        self.tables[table.name] = table
        return table

    def execute(self, query: ParsedQuery) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Execute a ParsedQuery.

        Returns:
            (columns, rows)
        where rows is a list of dictionaries with those columns as keys.
        """
        table = self._get_table(query.table)

        # 1. Apply WHERE filtering
        filtered_rows = self._apply_where(table, query.where)

        # 2. Aggregation (if any)
        if query.aggregate is not None:
            return self._execute_aggregate(query.aggregate, filtered_rows)

        # 3. Projection (SELECT columns)
        return self._execute_projection(query.select_columns, filtered_rows)

    # ---------- helpers ----------

    def _get_table(self, name: str) -> Table:
        if name not in self.tables:
            raise QueryExecutionError(
                f"Table '{name}' not found. "
                f"Loaded tables: {', '.join(self.tables.keys()) or 'none'}."
            )
        return self.tables[name]

    def _apply_where(
        self,
        table: Table,
        where: Optional[WhereClause],
    ) -> List[Dict[str, Any]]:
        if where is None:
            return table.rows

        col = where.column
        if col not in table.columns:
            raise QueryExecutionError(
                f"Column '{col}' in WHERE clause does not exist. "
                f"Available columns: {', '.join(table.columns)}."
            )

        op = where.operator
        value = where.value
        result = []

        for row in table.rows:
            cell = row.get(col)
            if self._compare(cell, op, value):
                result.append(row)

        return result

    def _compare(self, cell: Any, op: str, value: Any) -> bool:
        """
        Compare cell (a string from CSV) with value (parsed literal).
        - If value is numeric, we try to treat cell as numeric.
        - If value is string, we only allow = and != for safety.
        """
        if cell is None:
            cell_str = ""
        else:
            cell_str = str(cell)

        # Numeric comparison
        if isinstance(value, (int, float)):
            try:
                cell_num = float(cell_str)
            except ValueError:
                raise QueryExecutionError(
                    f"Type mismatch: cannot compare non-numeric value {cell!r} "
                    f"with numeric literal {value!r}."
                )
            return self._apply_operator(cell_num, op, value)

        # String comparison
        if isinstance(value, str):
            if op not in ("=", "!="):
                raise QueryExecutionError(
                    f"String comparisons only support '=' and '!='. "
                    f"Got operator '{op}'."
                )
            return self._apply_operator(cell_str, op, value)

        raise QueryExecutionError(
            f"Unsupported WHERE value type: {type(value).__name__}"
        )

    @staticmethod
    def _apply_operator(left: Any, op: str, right: Any) -> bool:
        if op == "=":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        raise QueryExecutionError(f"Unknown operator: {op}")

    def _execute_aggregate(
        self,
        aggregate: Aggregate,
        rows: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        if aggregate.func.upper() != "COUNT":
            raise QueryExecutionError(f"Unsupported aggregate function: {aggregate.func}")

        arg = aggregate.arg
        if arg == "*":
            count = len(rows)
        else:
            # COUNT(column): count non-null (non-empty) values
            count = 0
            for row in rows:
                v = row.get(arg)
                if v not in (None, ""):
                    count += 1

        col_name = f"COUNT({arg})"
        return [col_name], [{col_name: count}]

    def _execute_projection(
        self,
        select_columns: List[str],
        rows: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        if not select_columns:
            raise QueryExecutionError("No columns specified in SELECT clause.")

        # SELECT * → all columns
        if select_columns == ["*"]:
            if not rows:
                # no rows but we still need columns; infer from table?
                return [], []
            cols = list(rows[0].keys())
            projected = [{c: r.get(c) for c in cols} for r in rows]
            return cols, projected

        # Specific columns
        cols = select_columns

        if rows:
            available = set(rows[0].keys())
            for c in cols:
                if c not in available:
                    raise QueryExecutionError(
                        f"Column '{c}' in SELECT does not exist. "
                        f"Available columns: {', '.join(sorted(available))}."
                    )

        projected_rows = []
        for row in rows:
            projected_rows.append({c: row.get(c) for c in cols})

        return cols, projected_rows


def _print_result(columns: List[str], rows: List[Dict[str, Any]]) -> None:
    """
    Simple helper for manual testing: prints rows as a table.
    """
    if not columns:
        print("(no columns)")
        return

    # Convert all values to strings
    str_rows = [
        ["" if row.get(c) is None else str(row.get(c)) for c in columns]
        for row in rows
    ]

    # Column widths
    widths = []
    for i, col in enumerate(columns):
        max_len = len(col)
        for r in str_rows:
            if len(r[i]) > max_len:
                max_len = len(r[i])
        widths.append(max_len)

    def fmt(vals):
        return " | ".join(v.ljust(widths[i]) for i, v in enumerate(vals))

    # Header
    print(fmt(columns))
    print(fmt(["-" * w for w in widths]))
    # Rows
    for r in str_rows:
        print(fmt(r))


if __name__ == "__main__":
    # Manual test for step 3 (no CLI yet)

    engine = QueryEngine()
    try:
        table = engine.load_table_from_csv("data/people.csv")
    except QueryExecutionError as e:
        print("Error loading table:", e)
        raise SystemExit(1)

    print(f"Loaded table '{table.name}' with columns: {table.columns}")
    print()

    test_queries = [
        "SELECT * FROM people;",
        "SELECT name, department FROM people;",
        "SELECT name, email FROM people WHERE department = 'Engineering';",
        "SELECT COUNT(*) FROM people;",
        "SELECT COUNT(email) FROM people WHERE department = 'HR';",
    ]

    for sql in test_queries:
        print("SQL:", sql)
        try:
            parsed = parse_sql(sql)
            cols, rows = engine.execute(parsed)
            _print_result(cols, rows)
        except (SQLParseError, QueryExecutionError) as e:
            print("Error:", e)
        print()
