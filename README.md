Financial Management Web App Specification

Project Overview

A local Python-based web application to ingest bank, post office, and investment statements (PDF, Excel, CSV), maintain transaction history using SCD Type 2, and present a professional dashboard. Backend is entirely database-driven (Postgres), with auditability, exports, and optional Power BI integration.

Architecture and Stack

Runtime: Python 3.10+

Web Framework: FastAPI (backend APIs) + Jinja2 (UI) or Dash/Streamlit (dashboards)

Database: PostgreSQL (localhost:5432, database: cashcow, schema: public)

ORM/DB Access: SQLAlchemy or psycopg2

ETL/Parsing: pandas, openpyxl, csv, pdfplumber/camelot, tabula-py

File Storage: Local folders for uploads and processed files

Exports: CSV, Excel, JSON

Power BI: Direct connection to Postgres tables/views

Database Schema Design (Conceptual)

Core Dimensions (SCD Type 2)

Institution Dimension: Banks, post office, brokers, AMCs

Account Dimension: Bank/post office/investment accounts

Category Dimension: Transaction categories

Facts

Transaction Fact: Immutable ledger of transactions

Investment Position Fact: Positions snapshot (MF, equity, FD, RD, PPF, NSC)

Cash Flow Fact: Cash flows for investment accounts

Uploads, Batches, Audit, Errors

Upload Job: Each uploaded file and its lifecycle

Ingestion Batch: Group related loads for rollback/reporting

Audit Log: Every important action end-to-end

Error Log: Parsing/validation errors with row context

Staging Tables

Bank Transactions Staging

Investment Statements Staging

Indexes and Constraints

Transaction fact: account/date, institution/date, dedupe key

Investment position fact: account/date, instrument/date

Cash flow fact: account/date, instrument/date

SCD Type 2 Handling and ETL Pipeline

SCD Type 2 Pattern

Detect changes in dimension attributes

Close old record (valid_to, is_current = FALSE)

Insert new record (valid_from, is_current = TRUE)

ETL Pipeline Steps

Receive upload (audit, upload_job)

Parse to staging (PDF/Excel/CSV)

Validate (rules, error_log)

Transform & SCD (map dims, compute dedupe_key)

Load facts (begin ingestion_batch, commit)

Post-load checks (reconcile anomalies, audit)

UI and Dashboard Layout

Navigation Structure

Sidebar: Accounts, Transactions, Investments, Uploads, Reports, Settings

Top bar: Date range selector, filters, export buttons

Pages

Accounts Overview: KPIs, account table, balance trend chart

Transactions: Filters, table, monthly spending vs income chart, category breakdown

Investments: KPIs, positions table, allocation pie chart, value trend line

Uploads: Drag-and-drop upload, history with status/errors

Reports: Monthly statement, category report, cash flow summary

Settings: Backup/restore, mappings management

Exports and Power BI Integration

Exports: CSV, Excel, JSON from filtered views

Scheduled Exports: Optional nightly dumps to local folder

Power BI: Direct Postgres connection; convenience views for current-only dimensions

Project Structure : Ensure you follow Python 4 layer architecutre to decide on the skeleton structure, Infact go for DATAMESH implementation 

Technical Specifications and Key Decisions

Backend: FastAPI for APIs, Jinja2/Dash for UI

Parsing: pandas, pdfplumber/camelot/tabula-py

Validation: Central rules engine, error_log

Deduplication: dedupe_key based on institution, account, date, amount, description

Performance: Indexes, batch inserts, materialized views

Backups: Nightly pg_dump, archival of processed files

Security: Local-only, bind server to localhost

Testing: Unit tests, integration tests, data integrity checks

Minimal API Blueprint (Conceptual)

Upload endpoint: receive files, parse, validate, load

Transaction endpoint: query/filter transactions

Export endpoint: generate CSV/Excel/JSON

Next Steps

Confirm UI stack (Jinja2 vs Dash/Streamlit)

Approve schema design

Pick institutions to template first (bank + post office)

Define category rules for auto-categorization