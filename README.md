# stats_partite_db

Football Database Processor

What Is This Project?

Imagine you have many football match files and instead of just saving them as tables…
you build a real database to store them forever.

This project is like a smart football librarian
It reads match data from JSON files and stores everything inside a SQLite database.

It doesn’t just save data.
It organizes it, updates it, and makes it fast to search.

What Does It Do?

Think of it like this:

-It opens football match files.

-It checks if the match was really played.

-It saves the result in a special digital notebook (the database).

-It avoids saving the same match twice.

-It keeps everything clean and organized.

-And it does this automatically for up to 38 rounds.

Technologies Used

This project uses powerful backend technologies:

-Python 3

The main programming language controlling everything.

-SQLite

A lightweight but powerful relational database.
It allows:

-Structured storage

-Fast searches

-Indexed queries

-Data integrity rules

-JSON

Used as the raw data source for match information.

-Datetime

Used for time-related processing (if needed in future extensions).

-SQL Indexing

Indexes are created on:

-League

-Matchday

-Home team

-Away team

-Winner code

-League + Matchday combination

This dramatically improves query performance.

Database Architecture

The project creates a database called:

calcio.db

Inside it, there is a table:

Table: partite

It contains:

-League name

-Matchday

-Home team

-Away team

-Home goals

-Away goals

-First half goals

-Second half goals (automatically calculated!)

-Winner code

Advanced Features
1 Automatic Table Creation

If the database does not exist:

It is created automatically.

The table is created automatically.

Indexes are created automatically.

Zero manual setup required.

2 Smart Insert (No Duplicates)

The table uses:

UNIQUE(lega, giornata, squadra_casa, squadra_trasferta)

This means:

The same match cannot be inserted twice.

If it already exists, it gets updated instead.

This ensures data consistency and integrity.

3 Automatic Second Half Goal Calculation

The script calculates:

Second Half Goals = Total Goals – First Half Goals

This shows:

Advanced data transformation

Derived data generation

Business logic inside backend

4 Filtering Invalid Matches

The system skips:

Postponed matches

Not started matches

Matches without final score

Only valid results are stored.

Example Workflow

You place files like:

round_1.json
round_2.json
...
round_38.json

Run:

python scrapplusdb.py

The program:

Reads all rounds

Extracts match data

Inserts them into the database

Avoids duplicates

Commits changes safely

Why This Project Is Powerful

Even though it looks simple, it demonstrates:

Object-Oriented Programming (OOP)

Database design principles

SQL indexing

Data normalization

Automated ETL (Extract, Transform, Load)

Data integrity constraints

Scalable backend architecture

This is not just a script.
It is a mini data engineering pipeline with a database layer.

Final Summary

This project is like building a smart football archive:

It reads match data

Cleans and filters it

Stores it in a structured database

Prevents duplicates

Calculates advanced statistics

Optimizes performance with indexes

Simple to understand.
Professional in structure.
Database-driven.
