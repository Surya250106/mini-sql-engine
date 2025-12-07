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

mini-sql-engine/
│
├── parser.py # SQL string → ParsedQuery object
├── engine.py # Query execution engine
├── cli.py # Command-line REPL interface
│
├── data/
│ ├── people.csv # Sample dataset (employee example)
│ └── sales.csv # Additional optional dataset
│
└── README.md


---

## Installation

Requires Python **3.8+**.

No external libraries are required — uses only the Python standard library.

### Clone the repository

```bash
git clone <https://github.com/Surya250106/mini-sql-engine>.git
cd mini-sql-engine
