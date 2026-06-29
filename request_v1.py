# import requests
# import json


# def graphql_request(chain, contract_address, token_id, cookies=None, timeout=30):
#     url = "https://gql.opensea.io/graphql"

#     headers = {
#         "accept": "application/graphql-response+json, application/graphql+json, application/json",
#         "origin": "https://opensea.io",
#         "referer": "https://opensea.io/",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
#         "x-app-id": "os2-web",
#         "x-graphql-operation-type": "query",
#     }

#     params = {
#         "operationName": "ItemViewModalQuery",
#         "variables": json.dumps({
#             "identifier": {
#                 "chain": chain,
#                 "contractAddress": contract_address,
#                 "tokenId": str(token_id)
#             }
#         }),
#         "extensions": json.dumps({
#             "persistedQuery": {
#                 "sha256Hash": "aed3c7d2c804ef8b872cd5892115d64bc4d911ecf330129496c32afeeb9a8189",
#                 "version": 1
#             }
#         })
#     }

#     try:
#         response = requests.get(
#             url,
#             headers=headers,
#             params=params,
#             cookies=cookies,
#             timeout=timeout
#         )

#         print("Status Code:", response.status_code)

#         if response.status_code == 200:
#             return response.text

#         print(response.text[:1000])
#         return None

#     except Exception as e:
#         print("Request Error:", e)
#         return None


import requests
import json
from concurrent.futures import ThreadPoolExecutor


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
                "tokenId": str(token_id)
            }
        }),
        "extensions": json.dumps({
            "persistedQuery": {
                "sha256Hash": "aed3c7d2c804ef8b872cd5892115d64bc4d911ecf330129496c32afeeb9a8189",
                "version": 1
            }
        })
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            cookies=cookies,
            timeout=timeout
        )

        if response.status_code == 200:
            return response.text

        print(f"Error {response.status_code}")
        return None

    except Exception as e:
        print(e)
        return None


def graphql_request_thread(data):
    """
    data = (chain, contract_address, token_id)
    """
    chain, contract_address, token_id = data
    return graphql_request(chain, contract_address, token_id)


def run_threads(request_list, max_workers=10):
    """
    request_list example:
    [
        ("ethereum","0x123","1"),
        ("ethereum","0x456","2"),
        ("polygon","0x789","3")
    ]
    """

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(graphql_request_thread, request_list))

    return results