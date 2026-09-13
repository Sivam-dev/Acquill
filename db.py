import psycopg

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "learner",
    "password": "learner_pass",
    "dbname": "learningtrack"
}

def get_connection():
    return psycopg.connect(**DB_CONFIG)

def run_query(query, params=None, fetch=False):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            else:
                conn.commit()
                return None


