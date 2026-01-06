import os
import requests
import mysql.connector

# === ENV SETUP ===
EMAIL = os.getenv("METABASE_EMAIL")
PASSWORD = os.getenv("METABASE_PASSWORD")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "10110"))
MYSQL_USER = os.getenv("MYSQL_USER", "hanayo_prod_4cHWso1s")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "RCf{3YerJMh;[{lnU8}0YDJaE2mDP9tqs7CV?sdD5")
MYSQL_DB = os.getenv("MYSQL_DB", "hanayo_prod")  # ← change this to your actual DB

# === METABASE FUNCTIONS (READ ONLY) ===
def get_metabase_credentials():
    return (
        os.getenv("METABASE_EMAIL"),
        os.getenv("METABASE_PASSWORD"),
        os.getenv("METABASE_URL"),
    )

def metabase_insert_links(links: list[str]):
    """Insert new links into the database via Metabase API, ignoring duplicates."""
    if not links:
        return {"status": "no_links"}

    email, password, base_url = get_metabase_credentials()

    # Login
    session_resp = requests.post(
        f"{base_url}/api/session",
        json={"username": email, "password": password}
    )
    session_resp.raise_for_status()
    session_token = session_resp.json()["id"]

    # Prepare SQL values
    values = ", ".join(f"('{link}')" for link in links)
    query = f"""
        CREATE TABLE IF NOT EXISTS links (
            id INT AUTO_INCREMENT PRIMARY KEY,
            link VARCHAR(255) UNIQUE,
            likes INT DEFAULT 0,
            comments INT DEFAULT 0,
            views INT DEFAULT 0,
            shares INT DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        INSERT IGNORE INTO links (link) VALUES {values};
    """

    # Execute query via Metabase
    resp = requests.post(
        f"{base_url}/api/dataset",
        headers={"X-Metabase-Session": session_token},
        json={
            "database": 4,  # adjust to your Metabase DB ID
            "type": "native",
            "native": {"query": query},
            "display": "table",
            "visualization_settings": {},
        },
    )
    resp.raise_for_status()

    return {"status": "inserted", "count": len(links), "links": links}

def metabase_get_links():
    """Query Metabase API and return rows of links to scrape."""
    email, password, base_url = get_metabase_credentials()
    
    # 1. Login
    login_url = f"{base_url}/api/session"
    login_data = {"username": email, "password": password}
    resp = requests.post(login_url, json=login_data)
    resp.raise_for_status()
    session_token = resp.json()["id"]

   
    query_payload = {
        "database": 4,
        "type": "native",
        "native": {
            "query": """
                SELECT *
                    FROM links
                    WHERE update_quota > 0
                    AND (updated_at < NOW() - INTERVAL 3 DAY OR update_quota=3)
                    AND link NOT IN (SELECT link FROM link_locks)
                    ORDER BY updated_at ASC
                LIMIT 5;

            """
        },
        "display": "table",
        "visualization_settings": {},
    }

    

    # 3. Send query
    dataset_url = f"{base_url}/api/dataset"
    headers = {"X-Metabase-Session": session_token}
    response = requests.post(dataset_url, json=query_payload, headers=headers)
    response.raise_for_status()

    # 4. Extract rows
    result = response.json()
    cols = [c["name"] for c in result["data"]["cols"]]
    rows = [dict(zip(cols, row)) for row in result["data"]["rows"]]

    return rows

def metabase_get_post_links(links: list[str]):
    """Fetch link details from Metabase for a given list of links."""
    if not links:
        return []

    email, password, base_url = get_metabase_credentials()

    # 1. Login
    session_resp = requests.post(
        f"{base_url}/api/session",
        json={"username": email, "password": password}
    )
    session_resp.raise_for_status()
    session_token = session_resp.json()["id"]

    # 2. Build SQL query safely
    formatted_links = ", ".join([f"'{link}'" for link in links])
    query = f"""
        SELECT *
        FROM links
        WHERE link IN ({formatted_links});
    """

    # 3. Query Metabase dataset API
    dataset_resp = requests.post(
        f"{base_url}/api/dataset",
        headers={"X-Metabase-Session": session_token},
        json={
            "database": 4,
            "type": "native",
            "native": {"query": query},
            "display": "table",
            "visualization_settings": {},
        },
    )
    dataset_resp.raise_for_status()

    # 4. Extract and structure results
    result = dataset_resp.json()
    cols = [c["name"] for c in result["data"]["cols"]]
    rows = [dict(zip(cols, row)) for row in result["data"]["rows"]]

    return rows


# === METABASE WRITE FUNCTIONS ===
def metabase_lock_links(links: list[str]):
    """Insert lock entries into link_locks via Metabase API."""
    if not links:
        return {"status": "no_links"}
    
    email, password, base_url = get_metabase_credentials()
    
    # Login
    session_resp = requests.post(
        f"{base_url}/api/session",
        json={"username": email, "password": password}
    )
    session_resp.raise_for_status()
    session_token = session_resp.json()["id"]
    
    # Build SQL
    values = ", ".join(f"('{link}', NOW())" for link in links)
    query = f"INSERT IGNORE INTO link_locks (link, locked_at) VALUES {values};"
    
    # Execute via Metabase
    resp = requests.post(
        f"{base_url}/api/dataset",
        headers={"X-Metabase-Session": session_token},
        json={
            "database": 4,  # change to your DB id in Metabase
            "type": "native",
            "native": {"query": query},
            "display": "table",
            "visualization_settings": {},
        },
    )
    resp.raise_for_status()
    return {"status": "locked", "count": len(links), "links": links}


def metabase_unlock_links(links: list[str]):
    """Remove locks from link_locks via Metabase API."""
    if not links:
        return {"status": "no_links"}
    
    email, password, base_url = get_metabase_credentials()
    
    # Login
    session_resp = requests.post(
        f"{base_url}/api/session",
        json={"username": email, "password": password}
    )
    session_resp.raise_for_status()
    session_token = session_resp.json()["id"]
    
    links_str = ", ".join(f"'{link}'" for link in links)
    query = f"DELETE FROM link_locks WHERE link IN ({links_str});"
    
    resp = requests.post(
        f"{base_url}/api/dataset",
        headers={"X-Metabase-Session": session_token},
        json={
            "database": 4,
            "type": "native",
            "native": {"query": query},
            "display": "table",
            "visualization_settings": {},
        },
    )
    resp.raise_for_status()
    return {"status": "unlocked", "count": len(links), "links": links}


def metabase_update_links(results: list[dict]):
    """Update metrics for links via Metabase API."""
    if not results:
        return {"status": "no_results"}
    
    email, password, base_url = get_metabase_credentials()
    
    # Login
    session_resp = requests.post(
        f"{base_url}/api/session",
        json={"username": email, "password": password}
    )
    session_resp.raise_for_status()
    session_token = session_resp.json()["id"]
    
    for r in results:
        link = r["link"]
        likes = r.get("likes") or 0
        comments = r.get("comments") or 0
        views = r.get("views") or 0
        shares = r.get("shares") or 0
        query = f"""
            UPDATE links
            SET likes = {likes}, comments = {comments}, views = {views}, shares = {shares},
                updated_at = NOW(), update_quota = update_quota - 1
            WHERE link = '{link}';
        """
        requests.post(
            f"{base_url}/api/dataset",
            headers={"X-Metabase-Session": session_token},
            json={
                "database": 4,
                "type": "native",
                "native": {"query": query},
                "display": "table",
                "visualization_settings": {},
            },
        )
    
    return {"status": "updated", "count": len(results)}

# === VANILLA SQL FUNCTIONS (WRITE) ===
def vanilla_lock_links(links: list[str]):
    """Directly insert lock entries into link_locks using MySQL connector."""
    if not links:
        return {"status": "no_links"}

    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST.split(":")[0],
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
        )
        cursor = conn.cursor()

        values = ", ".join(f"('{link}', NOW())" for link in links)
        sql = f"INSERT IGNORE INTO link_locks (link, locked_at) VALUES {values};"
        cursor.execute(sql)
        conn.commit()

        return {"status": "locked", "count": len(links), "links": links}

    except mysql.connector.Error as err:
        return {"status": "error", "error": str(err)}

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def vanilla_get_order_ids_cogs(orderIds: list[str]):
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST.split(":")[0],
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
        )
        cursor = conn.cursor(dictionary=True)
        formatted_links = ", ".join([f"'{i}'" for i in orderIds])

        sql = f"""
            SELECT order_id, total_price + remaining + shipping_fee as cogs
            FROM orders
            WHERE order_id IN ({formatted_links});
        """

        cursor.execute(sql)
        rows = cursor.fetchall()

        return rows
    
    except mysql.connector.Error as err:
        return {
            "status": "error",
            "error": str(err)
        }

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def vanilla_get_post_links(links: list[str]):
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST.split(":")[0],
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
        )
        cursor = conn.cursor(dictionary=True)
        formatted_links = ", ".join([f"'{link}'" for link in links])

        sql = f"""
            SELECT *
            FROM links
            WHERE link IN ({formatted_links});
        """

        cursor.execute(sql)
        rows = cursor.fetchall()

        return rows

    except mysql.connector.Error as err:
        return {
            "status": "error",
            "error": str(err)
        }

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def vanilla_get_links():
    """Directly select links from MySQL based on scraping rules."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST.split(":")[0],
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
        )
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT *
            FROM links
            WHERE update_quota > 0
              AND (updated_at < NOW() - INTERVAL 3 DAY OR update_quota = 3)
              AND link NOT IN (SELECT link FROM link_locks)
            ORDER BY updated_at ASC
            LIMIT 5;
        """

        cursor.execute(sql)
        rows = cursor.fetchall()

        return rows

    except mysql.connector.Error as err:
        return {
            "status": "error",
            "error": str(err)
        }

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def vanilla_unlock_links(links: list[str]):
    """Remove locks from link_locks table using vanilla MySQL."""
    if not links:
        return {"status": "no_links"}

    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST.split(":")[0],
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
        )
        cursor = conn.cursor()

        links_str = ", ".join(f"'{link}'" for link in links)
        sql = f"DELETE FROM link_locks WHERE link IN ({links_str});"
        cursor.execute(sql)
        conn.commit()

        return {"status": "unlocked", "count": len(links), "links": links}

    except mysql.connector.Error as err:
        return {"status": "error", "error": str(err)}

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def vanilla_update_links(results: list[dict]):
    """Update scraped metrics (likes, comments, views, shares) into the links table."""
    if not results:
        return {"status": "no_results"}

    conn = mysql.connector.connect(
            host=MYSQL_HOST.split(":")[0],
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
        )
    cursor = conn.cursor()

    update_query = """
        UPDATE links
        SET likes = %s, comments = %s, views = %s, shares = %s, updated_at = NOW(),update_quota = update_quota - 1
        WHERE link = %s
    """

    data = [
        (
            r.get("likes") or 0,
            r.get("comments") or 0,
            r.get("views") or 0,
            r.get("shares") or 0,
            r["link"],
        )
        for r in results
    ]

    cursor.executemany(update_query, data)
    conn.commit()

    affected = cursor.rowcount
    cursor.close()
    conn.close()

    return {"status": "updated", "count": affected}

def vanilla_insert_links(links: list[str]):
    """Insert new links into the database, ignoring duplicates."""
    if not links:
        return {"status": "no_links"}

    conn = mysql.connector.connect(
        host=MYSQL_HOST.split(":")[0],
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
    )
    cursor = conn.cursor()

    # Ensure the table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INT AUTO_INCREMENT PRIMARY KEY,
            link VARCHAR(255) UNIQUE,
            likes INT DEFAULT 0,
            comments INT DEFAULT 0,
            views INT DEFAULT 0,
            shares INT DEFAULT 0,
            update_quota INT DEFAULT 3,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    insert_query = """
        INSERT IGNORE INTO links (link)
        VALUES (%s)
    """

    cursor.executemany(insert_query, [(l,) for l in links])
    conn.commit()

    affected = cursor.rowcount
    cursor.close()
    conn.close()

    return {"status": "inserted", "count": affected}