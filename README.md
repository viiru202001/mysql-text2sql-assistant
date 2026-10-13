# MySQL Text-to-SQL Business Assistant

An intelligent pipeline that turns natural language business questions into safe, read-only MySQL queries, executes them securely, and converts raw rows into plain-English executive summaries.

## Features
- **Dynamic Schema Inspection:** Automatically reads your MySQL database schema to inform the LLM.
- **Read-Only Guardrails:** Blocks dangerous keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, etc.) at the code level.
- **Natural Language Insights:** Translates raw SQL output back into business-friendly takeaways.

## Setup & Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
