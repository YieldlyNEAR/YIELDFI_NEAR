import os
import json
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Load environment variables from .env file
load_dotenv()

# --- Aurora Configuration ---
RPC_URL = os.getenv("NEAR_TESTNET_RPC_URL")  # Aurora testnet RPC
CHAIN_ID = int(os.getenv("NEAR_TESTNET_CHAIN_ID"))  # Aurora chain ID
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Contract Addresses ---
VAULT_ADDRESS = os.getenv("VAULT_ADDRESS")
VRF_STRATEGY_ADDRESS = os.getenv("VRF_STRATEGY_ADDRESS")
USDC_TOKEN_ADDRESS = os.getenv("USDC_TOKEN_ADDRESS")

# --- Aurora Strategy Addresses ---
REF_FINANCE_STRATEGY_ADDRESS = os.getenv("REF_FINANCE_STRATEGY_ADDRESS", "")

# --- Web3 Setup for Aurora ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
# Inject PoA middleware for Aurora
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# --- Agent Account ---
agent_account = w3.eth.account.from_key(AGENT_PRIVATE_KEY)
print(f"🤖 Aurora Agent Wallet Address: {agent_account.address}")

# --- Function to load ABI ---
def load_abi(filename):
    path = os.path.join("abi", filename)
    with open(path, "r") as f:
        return json.load(f)["abi"]

# --- Load ABIs ---
vault_abi = load_abi("Vault.json")
vrf_strategy_abi = load_abi("NearVrfYieldStrategy.json")  # Updated for NEAR VRF
usdc_abi = load_abi("MockUSDC.json")

# --- Create Contract Objects ---
vault_contract = w3.eth.contract(address=VAULT_ADDRESS, abi=vault_abi)
vrf_strategy_contract = w3.eth.contract(address=VRF_STRATEGY_ADDRESS, abi=vrf_strategy_abi)
usdc_contract = w3.eth.contract(address=USDC_TOKEN_ADDRESS, abi=usdc_abi)

print(f"✅ Aurora Configuration loaded on chain {CHAIN_ID}")
print(f"🌐 Aurora RPC: {RPC_URL}")
print(f"🎲 VRF Strategy: {VRF_STRATEGY_ADDRESS}")
print(f"💰 Agent has Aurora ETH for gas fees")