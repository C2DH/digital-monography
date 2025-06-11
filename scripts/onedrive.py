# requirements.txt
# # OneDrive integration
# msal==1.32.*

####
# This worked, but I hit "tenant does not have a SPO license" error.


import msal
import requests

app_name = "dgt-mon-personal-app-only-access"
app_id = "c2a027e0-06c1-45e9-9179-47b34b1c5348"
obj_id = "ceb946ac-d731-4378-adc3-3b7b5c0c83c1"
dir_id = "bc1c2255-9fb1-4fb3-a8df-8276315ca45b"
secret_val = "nG78Q~E5PW3XnnjJTUJi8KTer0fudEzJg7EIbceE"
secret_id = "451eb289-2f92-4b35-b163-b75a72ddc007"

scopes = [
    "https://graph.microsoft.com/.default",
]
url = "https://graph.microsoft.com/v1.0"


app = msal.ConfidentialClientApplication(
    client_id=app_id,
    client_credential=secret_val,
    authority=f"https://login.microsoftonline.com/{dir_id}",
)

result = app.acquire_token_silent(
    scopes=scopes,
    account=None,
)

if not result:
    result = app.acquire_token_for_client(scopes=scopes)


headers = {
    "Authorization": f"Bearer {result['access_token']}",
    "Content-Type": "application/json",
}

user_id = ""
# r = requests.get(url=f"{url}/users/{user_id}/drive/root/children", headers=headers).json()
# r = requests.get(url=f"{url}/users/{user_id}/drives", headers=headers).json()
