from database import get_connection

def save_chat_to_db(query, answer):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ChatHistory (UserQuery, BotResponse)
        VALUES (?, ?)
    """, (query, answer))

    conn.commit()
    conn.close()


def fetch_chat_history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT ID, UserQuery, BotResponse, CreatedAt FROM ChatHistory ORDER BY ID DESC")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "query": row[1],
            "response": row[2],
            "timestamp": str(row[3])
        }
        for row in rows
    ]
