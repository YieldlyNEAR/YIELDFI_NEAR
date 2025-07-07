from web3 import Web3

# --- Configuration ---
RPC_URL = "https://testnet.aurora.dev"
BLOCKS_PER_YEAR = 31_536_000

# A list of EVERY potential cUSDC address we have seen so far
BASTION_ADDRESSES = {
    "Main Hub cUSDC": "0xe5308dc623101508952948b141fD9eaBd3337D99",
    "Aurora Realm cUSDC": "0x8E9FB3f2cc8b08184CB5FB7BcDC61188E80C3cB0",
    "Multichain Realm cUSDC": "0x10a9153A7b4da83Aa1056908C710f1aaCCB3Ef85",
    "Found on Explorer (1)": "0x19A6356Be6704B2cBd98eE1137b2030C22516bE9",
    "Found on Explorer (2)": "0x6E2dbc1eaa9EEbbEc39C489d32657593cA1D4F48",
    "Testnet Address (from docs)": "0x51ff0b20d2ad385438268391189a08316b8472fc",
}

CUSDC_ABI = [{
    "constant": True,
    "inputs": [],
    "name": "supplyRatePerBlock",
    "outputs": [{"name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
}]

# --- Web3 Setup ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    print("❌ Connection Failed")
    exit()
print(f"✅ Connected to Aurora Testnet RPC: {RPC_URL}\n")


# --- Test All Addresses ---
for name, address in BASTION_ADDRESSES.items():
    print("-" * 50)
    print(f"Testing {name}: {address}")
    
    try:
        # Let web3.py create the correctly formatted checksum address
        checksum_address = Web3.to_checksum_address(address)
        
        # Create contract instance
        contract = w3.eth.contract(address=checksum_address, abi=CUSDC_ABI)
        
        # Call the view function
        rate_raw = contract.functions.supplyRatePerBlock().call()
        
        # If the call succeeds, calculate and print the APY
        apy = (rate_raw / 1e18) * BLOCKS_PER_YEAR * 100
        print(f"✅ SUCCESS! Found active contract.")
        print(f"   Live APY: {apy:.4f}%")
        
    except Exception as e:
        # If the call fails, print the error
        print(f"❌ FAILED. Reason: {e}")

print("-" * 50)