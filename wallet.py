from moralis import evm_api
from firebaseConfig import fs
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')

top_chains = ["eth", "bsc", "polygon", "avalanche","arbitrum"]
unitMap = {
    'eth':'NPQ',
    'bsc':'SQUID',
    'polygon':'MATIC',
    'avalanche':'AVAX',
    'arbitrum':'USDC'
}

def get_wallet_networth(wallet_address: str, chains=top_chains):
    params = {
        "chains": chains,
        "exclude_spam": True,
        "exclude_unverified_contracts": True,
        "max_token_inactivity": 1,
        "min_pair_side_liquidity_usd": 1000,
        "address": wallet_address
    }

    try:
        result = evm_api.wallets.get_wallet_net_worth(
            api_key=API_KEY,
            params=params
        )
        return result
    except Exception as e:
        print(f"Error fetching wallet net worth: {e}")
        return None




def get_wallet_active_chains(wallet_address: str, chains=top_chains):
    params = {
        "chains": chains,
        "address": wallet_address
    }
    try:
        result = evm_api.wallets.get_wallet_active_chains(
            api_key=API_KEY,
            params=params
        )
        return result
    except Exception as e:
        print(f"Error fetching active chains: {e}")
        return {"error": str(e)}
    

def clean_chain_response(chain_response,chain):
    for field in ["cursor", "page", "page_size", "block_number"]:
        chain_response.pop(field, None)

    tokens = chain_response.pop("result", [])

    filtered_tokens = [
        t for t in tokens
        if t.get("verified_contract", False) and not t.get("possible_spam", True)
    ]

    cleaned = []
    for token in filtered_tokens:
       
        cleaned.append({
            key: value for key, value in token.items()
            if key not in ["balance", "decimals", "possible_spam", "verified_contract", "security_score", "thumbnail", "logo","total_supply","total_supply_formatted","percentage_relative_to_total_supply","security_score"]
    }) 
        
    return {
        "unit": chain_response.get("unit", unitMap[chain]),
        "token": cleaned
    }

def get_top_chains_balances(address: str, chains=top_chains):
    all_chains_balances = {}

    for chain in chains:
        params = {
            "chain": chain, 
            "address": address,
            "exclude_spam": True,
            "exclude_unverified_contracts": True,
        }
        try:
            result = evm_api.wallets.get_wallet_token_balances_price(
                api_key=API_KEY,
                params=params,
            )
            cleaned_result = clean_chain_response(result,chain)
            all_chains_balances[chain] = cleaned_result

        except Exception as e:
            all_chains_balances[chain] = {"error": str(e)}

    return {"address": address, "chains": all_chains_balances}



def get_wallet_stats_multiple_chains(address: str,chains= top_chains):
    results = []
    for chain in chains:
        params = {
            "chain": chain,
            "address": address
        }
        try:
            result = evm_api.wallets.get_wallet_stats(
                api_key=API_KEY,
                params=params
            )
            results.append({"chain": chain, "result": result})
        except Exception as e:
            print(f"Error fetching wallet stats for chain {chain}: {e}")
            results.append({"chain": chain, "error": str(e)})
    return results


def clean_trans_response(trans_response, chain):
    trans = trans_response.get("result", [])

    keys_to_remove = {
        "from_address_label",
        "to_address_entity",
        "nonce",
        "to_address_entity_logo",
        "to_address_label",
        "value",
        "gas",
        "gas_price",
        "input",
        "receipt_cumulative_gas_used",
        "receipt_gas_used",
        "receipt_contract_address",
        "receipt_root",
        "from_address_entity",
        "from_address_entity_logo"
    }

    cleaned = []
    for tx in trans:
        cleaned_tx = {k: v for k, v in tx.items() if k not in keys_to_remove}
        cleaned.append(cleaned_tx)

    return {
        "chain": chain,
        "transactions": cleaned
    }


def get_transactions_for_chains(address: str, chains=top_chains):
    results = []
    for chain in chains:
        params = {
            "chain": chain,
            "limit": 5,
            "order": "ASC",
            "address": address
        }
        try:
            raw_result = evm_api.transaction.get_wallet_transactions(
                api_key=API_KEY,
                params=params
            )
            cleaned_result = clean_trans_response(raw_result, chain)
            results.append({
                "chain": chain,
                "unit": unitMap[chain],
                "transactions": cleaned_result.get("transactions", [])
            })
        except Exception as e:
            print(f"Error fetching transactions for chain {chain}: {e}")
            results.append({"chain": chain, "error": str(e)})
    return results



def sort_filter_and_clean_tokens(data):
    fields_to_remove = {
        "usd_price_24hr_percent_change",
        "usd_price_24hr_usd_change",
        "usd_value",
        "usd_value_24hr_usd_change",
        "native_token",
    }

    for chain_name, chain_data in data["chains"].items():
        filtered_tokens = [
            {k: v for k, v in t.items() if k not in fields_to_remove}
            for t in chain_data["token"]
            if t.get("portfolio_percentage", 0) > 0
        ]
        filtered_tokens.sort(key=lambda t: t["portfolio_percentage"], reverse=True)
        chain_data["token"] = filtered_tokens

    return data




def create_analytics_array(address:str):
    analytics = []
    try :
        ans = {}
        ans = get_top_chains_balances(address)
        ans = sort_filter_and_clean_tokens(ans)
        sorted_filtered_data = ans
        for chain_name, chain_data in sorted_filtered_data["chains"].items():
            analytics.append({
                "chain": chain_name,
                "token": chain_data["token"]
            })
    
    except Exception as e:
            print(f"Error : {e}")
            analytics = []
    
    return analytics

def fetchAllData(address: str):
    combinedAns = {}
    try:
        combinedAns = get_top_chains_balances(address)
        combinedAns['transaction'] = get_transactions_for_chains(address)
        combinedAns['networth'] = get_wallet_networth(address)
        combinedAns['stats'] = get_wallet_stats_multiple_chains(address)
        combinedAns['active_chains'] = get_wallet_active_chains(address)['active_chains']
        combinedAns['Analytics'] = create_analytics_array(address)
    except Exception as e:
        print(f"Error occurred: {e}")
    return combinedAns



def add_address_to_moralis_stream(address: str, stream_id: str):
    url = f"https://api.moralis.io/streams/v1/{stream_id}/address"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": API_KEY
    }
    payload = {
        "address": address
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Address {address} added to Moralis stream.")
    else:
        print(f"Error adding address: {response.text}")

def save_user_data(uid: str, address: str):
    try:
        data = fetchAllData(address)
        fs.collection("USERS").document(uid).collection("wallets").document(address).set(data)
        
        stream_id = '0d6a8c2c-0562-4b8c-84cb-c774b15c4c51'
        add_address_to_moralis_stream(address, stream_id)
        
        return {"status": "success"}
    except Exception as e:
        print(f"Error storing data for UID {uid}: {e}")
        return {"status": "error", "message": str(e)}