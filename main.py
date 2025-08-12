from fastapi import FastAPI,Request
from wallet import save_user_data
from fastapi.responses import JSONResponse
import json

app = FastAPI()

@app.get("/wallet/fetchAddressData&Store")
def fetch_and_store(uid: str, address: str):
    return save_user_data(uid, address)


@app.get('/')
def health():
    return {"status":"Running"}

@app.post("/api/moralis-webhook")
async def moralis_webhook(request: Request):
    try:
        payload = await request.json()
        print("Received webhook:\n", json.dumps(payload, indent=2))

        address = None
        if payload.get("erc20Transfers"):
            first_transfer = payload["erc20Transfers"][0]
            address = first_transfer.get("to") or first_transfer.get("from")
        elif payload.get("nativeTransfers"):
            first_transfer = payload["nativeTransfers"][0]
            address = first_transfer.get("to") or first_transfer.get("from")

        if not address:
            print("No address found in webhook payload")
            return JSONResponse({"message": "No address found"}, status_code=200)

        from firebaseConfig import fs
        uid = None
        users = fs.collection("USERS").stream()
        for user_doc in users:
            wallets_ref = fs.collection("USERS").document(user_doc.id).collection("wallets")
            wallet_doc = wallets_ref.document(address.lower()).get()
            if wallet_doc.exists:
                uid = user_doc.id
                break

        if not uid:
            print(f"Address {address} not in active users")
            return JSONResponse({"message": "Address not in active users"}, status_code=200)

        save_user_data(uid, address)
        print(f"Updated Firestore for {address}")

        return JSONResponse({"message": f"Updated Firestore for {address}"}, status_code=200)

    except Exception as e:
        print("Webhook error:", e)
        return JSONResponse({"error": str(e)}, status_code=200)
    


