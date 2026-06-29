import json
import mysql.connector
from urllib.parse import urlparse
from request_v1 import graphql_request


def read_product_urls():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="actowiz",   # Change if needed
        database="opensea"
    )

    cursor = conn.cursor(dictionary=True)

    query = "SELECT product_urls FROM link_table_thread"
    cursor.execute(query)

    product_urls = [row["product_urls"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return product_urls

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="actowiz",          
    database="opensea"
)

cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS opensea_items (
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


def parse_opensea_item(response_text, product_url):
    if not response_text:
        return None

    data = json.loads(response_text)

    with open("response.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    item = get_value(data, "data", "itemByIdentifier") or {}

    traits = []

    for attr in item.get("attributes", []):
        traits.append({
            "trait_type": attr.get("traitType"),
            "value": attr.get("value")
        })

    result = {
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
            "chain": get_value(item, "chain", "name")
        }
    }

    return result


def save_to_db(item):

    sql = """
    INSERT INTO opensea_items (
        item_url,
        item_id,
        item_name,
        collection_id,
        collection_name,
        collection_slug,
        owner_name,
        owner_address,
        top_offer,
        top_offer_currency,
        top_offer_usd,
        collection_floor,
        collection_floor_currency,
        collection_floor_usd,
        rarity_rank,
        rarity_category,
        rarity_total_supply,
        last_sale,
        last_sale_currency,
        last_sale_usd,
        buy_price,
        buy_currency,
        buy_price_usd,
        description,
        image_url,
        token_uri,
        contract_address,
        token_id,
        token_standard,
        chain,
        traits
    )
    VALUES (
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s,%s,%s,%s
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

        json.dumps(item.get("traits"), ensure_ascii=False)
    )

    cursor.execute(sql, values)
    conn.commit()

    print("Data inserted successfully.")


# -------------------- MAIN --------------------

# product_url = "https://opensea.io/item/ethereum/0x9c51a3cb5094b26aa1dcb380f3dc7e1a7c681c2d/8036"

# chain, contract_address, token_id = extract_identifier(product_url)

# response_text = graphql_request(
#     chain=chain,
#     contract_address=contract_address,
#     token_id=token_id
# )

# item_data = parse_opensea_item(response_text, product_url)

# if item_data:
#     save_to_db(item_data)

#     with open("data1.json", "w", encoding="utf-8") as f:
#         json.dump(item_data, f, indent=4, ensure_ascii=False)

# print("Completed Successfully.")

# cursor.close()
# conn.close()

# Read URLs from MySQL
product_urls = read_product_urls()

for product_url in product_urls:
    try:
        chain, contract_address, token_id = extract_identifier(product_url)

        response_text = graphql_request(
            chain=chain,
            contract_address=contract_address,
            token_id=token_id
        )

        item_data = parse_opensea_item(response_text, product_url)

        if item_data:
            save_to_db(item_data)

            with open("data1.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(item_data, ensure_ascii=False) + "\n")

            print(f"Completed: {product_url}")

    except Exception as e:
        print(f"Error processing {product_url}: {e}")

cursor.close()
conn.close()