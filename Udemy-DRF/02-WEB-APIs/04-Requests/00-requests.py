import requests


def main():
    response = requests.get("http://www.google.com")
    print(f'Status Code: {response.status_code}')


if __name__ == "__main__":
    main()
