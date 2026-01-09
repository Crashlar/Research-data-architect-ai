from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
import sqlite3
from dotenv import load_dotenv
import re
load_dotenv()

sql_template = """
You are a highly skilled SQL assistant working with a company database.  
Your role is to generate the most accurate, efficient, and well-structured SQL query based on the user's request.  

Database Schema:
1. employees (employee_id, full_name, role, department, salary, hired_at, is_active)
2. users (user_id, full_name, email, created_at)
3. products (product_id, product_name, category, price, sku, is_active)
4. purchases (purchase_id, user_id, product_id, quantity, total_amount, purchased_at)

### CRITICAL INSTRUCTIONS:
1. Return **ONLY** the SQL query text, nothing else.
2. **NEVER** use markdown code fences like ```sql or ```.
3. **NEVER** add explanations, comments, or additional text.
4. If filtering active records, use `is_active = 1`.
5. Format the SQL with proper indentation for readability.
6. End the query with a semicolon (;).

User question: {question}

SQL Query:
"""

# Explanation template for explaining results in English
explanation_template = """
You are a data analyst explaining SQL query results in simple English.

You have executed this SQL query:
{query}

The query returned these results:
{results}

Now, explain the results in a clear, concise manner:
- What data is being shown?
- What are the key findings or insights?
- Are there any trends or patterns visible?
- Keep it brief but informative.

Explanation:
"""

def clean_sql_query(query: str) -> str:
    """
    Clean SQL query by removing markdown code fences and any non-SQL text.
    """
    # Remove markdown code fences
    query = re.sub(r'^```sql\s*', '', query, flags=re.IGNORECASE)
    query = re.sub(r'^```\s*', '', query)
    query = re.sub(r'\s*```\s*$', '', query)
    
    # Remove any leading/trailing whitespace
    query = query.strip()
    
    return query

@tool
def sql_to_text_output(question :  str , database : str  = "company.db"  ):
    """
    Dynamically converts a natural language question into SQL,
    executes it against the SQLite database, and explains the results in English.
    """
    # Initialize model + parser
    model =  ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0
        )
    parser = StrOutputParser()
    
    # Step 1: Generate SQL query from user question
    sql_prompt = sql_template.format(question=question)
    ai_message = model.invoke(sql_prompt)
    query = parser.parse(ai_message.content)
    
    # Step 2: Clean the SQL query - remove markdown code fences
    query = clean_sql_query(query)  # THIS LINE MUST BE UNCOMMENTED!
    
    print(f"Generated SQL: {query}")  # Add this for debugging

    # Step 3: Execute SQL query
    if not database:
        raise FileNotFoundError("Database file not found or not provided.")

    conn = sqlite3.connect(database=database, check_same_thread=False)
    cursor = conn.cursor()
    
    # Execute query
    cursor.execute(query)
        
    # Fetch results
    results = cursor.fetchall()
    conn.close()
    
    # Step 4: Generate explanation in English
    explanation_prompt = explanation_template.format(query=query, results=results)
    ai_message = model.invoke(explanation_prompt)
    explanation = parser.parse(ai_message.content)
    return {
        "query": query,
        "results": results,
        "explanation": explanation
    }