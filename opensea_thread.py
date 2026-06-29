import requests
import mysql.connector
import json
import urllib.parse
import jmespath
from concurrent.futures import ThreadPoolExecutor


conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="actowiz",
    database="opensea"
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS link_table_thread(
    ID INT AUTO_INCREMENT PRIMARY KEY,
    COLLECTION_NAME VARCHAR(255),
    IS_VERIFIED VARCHAR(100),
    TOKEN_STANDARD VARCHAR(100),
    TOTAL_ITEMS VARCHAR(100),
    MINT_DATE VARCHAR(255),
    COLLECTION_URL VARCHAR(500),
    LISTED_NAME VARCHAR(255),
    TOKEN_ID VARCHAR(255),
    PRODUCT_URLS VARCHAR(455) UNIQUE,
    STATUS BOOLEAN DEFAULT 0,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()


cookies = {
    "os2AccessEx": "Wdr6yywSUvHzIWYeBybn17MOdxKRbbhM",
}

headers = {
    "accept": "application/json",
    "origin": "https://opensea.io",
    "referer": "https://opensea.io/",
    "user-agent": "Mozilla/5.0",
    "x-app-id": "os2-web",
    "x-graphql-operation-type": "query",
}



def insert_records(records):

    if not records:
        return

    query = """
    INSERT IGNORE INTO link_table_thread(
        COLLECTION_NAME,
        IS_VERIFIED,
        TOKEN_STANDARD,
        TOTAL_ITEMS,
        MINT_DATE,
        COLLECTION_URL,
        LISTED_NAME,
        TOKEN_ID,
        PRODUCT_URLS
    )
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.executemany(query, records)
    conn.commit()

    print("Inserted :", cursor.rowcount)



next_cursor = None

while True:

    variables = {
        "collectionSlug": "gorgez",
        "limit": 100,
        "sort": {
            "by": "PRICE",
            "direction": "ASC"
        }
    }

    if next_cursor:
        variables["after"] = next_cursor

    extensions = {
        "persistedQuery": {
            "sha256Hash": "8d6097806a0bae439d1c970077189c321c4e1efe9f40ec14b7e431b470dd8ac5",
            "version": 1
        }
    }

    url = (
        "https://gql.opensea.io/graphql?"
        "operationName=CollectionItemsListQuery&"
        f"variables={urllib.parse.quote(json.dumps(variables))}&"
        f"extensions={urllib.parse.quote(json.dumps(extensions))}"
    )

    response = requests.get(
        url,
        headers=headers,
        cookies=cookies
    )

    print(response.status_code)

    if response.status_code != 200:
        break

    data = response.json()

    items = jmespath.search(
        "data.collectionItems.items",
        data
    ) or []

    records = []

    for item in items:

        collection_name = jmespath.search("collection.slug", item) or "gorgez"

        is_verified = str(
            jmespath.search("collection.owner.isVerified", item)
        )

        token_standard = jmespath.search(
            "chain.identifier",
            item
        )

        total_items = str(
            jmespath.search("rarity.totalSupply", item)
        )

        mint_date = jmespath.search(
            "bestListing.startTime",
            item
        )

        listed_name = jmespath.search(
            "name",
            item
        )

        identifier = jmespath.search(
            "chain.identifier",
            item
        )

        contract = jmespath.search(
            "contractAddress",
            item
        )

        token = jmespath.search(
            "tokenId",
            item
        )

        if identifier and contract and token:

            product_url = (
                f"https://opensea.io/item/"
                f"{identifier}/{contract}/{token}"
            )

            print(product_url)

            records.append((
                collection_name,
                is_verified,
                token_standard,
                total_items,
                mint_date,
                f"https://opensea.io/collection/{collection_name}",
                listed_name,
                token,
                product_url
            ))

    insert_records(records)

    next_cursor = jmespath.search(
        "data.collectionItems.nextPageCursor",
        data
    )

    print("Next Cursor :", next_cursor)

    if not next_cursor:
        break

print("Completed")

cursor.close()
conn.close()