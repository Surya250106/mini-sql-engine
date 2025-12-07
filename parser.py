# parser.py
import re
from dataclasses import dataclass
from typing import List, Optional, Any


class SQLParseError(Exception):
    """Raised for any SQL syntax/parse errors."""
    pass


@dataclass
class WhereClause:
    column: str
    operator: str
    value: Any  # str, int, float


@dataclass
class Aggregate:
    func: str  # currently only "COUNT"
    arg: str   # "*" or column name


@dataclass
class ParsedQuery:
    table: str
    select_columns: List[str]              # empty if aggregate-only
    aggregate: Optional[Aggregate] = None  # None if not aggregate
    where: Optional[WhereClause] = None


# Main SELECT pattern:
#   SELECT <select> FROM <table> [WHERE <where>];
SELECT_PATTERN = re.compile(
    r"""
    ^\s*SELECT\s+(?P<select>.+?)\s+
    FROM\s+(?P<table>[A-Za-z_][A-Za-z0-9_]*)
    (?:\s+WHERE\s+(?P<where>.+?))?
    ;?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def parse_sql(sql: str) -> ParsedQuery:
    """
    Parse a simple SQL query into a ParsedQuery object.

    Supported form:
        SELECT <columns or COUNT(...)> FROM <table> [WHERE <col> <op> <value>];
    """
    match = SELECT_PATTERN.match(sql)
    if not match:
        raise SQLParseError("Could not parse SQL. Expected: SELECT ... FROM table [WHERE ...];")

    select_part = match.group("select").strip()
    table = match.group("table").strip()
    where_part = match.group("where")
    where_clause = _parse_where(where_part) if where_part else None

    # SELECT can be:
    #  - COUNT(*)
    #  - COUNT(col)
    #  - *
    #  - col1, col2, ...
    select_columns: List[str] = []
    aggregate: Optional[Aggregate] = None

    # Try aggregate first
    agg = _parse_aggregate(select_part)
    if agg is not None:
        aggregate = agg
        # We do NOT support mixing aggregates and normal columns
        return ParsedQuery(
            table=table,
            select_columns=[],
            aggregate=aggregate,
            where=where_clause,
        )

    # Not aggregate: parse columns
    if select_part == "*":
        select_columns = ["*"]
    else:
        parts = [p.strip() for p in select_part.split(",")]
        if not parts or any(not p for p in parts):
            raise SQLParseError("Invalid column list in SELECT clause.")
        select_columns = parts

    return ParsedQuery(
        table=table,
        select_columns=select_columns,
        aggregate=None,
        where=where_clause,
    )


def _parse_aggregate(select_part: str) -> Optional[Aggregate]:
    """
    Parse COUNT(*) or COUNT(col). Return Aggregate or None if not aggregate.
    """
    agg_pattern = re.compile(
        r"^COUNT\s*\(\s*(?P<arg>\*|[A-Za-z_][A-Za-z0-9_]*)\s*\)$",
        re.IGNORECASE,
    )
    m = agg_pattern.match(select_part)
    if not m:
        return None

    arg = m.group("arg")
    return Aggregate(func="COUNT", arg=arg)


def _parse_where(where_part: str) -> WhereClause:
    """
    Parse WHERE like: column op value
    op in (=, !=, >, <, >=, <=)
    value can be:
      - string: 'text' or "text"
      - number: int or float
    """
    where_pattern = re.compile(
        r"""
        ^\s*
        (?P<col>[A-Za-z_][A-Za-z0-9_]*)
        \s*
        (?P<op>=|!=|>=|<=|>|<)
        \s*
        (?P<val>.+?)
        \s*$
        """,
        re.VERBOSE,
    )
    m = where_pattern.match(where_part)
    if not m:
        raise SQLParseError(
            "Could not parse WHERE clause. Expected: column OP value "
            "with OP in (=, !=, >, <, >=, <=)."
        )

    col = m.group("col")
    op = m.group("op")
    raw_val = m.group("val").strip()

    value = _parse_value(raw_val)

    return WhereClause(column=col, operator=op, value=value)


def _parse_value(raw_val: str) -> Any:
    """
    Parse a WHERE value as either string or number.
    Strings must be quoted with single or double quotes.
    """
    # Quoted string
    if (
        (raw_val.startswith("'") and raw_val.endswith("'"))
        or (raw_val.startswith('"') and raw_val.endswith('"'))
    ):
        return raw_val[1:-1]

    # Try int
    try:
        return int(raw_val)
    except ValueError:
        pass

    # Try float
    try:
        return float(raw_val)
    except ValueError:
        pass

    raise SQLParseError(
        f"Invalid literal value in WHERE clause: {raw_val!r}. "
        "Strings must be quoted; numbers unquoted."
    )


# Simple manual tests
if __name__ == "__main__":
    tests = [
        "SELECT * FROM people;",
        "SELECT name, age FROM people",
        "SELECT COUNT(*) FROM people;",
        "SELECT COUNT(age) FROM people WHERE country = 'USA';",
        "SELECT name FROM people WHERE age > 30;",
    ]

    for sql in tests:
        print("SQL:", sql)
        try:
            pq = parse_sql(sql)
            print(" ParsedQuery:", pq, "\n")
        except SQLParseError as e:
            print(" ERROR:", e, "\n")

