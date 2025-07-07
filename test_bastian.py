import os
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables (optional, but good practice for RPC_URL)
load_dotenv()

# --- Configuration ---
RPC_URL = os.getenv("NEAR_TESTNET_RPC_URL", "https://testnet.aurora.dev")
CUSDC_ADDRESS = "0x8E9FB3f2cc8b08184CB5FB7BcDC61188E80C3cB0"
CUSDC_ABI = [{
    "constant": True,
    "inputs": [],
    "name": "supplyRatePerBlock",
    "outputs": [{"name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
}]
BLOCKS_PER_YEAR = 31_536_000 # ~1 block per second

# --- Web3 Setup ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
print(f"Attempting to connect to Aurora Testnet...")
if not w3.is_connected():
    print("❌ Connection Failed")
    exit()
print(f"✅ Connected to RPC: {RPC_URL}")


# --- Test Contract Call ---
try:
    print(f"\nQuerying Bastion cUSDC contract at: {CUSDC_ADDRESS}")
    bastion_contract = w3.eth.contract(address=CUSDC_ADDRESS, abi=CUSDC_ABI)

    # 1. Get the raw supply rate from the contract
    supply_rate_raw = bastion_contract.functions.supplyRatePerBlock().call()
    print(f"✅ Raw 'supplyRatePerBlock' value: {supply_rate_raw}")

    # 2. Calculate the APY
    # The rate has 18 decimals, so we divide by 1e18 before multiplying
    supply_apy = (supply_rate_raw / 1e18) * BLOCKS_PER_YEAR * 100
    print(f"📈 Calculated Live Supply APY: {supply_apy:.4f}%")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")