AI-Assisted Medallion Data Pipeline
Overview

This project implements a Medallion Architecture pipeline using PostgreSQL:

Bronze → Silver → Gold

The pipeline processes facilities management ticket data and demonstrates how AI agents can accelerate data engineering workflows.

Architecture

(paste diagram here)

Layer Design
Bronze Layer

Schema:

bronze.tickets_raw

Purpose:

Raw ingestion
Schema-on-read
No data loss
Lineage tracking

Metadata added:

Column	Purpose
source_file	source file name
source_file_hash	file-level idempotency
batch_id	ingestion batch tracking
ingested_at	ingestion timestamp
row_hash	row-level lineage
Idempotency

The Bronze layer computes:

MD5(file)

before ingestion.

If the file has already been loaded:

Skip ingestion

This allows safe reruns without duplicate data.

Silver Layer

Schema:

silver.tickets

Purpose:

Cleansing
Standardization
Deduplication
Validation
Cleaning Rules
Ticket Deduplication

Rule:

Keep latest record per ticket_id

Reason:

Duplicate tickets should not inflate metrics.

Priority Normalization

Examples:

High
HIGH
high
H

become

HIGH

Reason:

Consistent analytics.

Category Standardization

Examples:

Electrical
electrical
Electrical Issue

normalized into a standard category.

Reason:

Prevent fragmented reporting.

Cost Cleaning

Rule:

Convert to numeric
Invalid values → NULL

Reason:

Support financial analysis.

Quality Flags

Issues tracked:

Missing ticket id
Missing creation date
Missing category
Missing priority
Invalid cost

Reason:

Enable downstream quality monitoring.

Gold Layer

Schema:

gold.ticket_kpis
gold.building_hotspots
gold.assignee_performance
1. ticket_kpis

Business purpose:

Track operational performance.

Metrics:

ticket count
resolution rate
average resolution time
2. building_hotspots

Business purpose:

Identify buildings generating the most tickets.

Metrics:

ticket volume
average cost
resolution trends
3. assignee_performance

Business purpose:

Evaluate maintenance team performance.

Metrics:

assigned tickets
resolved tickets
average resolution time
Agentic Acceleration

Two agents were implemented.

Agent 1: Data Quality Agent

Type:

Rule-based local agent

Purpose:

Automatically profile data and infer schema.

Input:

silver dataframe

Output:

{
  row_count,
  null_rates,
  unique_counts,
  inferred_schema
}

Example Output:

{
  "cost_clean": {
      "null_rate": 0.37
  }
}
Value Added

Without the agent:

Manual profiling
Manual schema review

With the agent:

Automatic quality assessment
Automatic schema inference

Estimated time saved:

15-30 minutes per dataset
Agent 2: Gold Design Agent

Type:

Local LLM (Ollama)

Model:

llama3

Purpose:

Suggest useful business-facing Gold models.

Input:

schema
+
data profile

Output:

Building Performance
Assignee Performance
Operational Bottlenecks

Example:

{
  "name": "Assignee Performance",
  "metrics": [
      "Average Resolution Time",
      "Resolution Rate"
  ]
}
Value Added

Without the agent:

Manual KPI discovery
Manual dashboard brainstorming

With the agent:

Automatic business metric suggestions

Estimated time saved:

30-60 minutes
Honest Agent Assessment
Data Quality Agent

Worth keeping:

✅ Yes

Reason:

Produces deterministic profiling quickly and reliably.

Gold Design Agent

Worth keeping:

✅ Yes, with human review

Reason:

Produces useful ideas but occasionally suggests unrealistic metrics.

Human approval should remain part of the workflow.

Cost and Scale Considerations

Current dataset:

~10k rows

Production scale:

10M+ rows

Changes required:

Bronze

Current:

Pandas

Production:

COPY command
Partitioned tables
Incremental loads
Silver

Current:

Pandas transformations

Production:

SQL transformations
Spark / dbt
Agents

Current:

Full dataset profile

Production:

Sample-based profiling
Caching
Batch processing

Only schema metadata and samples would be sent to the LLM.

How To Run
Start PostgreSQL
docker-compose up -d
Install dependencies
pip install -r requirements.txt
Run pipeline
python run_pipeline.py
Query results
SELECT * FROM bronze.tickets_raw LIMIT 10;

SELECT * FROM silver.tickets LIMIT 10;

SELECT * FROM gold.ticket_kpis;

SELECT * FROM gold.building_hotspots;

SELECT * FROM gold.assignee_performance;
Technologies Used
Python
PostgreSQL
Pandas
SQLAlchemy
Docker
Ollama
Llama 3
Medallion Architecture
