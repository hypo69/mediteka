from SANDBOX.Alrix010.sdk import FoundryClient

with FoundryClient("http://localhost:9696") as client:
    response = client._request("GET", "/api/v1/foundry/models/available")
    print(response)
