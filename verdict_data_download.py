import os
import requests
import json


## Setting up the vector database connections
os.environ["MYSCALE_HOST"] = "msc-43065d8c.us-east-1.aws.myscale.com"
os.environ["MYSCALE_PORT"] = "443"
os.environ["MYSCALE_USERNAME"] = "steven_org_default"
os.environ["MYSCALE_PASSWORD"] = "passwd_s3vsWNIlSeZLmC"


## Download verdict data
def get_member_token(member_account, password):
    # API endpoint URL
    url = "https://opendata.judicial.gov.tw/api/MemberTokens"

    # HTTP headers
    headers = {
        "Content-Type": "application/json"
    }

    # Request body with member credentials
    body = {
        "memberAccount": member_account,
        "pwd": password
    }

    try:
        # Make HTTP POST request to get the token
        response = requests.post(url, headers=headers, data=json.dumps(body))
        response.raise_for_status()  # Raise an error if the request fails
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None

    # Parse JSON response
    response_data = response.json()

    # Check if succeeded
    if "token" in response_data:
        print("Token received successfully.")
        return response_data["token"], response_data["expires"]
    else:
        print(f"Failed to get token: {response_data.get('message', 'Unknown error')}")
        return None

def query_datasets(token, api_url):
    # HTTP headers including Authorization header
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        # Make HTTP GET request to a protected API
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an error if the request fails
    except requests.exceptions.RequestException as e:
        print(f"Error during protected API request: {e}")
        return None

    # Parse JSON response
    response_data = response.json()
    # print("Protected API response:", response_data)
    return response_data

def download_file(token, file_set_id, save_path):
    file_download_url = f"https://opendata.judicial.gov.tw/api/FilesetLists/{file_set_id}/file"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.get(file_download_url, headers=headers, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error during file download request: {e}")
        return False

    # Save the file to the specified path
    with open(save_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
    print(f"File downloaded successfully: {save_path}")
    return True

if __name__ == "__main__":
    # Replace these with your actual member account credentials
    member_account = "coolboy371"
    password = "coolboy173"

    # Step 3-1: Get member token
    token_info = get_member_token(member_account, password)
    if token_info:
        token, expires = token_info
        print(f"Token: {token}\nExpires: {expires}")

        api_url = "https://opendata.judicial.gov.tw/data/api/rest/categories/051/resources"
        datasets = query_datasets(token, api_url)
        
        if not datasets:
            print("No datasets found.")
            exit(1)

        # Download
        download_directory = "data/"
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)

        for dataset in datasets:
            for fileset in dataset.get("filesets", []):
                file_set_id = fileset["fileSetId"]
                file_name = f"{file_set_id}.{fileset['resourceFormat'].lower()}"
                save_path = os.path.join(download_directory, file_name)
                download_file(token, file_set_id, save_path)
    else:
        print("Unable to retrieve token.")
