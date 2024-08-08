import requests

API_URL = "https://kd-panels.twkd.com/room/"
ROOM_UUID = "30c12fe0d72a4872b7af83cabb4cac09"
URL = API_URL + ROOM_UUID


def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"status: {response.status_code}")
        return None


def process_data(data):
    teachers = data["data"]["teachers"]
    records = data["data"]["records"]

    for idx, (teacher, record) in enumerate(zip(teachers.items(), records), start=1):
        teacher_name, teacher_info = teacher
        print(f"teacher{idx} name: {teacher_name}")

        intime = teacher_info["online"]
        outtime = teacher_info["offline"]
        print(f"人物進入時間: {intime}")
        print(f"人物離開時間: {outtime}")

        record_details = record["recordDetails"][0]
        print(f"fileName: {record_details['fileName']}")
        print(f"url: {record_details['url']}")

        intime = record["startTime"]
        outtime = record["endTime"]
        print(f"錄影開始時間: {intime}")
        print(f"錄影結束時間: {outtime}")


def main():
    data = fetch_data(URL)
    if data:
        process_data(data)


if __name__ == "__main__":
    main()
