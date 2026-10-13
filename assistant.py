import json
import re
import mysql.connector
from openai import OpenAI

class MySQLAssistant:
    def __init__(self, db_config: dict, openai_api_key: str):
        self.db_config = db_config
        self.client = OpenAI(api_key=openai_api_key)
        self.schema_context = self._fetch_db_schema()

    def _fetch_db_schema(self) -> str:
        """Dynamically inspects the MySQL database to build the schema prompt context."""
        schema_info = []
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get all table names
        cursor.execute("SHOW TABLES;")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"DESCRIBE {table};")
            columns = cursor.fetchall()
            col_desc = ", ".join([f"{col['Field']} ({col['Type']})" for col in columns])
            schema_info.append(f"Table '{table}': [{col_desc}]")
            
        cursor.close()
        conn.close()
        return "\n".join(schema_info)

    def validate_read_only(self, sql: str) -> bool:
        """Validates that the SQL query is strictly read-only."""
        normalized_sql = sql.lower().strip()
        
        # Ensure it starts with SELECT or WITH (for CTEs)
        if not (normalized_sql.startswith('select') or normalized_sql.startswith('with')):
            return False

        # Block any write or schema modification keywords
        forbidden_keywords = [
            'insert', 'update', 'delete', 'drop', 'alter', 
            'truncate', 'create', 'replace', 'grant', 'revoke'
        ]
        
        for word in forbidden_keywords:
            if re.search(r'\b' + word + r'\b', normalized_sql):
                return False
                
        return True

    def generate_sql(self, question: str) -> str:
        """Generates a MySQL query from natural language."""
        system_prompt = f"""
        You are an expert MySQL data analyst. Translate business questions into valid MySQL queries.
        
        DATABASE SCHEMA:
        {self.schema_context}
        
        RULES:
        1. Produce ONLY valid, read-only SELECT or CTE queries for MySQL.
        2. Never use write/modify queries (INSERT, UPDATE, DELETE, ALTER, DROP, etc.).
        3. Use standard MySQL functions (e.g., DATE_FORMAT, IFNULL, CONCAT).
        4. Apply a default LIMIT 100 unless a specific limit is requested.
        5. Return ONLY a JSON object with the format: {{"sql": "<your query>"}}
        """

        response = self.client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )
        
        data = json.loads(response.choices[0].message.content)
        return data["sql"]

    def execute_query(self, sql: str):
        """Executes the query safely on MySQL in read-only mode."""
        if not self.validate_read_only(sql):
            raise ValueError("Security Alert: Query failed read-only safety checks.")

        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Execute query
        cursor.execute(sql)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return results

    def explain_results(self, question: str, sql: str, results: list) -> str:
        """Translates the SQL result back into plain business insights."""
        prompt = f"""
        User Question: "{question}"
        Executed SQL: `{sql}`
        Query Results: {json.dumps(results, default=str)}
        
        Provide a concise, executive summary explaining the findings directly answering the question.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def ask(self, question: str) -> dict:
        """Main pipeline handler."""
        sql = self.generate_sql(question)
        results = self.execute_query(sql)
        insight = self.explain_results(question, sql, results)
        
        return {
            "question": question,
            "sql": sql,
            "results": results,
            "insight": insight
        }
