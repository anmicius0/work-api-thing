from quart import Quart, render_template, jsonify, request
import time
import httpx
import logging

app = Quart(__name__)

# Constants
TOKEN_URL = "https://login-p10.xiaoshouyi.com/auc/oauth2/token"
DATA_URL = "https://api-p10.xiaoshouyi.com/rest/data/v2.0/query/xoqlScroll"
ROOM_URL = "https://kd-panels.twkd.com/room/"
TOKEN_PAYLOAD = {
    "grant_type": "password",
    "client_id": "bc4896f9e3e4fad682f9fe60d5fbaa2e",
    "client_secret": "3407faf39a38b6821f18cdbe019a56e3",
    "redirect_uri": "https://api.xiaoshouyi.com",
    "username": "11021054@twkd.com",
    "password": "Kevin53189fpmAUmr",
}
HEADERS = {"content-type": "application/x-www-form-urlencoded"}
XOQL_QUERY_TEMPLATE = """
    select name K大預約表編號, customItem3__c.accountName 公司名稱, customItem2__c 預約K大日期, customItem23__c.name 講解人, customItem17__c 會議室鏈接, customItem140__c K大顧問會議室連結v, customItem118__c 房間ID, customItem123__c 會議錄影連結
    from customEntity23__c
    where {condition}
"""

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global variables for token caching
cached_token = None
token_expiry = 0
TOKEN_TTL = 3600


async def fetch_token(client):
    """Retrieve access token."""
    global cached_token, token_expiry
    try:
        response = await client.post(TOKEN_URL, data=TOKEN_PAYLOAD)
        response.raise_for_status()
        content = response.json()
        cached_token = content.get("access_token")
        token_expiry = time.time() + TOKEN_TTL
        logger.debug(f"Token fetched: {cached_token}")
        return cached_token
    except httpx.RequestError as e:
        logger.error(f"Failed to retrieve access token: {e}")
        return None


async def get_token():
    """Return a valid access token, fetching a new one if necessary."""
    global cached_token, token_expiry
    async with httpx.AsyncClient() as client:
        if cached_token and time.time() < token_expiry:
            logger.debug("Using cached token")
            return cached_token
        logger.debug("Fetching new token")
        return await fetch_token(client)


def stamp(num):
    """Convert timestamp to formatted datetime string."""
    try:
        num = int(num / 1000)
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(num))
    except (TypeError, ValueError):
        return "error"


def process_participants(participants):
    """Process participants, which can be a dict or list."""
    if isinstance(participants, dict):
        return {
            name: {
                "online_time": stamp(info.get("online")),
                "offline_time": stamp(info.get("offline")),
            }
            for name, info in participants.items()
        }
    elif isinstance(participants, list):
        return {
            participant.get("name"): {
                "online_time": stamp(participant.get("online")),
                "offline_time": stamp(participant.get("offline")),
            }
            for participant in participants
        }
    return {}


@app.route("/")
async def index():
    """Render the index page."""
    return await render_template("index.html")


@app.route("/test-speaker", methods=["POST"])
async def testSpeaker():
    """Handle order request and fetch related data."""
    token = await get_token()
    if not token:
        return (
            jsonify({"success": False, "error": "Failed to retrieve access token"}),
            500,
        )

    query = XOQL_QUERY_TEMPLATE.format(condition="customItem23__c.name = '陳泓愷'")
    data = {"xoql": query, "batchCount": 2000, "queryLocator": ""}
    headers = {"Authorization": f"Bearer {token}", **HEADERS}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(DATA_URL, headers=headers, data=data)
            response.raise_for_status()
            unique_speakers = {
                record["講解人"] for record in response.json()["data"]["records"]
            }
            return jsonify(list(unique_speakers))
        except httpx.RequestError as e:
            logger.error(f"Failed to retrieve data: {e}")
            return jsonify({"success": False, "error": "Failed to retrieve data"}), 500


@app.route("/someone", methods=["POST"])
async def someone():
    """Handle someone request."""
    token = await get_token()
    if not token:
        return (
            jsonify({"success": False, "error": "Failed to retrieve access token"}),
            500,
        )

    data = await request.get_json()
    someone = data.get("name")
    query = XOQL_QUERY_TEMPLATE.format(condition=f"customItem23__c.name = '{someone}'")
    data = {"xoql": query, "batchCount": 2000, "queryLocator": ""}
    headers = {"Authorization": f"Bearer {token}", **HEADERS}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(DATA_URL, headers=headers, data=data)
            response.raise_for_status()
            raw_data = response.json()
            return jsonify(raw_data)
        except httpx.RequestError as e:
            logger.error(f"Failed to retrieve data: {e}")
            return jsonify({"success": False, "error": "Failed to retrieve data"}), 500


@app.route("/someroom", methods=["POST"])
async def someroom():
    """Handle someroom request."""
    data = await request.get_json()
    someroom = data.get("roomID")

    async with httpx.AsyncClient() as client:
        try:
            room_url = f"{ROOM_URL}{someroom}"
            response = await client.get(room_url)
            response.raise_for_status()
            room_data = response.json()

            return jsonify(
                {
                    "teachers": process_participants(
                        room_data["data"].get("teachers", [])
                    ),
                    "students": process_participants(
                        room_data["data"].get("students", [])
                    ),
                    "records": [
                        {
                            "url": (
                                rec["recordDetails"][0]["url"]
                                if rec.get("recordDetails")
                                else None
                            ),
                            "start_time": (
                                rec["startTime"] if rec.get("startTime") else None
                            ),
                            "end_time": rec["endTime"] if rec.get("endTime") else None,
                        }
                        for rec in room_data["data"].get("records", [])
                    ],
                }
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to retrieve data: {e}")
            return jsonify({"success": False, "error": "Failed to retrieve data"}), 500


if __name__ == "__main__":
    app.run(port=5050, debug=True)
