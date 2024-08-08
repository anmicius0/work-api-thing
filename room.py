import requests
import pandas as pd

# Constants
TOKEN_URL = "https://login-p10.xiaoshouyi.com/auc/oauth2/token"
DATA_URL = "https://api-p10.xiaoshouyi.com/rest/data/v2.0/query/xoqlScroll"
PAYLOAD = {
    "grant_type": "password",
    "client_id": "bc4896f9e3e4fad682f9fe60d5fbaa2e",
    "client_secret": "3407faf39a38b6821f18cdbe019a56e3",
    "redirect_uri": "https://api.xiaoshouyi.com",
    "username": "11021054@twkd.com",
    "password": "Kevin53189fpmAUmr",
}
HEADERS = {"content-type": "application/x-www-form-urlencoded"}
XOQL_QUERY = """
    select name K大預約表編號, customItem3__c.accountName 公司名稱, customItem2__c 預約K大日期, customItem23__c.name 講解人, customItem17__c 會議室鏈接, customItem140__c K大顧問會議室連結v, customItem118__c 房間ID, customItem123__c 會議錄影連結
    from customEntity23__c
    where name = 'CYY000145128'
"""
BATCH_COUNT = 2000


def fetch_access_token():
    response = requests.post(TOKEN_URL, data=PAYLOAD)
    response.raise_for_status()
    return response.json()["access_token"]


def fetch_data(query_locator):
    data = {
        "xoql": XOQL_QUERY,
        "batchCount": BATCH_COUNT,
        "queryLocator": query_locator,
    }
    response = requests.post(DATA_URL, headers=HEADERS, data=data)
    response.raise_for_status()
    return response.json()


def main():
    # Get token and set headers
    access_token = fetch_access_token()
    HEADERS["Authorization"] = f"Bearer {access_token}"

    query_locator = ""
    contact_related = []

    while True:
        result = fetch_data(query_locator)

        records = result.get("data", {}).get("records", [])
        if not records:
            break

        contact_related.extend(records)
        print(
            pd.DataFrame(records).iloc[0]
        )  # Print the first record of the current batch

        query_locator = result.get("queryLocator")
        if not query_locator:
            break

    # Convert list of records to DataFrame
    contact_related_df = pd.DataFrame(contact_related)
    print("Total records fetched:", len(contact_related_df))


if __name__ == "__main__":
    main()
