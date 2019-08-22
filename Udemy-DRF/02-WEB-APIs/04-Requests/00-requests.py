import requests


def main():
    response = requests.get("http://www.google.com")
    print(f'Status Code: {response.status_code}')
    print(f'Headers: {response.headers}')
    print(f'Content: {response.text}')

if __name__ == "__main__":
    main()


# https://api.exchangeratesapi.io/latest