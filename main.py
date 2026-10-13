from assistant import MySQLAssistant

# Configure your database connection credentials
db_config = {
    'host': 'localhost',
    'user': 'text2sql_user',
    'password': 'StrongPassword123!',
    'database': 'e_commerce'
}

if __name__ == "__main__":
    # Initialize assistant (Ensure OPENAI_API_KEY environment variable is set or pass key directly)
    assistant = MySQLAssistant(db_config=db_config, openai_api_key="your-openai-key-here")

    # Run a sample business question
    question = "What are our top 3 best-selling product categories this month?"
    
    print(f"Asking: '{question}'\n")
    response = assistant.ask(question)

    print("--- Generated MySQL Query ---")
    print(response["sql"])
    
    print("\n--- Business Insight ---")
    print(response["insight"])
