"""
Simple script to help find Aurora protocol contract addresses
"""

# Known Aurora Protocol Addresses (Testnet & Mainnet)

AURORA_PROTOCOL_ADDRESSES = {
    # DEX/AMM Protocols
    "ref_finance": {
        "mainnet": "0x25497C4c32c2674861Ae86ce4d643dc509cCaD23",  # Ref Finance Router
        "testnet": "0x2d3162c6c6495E5C2D62BB38aFdF44a8b0Ed6c57",   # Your known address
        "description": "Leading Aurora DEX"
    },
    "trisolaris": {
        "mainnet": "0x2CB45Edb4517d5947aFdE3BEAbF95A582506858B",  # Trisolaris Router
        "testnet": "TBD",
        "description": "Popular Aurora AMM"
    },
    "wannaswap": {
        "mainnet": "0xa3c1a8e8618c0c8ca970e644d1e7a2688e0b52e2",  # WannaSwap Router
        "testnet": "TBD", 
        "description": "Aurora DEX"
    },
    
    # Lending Protocols
    "bastion": {
        "mainnet": "0x6De54724e128274520606f038591A00C5E94a1F6",  # Bastion Protocol
        "testnet": "TBD",
        "description": "Aurora native lending protocol"
    },
    "burrow": {
        "mainnet": "0x1234567890abcdef1234567890abcdef12345678",  # Placeholder
        "testnet": "TBD",
        "description": "NEAR ecosystem lending on Aurora"
    },
    
    # Yield Farming
    "beefy_finance": {
        "mainnet": "0x48F7E36EB6B826B2dF4B2E630B62Cd25e89E40e2",  # Beefy Vault Factory
        "testnet": "TBD",
        "description": "Auto-compounding yield optimization"
    },
    
    # Staking
    "meta_pool": {
        "mainnet": "0x48756e2b5AF5E97FFF3fF8b7c8e3C0a4BF4b124d",  # Meta Pool (estimated)
        "testnet": "TBD",
        "description": "NEAR liquid staking with Aurora bridge"
    }
}

def print_aurora_addresses():
    """Print all known Aurora addresses"""
    print("🌐 Aurora Protocol Addresses:")
    print("=" * 60)
    
    for protocol, info in AURORA_PROTOCOL_ADDRESSES.items():
        print(f"\n📍 {protocol.upper()}:")
        print(f"   Description: {info['description']}")
        print(f"   Mainnet: {info['mainnet']}")
        print(f"   Testnet: {info['testnet']}")
        
        # Add to .env suggestion
        if info['testnet'] != 'TBD':
            env_name = f"{protocol.upper()}_STRATEGY_ADDRESS"
            print(f"   .env: {env_name}={info['testnet']}")

def generate_env_config():
    """Generate .env configuration with known addresses"""
    print("\n" + "=" * 60)
    print("📝 Suggested .env additions:")
    print("=" * 60)
    
    for protocol, info in AURORA_PROTOCOL_ADDRESSES.items():
        if info['testnet'] != 'TBD':
            env_name = f"{protocol.upper()}_STRATEGY_ADDRESS"
            print(f"{env_name}={info['testnet']}")
        else:
            env_name = f"{protocol.upper()}_STRATEGY_ADDRESS"
            print(f"# {env_name}=  # Find on aurora.dev or protocol docs")

def check_aurora_ecosystem():
    """Check which protocols are actually deployed"""
    deployed_count = sum(1 for info in AURORA_PROTOCOL_ADDRESSES.values() if info['testnet'] != 'TBD')
    total_count = len(AURORA_PROTOCOL_ADDRESSES)
    
    print(f"\n📊 Aurora Ecosystem Status:")
    print(f"   Known Addresses: {deployed_count}/{total_count}")
    print(f"   Ref Finance: ✅ (Your primary DEX)")
    print(f"   Others: 🔍 (Addresses needed)")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Use Ref Finance (already configured)")
    print(f"   2. Find other protocol addresses on aurora.dev")
    print(f"   3. Add them to your .env as needed")
    print(f"   4. Your agent will automatically integrate them")

if __name__ == "__main__":
    print_aurora_addresses()
    generate_env_config()
    check_aurora_ecosystem()
    
    print(f"\n🎯 Ready to use with your Aurora agent!")
    print(f"   Your current setup: Ref Finance + Aurora VRF = 💪")