"""
get_sandbox_token.py
---------------------
Run this once to get a Plaid sandbox access token for testing.
Usage: python get_sandbox_token.py
"""

import os
from dotenv import load_dotenv
import plaid
from plaid.api import plaid_api
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

load_dotenv()

configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        "clientId": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SECRET"),
    },
)

client = plaid_api.PlaidApi(plaid.ApiClient(configuration))

# Create a sandbox public token (simulates a user linking their bank)
public_token_response = client.sandbox_public_token_create(
    SandboxPublicTokenCreateRequest(
        institution_id="ins_109508",  # First Platypus Bank (Plaid's sandbox bank)
        initial_products=[Products("transactions")],
    )
)

# Exchange for access token
exchange_response = client.item_public_token_exchange(
    ItemPublicTokenExchangeRequest(
        public_token=public_token_response["public_token"]
    )
)

access_token = exchange_response["access_token"]
print(f"\nYour sandbox access token:\n{access_token}\n")
print("Copy this token — you'll use it with fetch_bank_transactions.")
