# 🚀 AI-Assisted Medallion Data Pipeline

## Overview

This project implements a Medallion Architecture pipeline using PostgreSQL:

```text
Bronze → Silver → Gold
```

The pipeline processes facilities management ticket data and demonstrates how AI agents can accelerate data engineering workflows.

---

# 🏗️ Architecture

```text
                    +------------------+
                    | raw_tickets.csv  |
                    +---------+--------+
                              |
                              v
                    +------------------+
                    | Bronze Layer     |
                    | bronze.tickets   |
                    |                  |
                    | Raw ingestion    |
                    | Row hash         |
                    | Source file      |
                    | Batch id         |
                    | Ingested at      |
                    +---------+--------+
                              |
                              v
                    +------------------+
                    | Silver Layer     |
                    | silver.tickets   |
                    |                  |
                    | Deduplication    |
                    | Validation       |
                    | Type conversion  |
                    | Standardization  |
                    | Quality flags    |
                    +---------+--------+
                              |
            +----------------+----------------+
            |                                 |
            v                                 v

+----------------------+      +-------------------------+
| Data Quality Agent   |      | Gold Design Agent       |
|                      |      |                         |
| Profiling            |      | KPI recommendations     |
| Null analysis        |      | Business model design   |
| Schema inference     |      | Aggregation proposals   |
+-----------+----------+      +-----------+-------------+
            |                             |
            +-------------+---------------+
                          |
                          v

                  +---------------+
                  | Gold Layer    |
                  |               |
                  | ticket_kpis   |
                  | building_hotspots |
                  | assignee_performance |
                  +---------------+
```

---

# 🥉 Bronze Layer

### Schema

```sql
bronze.tickets_raw
```

### Purpose

* Raw ingestion
* Schema-on-read
* No data loss
* Lineage tracking

### Metadata Added

| Column           | Purpose                              |
| ---------------- | ------------------------------------ |
| source_file      | Source file name                     |
| source_file_hash | File-level idempotency               |
| batch_id         | Ingestion batch tracking             |
| ingested_at      | Ingestion timestamp                  |
| row_hash         | Row-level lineage and dedup tracking |

### Idempotency

The Bronze layer computes a hash of the input file before ingestion:

```python
MD5(file)
```

If the file has already been loaded:

```text
Skip ingestion
```

This allows the pipeline to be safely rerun without creating duplicate records.

---

# 🥈 Silver Layer

### Schema

```sql
silver.tickets
```

### Purpose

* Cleansing
* Standardization
* Deduplication
* Validation

---

## Cleaning Rules

### 1. Ticket Deduplication

**Rule**

```text
Keep latest record per ticket_id
```

**Reason**

Duplicate tickets should not inflate reporting metrics.

---

### 2. Priority Normalization

Examples:

```text
High
HIGH
high
H
```

Normalized to:

```text
HIGH
```

**Reason**

Ensures consistent reporting and aggregation.

---

### 3. Category Standardization

Examples:

```text
Electrical
electrical
Electrical Issue
```

Mapped into standardized categories.

**Reason**

Prevents fragmented analytics caused by inconsistent category names.

---

### 4. Cost Cleaning

**Rule**

```text
Convert values to numeric
Invalid values → NULL
```

**Reason**

Enables reliable financial analysis.

---

### 5. Quality Flags

Issues tracked:

* Missing ticket_id
* Missing created_at
* Missing category
* Missing priority
* Invalid cost

**Reason**

Supports downstream monitoring and data quality reporting.

---

# 🥇 Gold Layer

### Schemas

```sql
gold.ticket_kpis
gold.building_hotspots
gold.assignee_performance
```

---

## 1. ticket_kpis

### Business Purpose

Track overall operational performance.

### Metrics

* Ticket count
* Resolution rate
* Average resolution time
* Open vs Closed ticket ratio

---

## 2. building_hotspots

### Business Purpose

Identify buildings generating the highest ticket volume.

### Metrics

* Ticket volume
* Average maintenance cost
* Resolution trends
* High-priority ticket concentration

---

## 3. assignee_performance

### Business Purpose

Measure maintenance team performance.

### Metrics

* Assigned tickets
* Resolved tickets
* Average resolution time
* Resolution rate

---

# 🤖 Agentic Acceleration

Two agents were implemented to accelerate data engineering tasks.

---

# Agent 1 — Data Quality Agent

### Type

```text
Rule-Based Local Agent
```

### Purpose

Automatically profile datasets and infer schema characteristics.

### Input

```python
silver_dataframe
```

### Output

```python
{
    "row_count": ...,
    "null_rates": ...,
    "unique_counts": ...,
    "inferred_schema": ...
}
```

### Example Output

```python
{
    "cost_clean": {
        "null_rate": 0.37
    }
}
```

### Value Added

Without the agent:

```text
Manual profiling
Manual schema inspection
```

With the agent:

```text
Automatic quality assessment
Automatic schema inference
```

### Estimated Time Saved

```text
15–30 minutes per dataset
```

---

# Agent 2 — Gold Design Agent

### Type

```text
Local LLM (Ollama)
```

### Model

```text
Llama 3
```

### Purpose

Suggest useful business-facing Gold models and KPIs.

### Input

```text
Schema
+
Data Profile
```

### Output

Example recommendation:

```json
{
  "name": "Assignee Performance",
  "metrics": [
    "Average Resolution Time",
    "Resolution Rate"
  ]
}
```

### Sample Suggestions Generated

* Building Performance
* Assignee Performance
* Operational Bottlenecks
* SLA Compliance

### Value Added

Without the agent:

```text
Manual KPI discovery
Manual dashboard brainstorming
```

With the agent:

```text
Automatic business metric suggestions
```

### Estimated Time Saved

```text
30–60 minutes
```

---

# 📊 Honest Agent Assessment

## Data Quality Agent

### Worth Keeping?

✅ Yes

### Reason

Produces deterministic and reliable profiling results quickly.

Useful for:

* Initial data exploration
* Data quality reviews
* Schema understanding

---

## Gold Design Agent

### Worth Keeping?

✅ Yes, with human review

### Reason

Provides useful business ideas and KPI suggestions.

However, some recommendations may be unrealistic or not aligned with business requirements.

A human should always approve Gold-layer models before implementation.

---

# ⚖️ Cost and Scale Considerations

### Current Dataset

```text
~10K rows
```

### Production Scale

```text
10M+ rows
```

---

## Bronze Layer

### Current

```text
Pandas ingestion
```

### Production

```text
PostgreSQL COPY
Partitioned tables
Incremental ingestion
```

---

## Silver Layer

### Current

```text
Pandas transformations
```

### Production

```text
SQL-based transformations
dbt
Apache Spark
```

---

## Agents

### Current

```text
Full dataset profiling
```

### Production

```text
Sampling
Caching
Batch processing
Metadata-only analysis
```

Only schema metadata and representative samples would be sent to the LLM to reduce cost and latency.

---

# ▶️ How To Run

## 1. Clone Repo

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```
---

## 2. Create Virtual Environment

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---
## 4. Setup LLM (Ollama)

```bash
brew install ollama

ollama serve
ollama run llama3
```

---

## 5. Start PostgreSQL

```bash
docker-compose up -d
```

---



## 6. Run Pipeline

```bash
python run_pipeline.py
```

---

## 7. Query Results

### Bronze

```sql
SELECT * FROM bronze.tickets_raw LIMIT 10;
```

### Silver

```sql
SELECT * FROM silver.tickets LIMIT 10;
```

### Gold

```sql
SELECT * FROM gold.ticket_kpis;

SELECT * FROM gold.building_hotspots;

SELECT * FROM gold.assignee_performance;
```

---

# 🛠️ Technologies Used

* Python
* PostgreSQL
* Pandas
* SQLAlchemy
* Docker
* Ollama
* Llama 3
* Medallion Architecture

---

# 🎯 Assignment Requirements Coverage

| Requirement              | Status |
| ------------------------ | ------ |
| Bronze Layer             | ✅      |
| Silver Layer             | ✅      |
| Gold Layer               | ✅      |
| Lineage Metadata         | ✅      |
| Idempotent Pipeline      | ✅      |
| Re-runnable Pipeline     | ✅      |
| Data Quality Agent       | ✅      |
| Gold Design Agent        | ✅      |
| Local LLM Integration    | ✅      |
| Logging & Monitoring     | ✅      |
| Scale Considerations     | ✅      |
| Architecture Diagram     | ✅      |
| Agent Assessment         | ✅      |
| Single Command Execution | ✅      |

```
```
