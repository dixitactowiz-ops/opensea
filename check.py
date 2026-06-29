import json
import os
from concurrent.futures import ThreadPoolExecutor
import threading
from urllib.parse import urlparse
import mysql.connector
from mysql.connector import pooling
import requests
import hashlib
import argparse  # Added for multi-terminal argument handling

PAGE_SAVE_PATH = r"D:\pagesave\opensea"
os.makedirs(PAGE_SAVE_PATH, exist_ok=True)

file_lock = threading.Lock()

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "actowiz",  # Change if needed
    "database": "opensea",
}

try:
    # 10 connections per terminal instance is safe and efficient
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="opensea_pool", pool_size=10, **DB_CONFIG
    )
except mysql.connector.Error as err:
    print(f"Error creating connection pool: {err}")
    exit(1)

def save_page(product_url, response_text):
    try:
        # Create hash from product URL
        hash_name = hashlib.md5(product_url.encode("utf-8")).hexdigest()
        file_path = os.path.join(PAGE_SAVE_PATH, f"{hash_name}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response_text)

        return file_path
    except Exception as e:
        print(f"Page Save Error: {e}")
        return None


def setup_database():
    """Initializes the database table if it doesn't exist."""
    conn = db_pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS opensea_items_check (
        id INT AUTO_INCREMENT PRIMARY KEY,
        item_url TEXT,
        item_id VARCHAR(255),
        item_name TEXT,
        collection_id VARCHAR(255),
        collection_name TEXT,
        collection_slug VARCHAR(255),
        owner_name TEXT,
        owner_address VARCHAR(255),
        top_offer DECIMAL(30,10),
        top_offer_currency VARCHAR(50),
        top_offer_usd DECIMAL(30,10),
        collection_floor DECIMAL(30,10),
        collection_floor_currency VARCHAR(50),
        collection_floor_usd DECIMAL(30,10),
        rarity_rank INT,
        rarity_category VARCHAR(100),
        rarity_total_supply INT,
        last_sale DECIMAL(30,10),
        last_sale_currency VARCHAR(50),
        last_sale_usd DECIMAL(30,10),
        buy_price DECIMAL(30,10),
        buy_currency VARCHAR(50),
        buy_price_usd DECIMAL(30,10),
        description LONGTEXT,
        image_url TEXT,
        token_uri TEXT,
        contract_address VARCHAR(255),
        token_id VARCHAR(255),
        token_standard VARCHAR(100),
        chain VARCHAR(100),
        traits JSON
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()


def read_product_urls():
    """Fetches target URLs from the tracking table."""
    conn = db_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT product_urls
    FROM link_table_thread
    WHERE status = 0
    """
    cursor.execute(query)
    product_urls = [row["product_urls"] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return product_urls


def extract_identifier(product_url):
    parts = urlparse(product_url).path.strip("/").split("/")
    return parts[1], parts[2], parts[3]


def get_value(data, *keys):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def graphql_request(chain, contract_address, token_id, cookies=None, timeout=30):
    url = "https://gql.opensea.io/graphql"
    headers = {
        "accept": "application/graphql-response+json, application/graphql+json, application/json",
        "origin": "https://opensea.io",
        "referer": "https://opensea.io/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-app-id": "os2-web",
        "x-graphql-operation-type": "query",
    }
    params = {
        "operationName": "ItemViewModalQuery",
        "variables": json.dumps({
            "identifier": {
                "chain": chain,
                "contractAddress": contract_address,
                "tokenId": str(token_id),
            }
        }),
        "extensions": json.dumps({
            "persistedQuery": {
                "sha256Hash": "aed3c7d2c804ef8b872cd5892115d64bc4d911ecf330129496c32afeeb9a8189",
                "version": 1,
            }
        }),
    }
    try:
        response = requests.get(
            url, headers=headers, params=params, cookies=cookies, timeout=timeout
        )
        if response.status_code == 200:
            return response.text
        print(f"GraphQL Error Status Code: {response.status_code}")
        return None
    except Exception as e:
        print(f"Request Exception: {e}")
        return None


def parse_opensea_item(response_text, product_url):
    if not response_text:
        return None

    data = json.loads(response_text)
    item = get_value(data, "data", "itemByIdentifier") or {}

    traits = [
        {"trait_type": attr.get("traitType"), "value": attr.get("value")}
        for attr in item.get("attributes", [])
    ]

    return {
        "item_url": product_url,
        "item_id": item.get("id"),
        "item_name": item.get("name"),
        "collection_id": get_value(item, "collection", "id"),
        "collection_name": get_value(item, "collection", "name"),
        "collection_slug": get_value(item, "collection", "slug"),
        "owner_name": get_value(item, "owner", "displayName"),
        "owner_address": get_value(item, "owner", "address"),
        "top_offer": get_value(item, "bestOffer", "pricePerItem", "token", "unit"),
        "top_offer_currency": get_value(item, "bestOffer", "pricePerItem", "token", "symbol"),
        "top_offer_usd": get_value(item, "bestOffer", "pricePerItem", "usd"),
        "collection_floor": get_value(item, "collection", "floorPrice", "pricePerItem", "token", "unit"),
        "collection_floor_currency": get_value(item, "collection", "floorPrice", "pricePerItem", "token", "symbol"),
        "collection_floor_usd": get_value(item, "collection", "floorPrice", "pricePerItem", "usd"),
        "rarity_rank": get_value(item, "rarity", "rank"),
        "rarity_category": get_value(item, "rarity", "category"),
        "rarity_total_supply": get_value(item, "rarity", "totalSupply"),
        "last_sale": get_value(item, "lastSale", "token", "unit"),
        "last_sale_currency": get_value(item, "lastSale", "token", "symbol"),
        "last_sale_usd": get_value(item, "lastSale", "usd"),
        "buy_price": get_value(item, "bestListing", "pricePerItem", "token", "unit"),
        "buy_currency": get_value(item, "bestListing", "pricePerItem", "token", "symbol"),
        "buy_price_usd": get_value(item, "bestListing", "pricePerItem", "usd"),
        "description": item.get("description"),
        "image_url": item.get("imageUrl"),
        "token_uri": item.get("tokenUri"),
        "traits": traits,
        "blockchain_details": {
            "contract_address": item.get("contractAddress"),
            "token_id": item.get("tokenId"),
            "token_standard": item.get("standard"),
            "chain": get_value(item, "chain", "name"),
        },
    }


def save_to_db(item):
    """Saves a single processed item using a thread pool connection."""
    sql = """
    INSERT INTO opensea_items_check (
        item_url, item_id, item_name, collection_id, collection_name, collection_slug,
        owner_name, owner_address, top_offer, top_offer_currency, top_offer_usd,
        collection_floor, collection_floor_currency, collection_floor_usd,
        rarity_rank, rarity_category, rarity_total_supply, last_sale, last_sale_currency, last_sale_usd,
        buy_price, buy_currency, buy_price_usd, description, image_url, token_uri,
        contract_address, token_id, token_standard, chain, traits
    )
    VALUES (
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
    )
    """
    values = (
        item.get("item_url"),
        item.get("item_id"),
        item.get("item_name"),
        item.get("collection_id"),
        item.get("collection_name"),
        item.get("collection_slug"),
        item.get("owner_name"),
        item.get("owner_address"),
        item.get("top_offer"),
        item.get("top_offer_currency"),
        item.get("top_offer_usd"),
        item.get("collection_floor"),
        item.get("collection_floor_currency"),
        item.get("collection_floor_usd"),
        item.get("rarity_rank"),
        item.get("rarity_category"),
        item.get("rarity_total_supply"),
        item.get("last_sale"),
        item.get("last_sale_currency"),
        item.get("last_sale_usd"),
        item.get("buy_price"),
        item.get("buy_currency"),
        item.get("buy_price_usd"),
        item.get("description"),
        item.get("image_url"),
        item.get("token_uri"),
        item["blockchain_details"].get("contract_address"),
        item["blockchain_details"].get("token_id"),
        item["blockchain_details"].get("token_standard"),
        item["blockchain_details"].get("chain"),
        json.dumps(item.get("traits"), ensure_ascii=False),
    )

    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Database error writing item: {err}")


def update_status(product_url):
    """Update scraped status to 1 after successful processing."""
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        sql = """
        UPDATE link_table_thread
        SET status = 1
        WHERE product_urls = %s
        """
        cursor.execute(sql, (product_url,))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Status Update Error: {err}")


def process_url(product_url):
    """The task executed by each thread worker."""
    try:
        chain, contract_address, token_id = extract_identifier(product_url)
        response_text = graphql_request(chain, contract_address, token_id)
        if response_text:
            save_page(product_url, response_text)
        item_data = parse_opensea_item(response_text, product_url)
        
        if item_data:
            save_to_db(item_data)
            update_status(product_url)

            # Thread-safe appending to data1.json
            with file_lock:
                with open("data1.json", "a", encoding="utf-8") as f:
                    f.write(json.dumps(item_data, ensure_ascii=False) + "\n")
            print(f"Completed: {product_url}")

    except Exception as e:
        print(f"Error processing {product_url}: {e}")


if __name__ == "__main__":
    # 1. Ensure DB setups are checked
    setup_database()

    # 2. Configure arguments passed from the batch file
    parser = argparse.ArgumentParser(description="Multi-terminal OpenSea Scraper Worker")
    parser.add_argument("--worker_id", type=int, default=0, help="Unique index of this terminal instance")
    parser.add_argument("--total_workers", type=int, default=1, help="Total number of running terminal windows")
    args = parser.parse_args()

    # 3. Pull all non-scraped target URLs
    all_urls = read_product_urls()
    
    # 4. Filter work uniquely for this terminal instance using modulo tracking
    urls_to_scrape = [
        url for i, url in enumerate(all_urls) 
        if i % args.total_workers == args.worker_id
    ]

    print(f"==================================================")
    print(f" STARTING TERMINAL WORKER: {args.worker_id + 1} / {args.total_workers}")
    print(f" Assigned Workload: {len(urls_to_scrape)} URLs")
    print(f"==================================================")

    # 5. Execute threaded mapping per terminal setup (Max 10 threads per window to keep MySQL happy)
    MAX_WORKERS = 5

    if urls_to_scrape:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            executor.map(process_url, urls_to_scrape)

    print(f"\nWorker {args.worker_id + 1} has completely finished its batch queue.")