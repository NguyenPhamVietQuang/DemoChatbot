
import requests
import json


def call_run_query_api(user_input):
    url = "http://127.0.0.1:8000/run_query"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "user_input": user_input
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        else:
            print(f"{response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"{e}")


def main():
    user_input = "tôi muốn đặt 2 bát Gỏi Cuốn"
    call_run_query_api(user_input)


if __name__ == "__main__":
    main()
