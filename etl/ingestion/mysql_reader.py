import os
from mysql.connector import connect


def connect_mysql():
    return connect(
        host=os.environ.get('MYSQL_HOST', 'internal-mysql.company.internal'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER', 'readonly_client'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        database=os.environ.get('MYSQL_DATABASE', 'main_db'),
        read_default_file='~/.my.cnf'
    )


def fetch_entities(limit: int = 5000, offset: int = 0) -> list[dict]:
    """Fetch records from internal MySQL as dicts."""
    conn = connect_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name, description, created_at, updated_at
        FROM entities
        WHERE status = 'active'
        ORDER BY updated_at DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def get_mysql_last_updated() -> str | None:
    """Get timestamp of most recent record update."""
    conn = connect_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(updated_at) FROM entities WHERE status = 'active'")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0].isoformat() if result and result[0] else None