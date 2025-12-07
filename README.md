# Mini SQL Engine (In-Memory Query Processor)

## Overview

This project implements a simplified **in-memory SQL query engine** written in Python.  
It demonstrates how a database processes a SQL query internally — covering parsing, filtering, projection, and aggregation — without relying on any external SQL libraries.

The engine loads a CSV file into memory and supports a subset of SQL, including:

- `SELECT *`
- `SELECT column1, column2`
- `WHERE` with comparison operators
- `COUNT(*)` and `COUNT(column)`
- An interactive REPL (CLI) where users can execute SQL queries

This project is designed for educational purposes to illustrate how SQL engines work under the hood.

---

## Project Structure

```
mini-sql-engine/
│
├── parser.py        # SQL string → ParsedQuery object
├── engine.py        # Query execution engine
├── cli.py           # Command-line REPL interface
│
├── data/
│   ├── people.csv   # Sample dataset (employee example)
│   └── sales.csv    # Additional optional dataset
│
└── README.md
```

---

## Installation

Requires **Python 3.8+**.  
No external libraries are needed — only the Python standard library.

### Clone the repository

```bash
git clone https://github.com/Surya250106/mini-sql-engine.git
cd mini-sql-engine
```

### (Optional) Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```

---

## Running the CLI

Run the REPL and load a CSV:

```bash
python cli.py data/people.csv
```

Example session:

```
Loaded table 'people' from 'data/people.csv'
Enter SQL queries, or type 'exit', 'quit', or '\q' to quit.
Remember: use FROM people

sql> SELECT * FROM people;
sql> SELECT name, department FROM people;
sql> SELECT email FROM people WHERE department = 'Engineering';
sql> SELECT COUNT(*) FROM people;
sql> SELECT COUNT(email) FROM people WHERE department = 'HR';
```

Exit using:

```
exit
quit
\q
```

---

## Supported SQL Grammar

This engine supports a controlled subset of SQL, described below.

---

### **1. SELECT Clause**

#### Select all columns

```sql
SELECT * FROM people;
```

#### Select specific columns

```sql
SELECT name, department FROM people;
```

---

### **2. WHERE Clause**

Supports exactly one condition.

Format:

```
WHERE <column> <operator> <value>
```

#### Supported Operators

| Operator | Meaning        |
|----------|----------------|
| =        | equals         |
| !=       | not equals     |
| >        | greater than   |
| <        | less than      |
| >=       | greater or equal |
| <=       | less or equal    |

#### Value Types

- **Strings** must be quoted:

```sql
WHERE department = 'Engineering'
```

- **Numbers** are unquoted:

```sql
WHERE age > 30
```

---

### **3. Aggregation**

Only **COUNT()** is supported.

#### Count all rows

```sql
SELECT COUNT(*) FROM people;
```

#### Count non-null values in a column

```sql
SELECT COUNT(email) FROM people;
```

❌ Not allowed (mixing aggregates with columns):

```sql
SELECT name, COUNT(*) FROM people;
```

---

### **4. Table Rules**

- Only **one table** per query
- Table name = CSV filename without `.csv`

Examples:

| File        | Table  |
|-------------|--------|
| people.csv  | people |
| sales.csv   | sales  |

---

## Example Queries

Assume `people.csv` contains:

| employee_id | name           | department   | email               |
|-------------|----------------|--------------|---------------------|
| 1           | Alice Johnson  | HR           | alice@example.com   |
| 2           | Bob Smith      | Engineering  | bob@example.com     |
| 3           | Carol Lee      | Sales        | carol@example.com   |

### All rows

```sql
SELECT * FROM people;
```

### Projection

```sql
SELECT name, department FROM people;
```

### Filtering

```sql
SELECT name FROM people WHERE department = 'Engineering';
```

### Aggregation

```sql
SELECT COUNT(*) FROM people;
SELECT COUNT(email) FROM people WHERE department = 'HR';
```

---

## Error Handling

The engine provides intentional, clear error messages for:

- Invalid SQL syntax
- Unknown columns
- Mismatched data types
- Unsupported operations
- Nonexistent table

Examples:

```
[Execution error] Column 'age' does not exist.
[Syntax error] Could not parse SQL. Expected: SELECT ... FROM table [WHERE ...];
```

---

## Limitations (Intentional for Learning Purposes)

- No JOINs  
- No GROUP BY  
- No ORDER BY  
- No INSERT / UPDATE / DELETE  
- Only one WHERE condition  
- Only COUNT() is implemented  
- Only one table can be loaded at a time  

---

## Future Enhancements

Potential improvements include:

- Support AND / OR in WHERE  
- Add SUM, AVG, MIN, MAX  
- Implement ORDER BY  
- Add GROUP BY  
- Support multiple tables  
- Introduce JOIN operations  

---

## Author 
SURYA

