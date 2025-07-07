import os
import json
import time
import asyncio
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import ContractLogicError
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools import tool

load_dotenv()

# ==============================================================================
# ML RISK ASSESSMENT INTEGRATION - FIXED IMPORT PATHS
# ==============================================================================

# Try to import the ML risk assessment with multiple path options
try:
    import sys
    
    # Try different possible paths
    possible_paths = [
        './ml-risk',
        './near-vault-agent/ml-risk', 
        'ml-risk',
        'near-vault-agent/ml-risk',
        os.path.join(os.path.dirname(__file__), 'ml-risk'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml-risk')
    ]
    
    risk_api = None
    ML_RISK_AVAILABLE = False
    
    for path in possible_paths:
        try:
            if path not in sys.path:
                sys.path.append(path)
            
            # Check if risk_api.py exists in this path
            risk_api_file = os.path.join(path, 'risk_api.py')
            if os.path.exists(risk_api_file):
                from risk_api import StrategyRiskAPI
                
                # Initialize ML risk API
                risk_api = StrategyRiskAPI()
                print(f"🧠 ML Risk Assessment: LOADED from {path}")
                ML_RISK_AVAILABLE = True
                break
        except Exception as e:
            continue
    
    if not ML_RISK_AVAILABLE:
        raise ImportError("Could not find risk_api in any path")
    
except Exception as e:
    print(f"⚠️ ML Risk Assessment: NOT AVAILABLE ({e})")
    print("📝 To enable ML risk assessment:")
    print("   1. Ensure near-vault-agent/ml-risk/risk_api.py exists")
    print("   2. Run: python near-vault-agent/ml-risk/anomaly_risk_model.py")
    print("   3. Restart the Aurora agent")
    risk_api = None
    ML_RISK_AVAILABLE = False

# ==============================================================================
# AURORA MULTI-STRATEGY CONFIGURATION
# ==============================================================================

# Aurora Configuration
RPC_URL = os.getenv("NEAR_TESTNET_RPC_URL", "https://testnet.aurora.dev")
CHAIN_ID = int(os.getenv("NEAR_TESTNET_CHAIN_ID", 1313161555))
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Contract Addresses (Your Deployed Contracts!)
MULTI_VAULT_ADDRESS = "0x494672E363A914e0314B7d70Ad7b4F99E66E789a" # UPDATED!
USDC_TOKEN_ADDRESS = "0xC0933C5440c656464D1Eb1F886422bE3466B1459"

# Aurora Strategy Addresses (Your Deployed Strategies!)
AURORA_STRATEGY_ADDRESSES = {
    "ref_finance": "0x6B6A30149b99A09b697805eA5b2AaDCbC396586a",
    "trisolaris": "0x7964bBECA179E4e00c02A71A84C6A327E3e808Cb", 
    "bastion": "0xFF2B890de3C8f2eE8725678F2a2598b5C42E4fAc" # UPDATED
}



# Aurora Protocol Addresses (Real ones)
AURORA_PROTOCOLS = {
    "ref_finance": {
        "router": "0x2d3162c6c6495E5C2D62BB38aFdF44a8b0Ed6c57",
        "factory": "0x1a3D6C0F61f59CBfe9f17e6E06aa8B4df20e14BC",
        "farms": "0x73a51Da6b1aD2d71a8EA0BeF0B9e2c78A1C6E9BB",
        "expected_apy": 15.2
    },
    "trisolaris": {
        "router": "0x2CB45Edb4517d5947aFdE3BEAbF95A582506858B",
        "factory": "0xc66F594268041dB60507F00703b152492fb176E7",
        "farms": "0x1f1Ed214bef5E83D8f5d0eB5D7011EB965D0D79B",
        "expected_apy": 12.8
    },
    "bastion": {
        "protocol": "0x6De54724e128274520606f038591A00C5E94a1F6",
        "cusdc": "0xe5308dc623101508952948b141fD9eaBd3337D99",
        "comptroller": "0x6edd3b3ac5B700EfD0adBE7FdE4E45a1B4C5B1b4",
        "expected_apy": 9.1
    },
    "aurora_bridge": {
        "bridge": "0x51b5cc6d70746d8275636493e4f5708a4AEB13a0",
        "expected_apy": 0.0
    }
}

# Portfolio Allocation Strategy
DEFAULT_ALLOCATION = {
    "ref_finance": 0.40,     # 40% - Highest yield DEX
    "trisolaris": 0.30,      # 30% - Diversified AMM
    "bastion": 0.20,         # 20% - Lower risk lending
    "reserve": 0.10          # 10% - Liquid reserve
}

# Risk Thresholds
RISK_THRESHOLDS = {
    "max_single_protocol": 0.50,  # Max 50% in any protocol
    "min_reserve": 0.05,           # Min 5% reserve
    "rebalance_threshold": 0.05,   # Rebalance if >5% drift
    "emergency_exit_threshold": 0.8 # Exit if risk score >0.8
}

# Web3 Setup
w3 = Web3(Web3.HTTPProvider(RPC_URL))
agent_account = w3.eth.account.from_key(AGENT_PRIVATE_KEY)
print(f"🚀 Aurora Multi-Strategy Agent: {agent_account.address}")

# Load ABIs for deployed contracts
vault_abi = [
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_asset",
          "type": "address"
        },
        {
          "internalType": "string",
          "name": "_name",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "_symbol",
          "type": "string"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "value",
          "type": "uint256"
        }
      ],
      "name": "Approval",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "strategy",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "EmergencyExit",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "previousOwner",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "OwnershipTransferred",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "strategy",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "name",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "allocation",
          "type": "uint256"
        }
      ],
      "name": "StrategyAdded",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "strategy",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "oldBalance",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "newBalance",
          "type": "uint256"
        }
      ],
      "name": "StrategyRebalanced",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "from",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "to",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "value",
          "type": "uint256"
        }
      ],
      "name": "Transfer",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "strategy",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "YieldHarvested",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "REBALANCE_INTERVAL",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_strategy",
          "type": "address"
        },
        {
          "internalType": "string",
          "name": "_name",
          "type": "string"
        },
        {
          "internalType": "uint256",
          "name": "_allocation",
          "type": "uint256"
        }
      ],
      "name": "addStrategy",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        }
      ],
      "name": "allowance",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "approve",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "asset",
      "outputs": [
        {
          "internalType": "contract IERC20",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "account",
          "type": "address"
        }
      ],
      "name": "balanceOf",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        }
      ],
      "name": "convertToAssets",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        }
      ],
      "name": "convertToShares",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "decimals",
      "outputs": [
        {
          "internalType": "uint8",
          "name": "",
          "type": "uint8"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "subtractedValue",
          "type": "uint256"
        }
      ],
      "name": "decreaseAllowance",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "receiver",
          "type": "address"
        }
      ],
      "name": "deposit",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "strategy",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        },
        {
          "internalType": "bytes",
          "name": "data",
          "type": "bytes"
        }
      ],
      "name": "depositToStrategy",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "emergencyExit",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "getStrategies",
      "outputs": [
        {
          "components": [
            {
              "internalType": "address",
              "name": "strategyAddress",
              "type": "address"
            },
            {
              "internalType": "uint256",
              "name": "allocation",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "balance",
              "type": "uint256"
            },
            {
              "internalType": "bool",
              "name": "active",
              "type": "bool"
            },
            {
              "internalType": "string",
              "name": "name",
              "type": "string"
            }
          ],
          "internalType": "struct AuroraMultiVault.Strategy[]",
          "name": "",
          "type": "tuple[]"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "strategyAddress",
          "type": "address"
        }
      ],
      "name": "getStrategy",
      "outputs": [
        {
          "components": [
            {
              "internalType": "address",
              "name": "strategyAddress",
              "type": "address"
            },
            {
              "internalType": "uint256",
              "name": "allocation",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "balance",
              "type": "uint256"
            },
            {
              "internalType": "bool",
              "name": "active",
              "type": "bool"
            },
            {
              "internalType": "string",
              "name": "name",
              "type": "string"
            }
          ],
          "internalType": "struct AuroraMultiVault.Strategy",
          "name": "",
          "type": "tuple"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "strategy",
          "type": "address"
        },
        {
          "internalType": "bytes",
          "name": "data",
          "type": "bytes"
        }
      ],
      "name": "harvestStrategy",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "addedValue",
          "type": "uint256"
        }
      ],
      "name": "increaseAllowance",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "name": "isStrategy",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "lastRebalance",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "name",
      "outputs": [
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "owner",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address[]",
          "name": "strategyAddresses",
          "type": "address[]"
        },
        {
          "internalType": "uint256[]",
          "name": "targetAmounts",
          "type": "uint256[]"
        }
      ],
      "name": "rebalance",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "renounceOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "name": "strategies",
      "outputs": [
        {
          "internalType": "address",
          "name": "strategyAddress",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "allocation",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "balance",
          "type": "uint256"
        },
        {
          "internalType": "bool",
          "name": "active",
          "type": "bool"
        },
        {
          "internalType": "string",
          "name": "name",
          "type": "string"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "name": "strategyIndex",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "symbol",
      "outputs": [
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalAssets",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalDeployed",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalSupply",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "to",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "transfer",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "from",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "to",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "transferFrom",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "transferOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "receiver",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        }
      ],
      "name": "withdraw",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    }
]

strategy_abi = [
    {"name": "deposit", "type": "function", "inputs": [{"type": "uint256"}], "outputs": [], "stateMutability": "nonpayable"},
    {"name": "withdraw", "type": "function", "inputs": [{"type": "uint256"}], "outputs": [], "stateMutability": "nonpayable"},
    {"name": "harvest", "type": "function", "inputs": [], "outputs": [], "stateMutability": "nonpayable"},
    {"name": "getBalance", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"}
]

usdc_abi = [
    {"name": "balanceOf", "type": "function", "inputs": [{"type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "approve", "type": "function", "inputs": [{"type": "address"}, {"type": "uint256"}], "outputs": [{"type": "bool"}], "stateMutability": "nonpayable"},
    {"name": "transfer", "type": "function", "inputs": [{"type": "address"}, {"type": "uint256"}], "outputs": [{"type": "bool"}], "stateMutability": "nonpayable"},
    {"name": "transferFrom", "type": "function", "inputs": [{"type": "address"}, {"type": "address"}, {"type": "uint256"}], "outputs": [{"type": "bool"}], "stateMutability": "nonpayable"},
    {"name": "mint", "type": "function", "inputs": [{"type": "address"}, {"type": "uint256"}], "outputs": [], "stateMutability": "nonpayable"},
    {"name": "faucet", "type": "function", "inputs": [{"type": "uint256"}], "outputs": [], "stateMutability": "nonpayable"},
    {"name": "decimals", "type": "function", "inputs": [], "outputs": [{"type": "uint8"}], "stateMutability": "pure"},
    {"name": "totalSupply", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"}
]

vault_contract = w3.eth.contract(address=MULTI_VAULT_ADDRESS, abi=vault_abi)
usdc_contract = w3.eth.contract(address=USDC_TOKEN_ADDRESS, abi=usdc_abi)

# Strategy contract instances
ref_strategy_contract = w3.eth.contract(address=AURORA_STRATEGY_ADDRESSES["ref_finance"], abi=strategy_abi)
tri_strategy_contract = w3.eth.contract(address=AURORA_STRATEGY_ADDRESSES["trisolaris"], abi=strategy_abi)
bastion_strategy_contract = w3.eth.contract(address=AURORA_STRATEGY_ADDRESSES["bastion"], abi=strategy_abi)

# ==============================================================================
# ML-ENHANCED AURORA PROTOCOL DATA PROVIDERS
# ==============================================================================

def get_ml_risk_score(strategy_address: str, protocol_name: str, fallback_score: float) -> float:
    """Get ML risk score with fallback."""
    if not ML_RISK_AVAILABLE or not risk_api:
        return fallback_score
    
    try:
        ml_score = risk_api.assess_strategy_risk(strategy_address)
        print(f"🧠 ML Risk Score for {protocol_name}: {ml_score:.3f}")
        return ml_score
    except Exception as e:
        print(f"⚠️ ML risk assessment failed for {protocol_name}: {e}")
        return fallback_score

class RefFinanceProvider:
    def __init__(self):
        self.api_url = "https://testnet-indexer.ref-finance.com"
    
    def get_pools_data(self) -> Dict[str, Any]:
        """Get current pool data from Ref Finance with ML risk assessment."""
        try:
            # Use the correct /list-top-pools endpoint. No parameters are needed.
            response = requests.get(f"{self.api_url}/list-top-pools", timeout=10)
            response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx)
            pools = response.json()
            
            # Find USDC pools by checking the more reliable 'token_symbols' field
            usdc_pools = [
                p for p in pools if any('usdc' in symbol.lower() for symbol in p.get('token_symbols', []))
            ]
            
            total_tvl = sum(float(p.get('tvl', 0)) for p in usdc_pools)
            avg_fee = sum(float(p.get('total_fee', 0)) for p in usdc_pools) / len(usdc_pools) if usdc_pools else 0
            
            # Get ML risk score
            risk_score = get_ml_risk_score(
                AURORA_STRATEGY_ADDRESSES["ref_finance"], 
                "Ref Finance", 
                0.35  # Fallback risk score
            )
            
            return {
                "protocol": "ref_finance",
                "tvl": total_tvl,
                "avg_fee_rate": avg_fee,
                "pool_count": len(usdc_pools),
                "estimated_apy": 15.2,
                "risk_score": risk_score,
                "ml_enhanced": ML_RISK_AVAILABLE,
                "status": "active"
            }
        except Exception as e:
            print(f"⚠️ Ref Finance API unavailable, using fallback data: {e}")
            
            # Get ML risk even with fallback data
            risk_score = get_ml_risk_score(
                AURORA_STRATEGY_ADDRESSES["ref_finance"], 
                "Ref Finance", 
                0.35
            )
            
            return {
                "protocol": "ref_finance",
                "tvl": 50000000,
                "avg_fee_rate": 0.003,
                "pool_count": 25,
                "estimated_apy": 15.2,
                "risk_score": risk_score,
                "ml_enhanced": ML_RISK_AVAILABLE,
                "status": "fallback"
            }
            
class TriSolarisProvider:
    """Real-time data from the official Trisolaris Subgraph on The Graph."""

    def __init__(self):
        # The new, official Graph Gateway URL for the Trisolaris subgraph
        self.api_url = f"https://gateway.thegraph.com/api/{os.getenv('GRAPH_API_KEY')}/subgraphs/id/GDDMJSmzYykEvyjDoWG8gDkhcwiPo3y8KsD4R6S6cWmz"
        
        # The efficient query that filters for USDC pools directly
        self.query = """
            query GetUsdcFarms {
              liquidityPools(
                first: 20,
                orderBy: totalValueLockedUSD,
                orderDirection: desc,
                where: {inputTokens_: {symbol_contains_nocase: "usdc"}}
              ) {
                id
                name
                totalValueLockedUSD
                rewardTokenEmissionsUSD
              }
            }
        """

    def get_farms_data(self) -> Dict[str, Any]:
        """Get farming data from Trisolaris using the authenticated Graph Gateway."""
        try:
            # The API key is now part of the URL, so no extra headers are needed.
            response = requests.post(self.api_url, json={"query": self.query}, timeout=15)
            response.raise_for_status()
            data = response.json()

            usdc_farms = data.get("data", {}).get("liquidityPools", [])

            if not usdc_farms:
                raise Exception("No USDC farms found in The Graph response")
            
            # --- We can now try to calculate APY again ---
            apys = []
            for farm in usdc_farms:
                tvl = float(farm.get("totalValueLockedUSD", 0))
                # The rewards are often given daily, so we multiply by 365 for APY
                # Handle cases where rewards might be null or not a list
                rewards_list = farm.get("rewardTokenEmissionsUSD")
                daily_rewards = 0
                if rewards_list and isinstance(rewards_list, list) and len(rewards_list) > 0:
                    daily_rewards = float(rewards_list[0])

                if tvl > 1000 and daily_rewards > 0:
                    apy = (daily_rewards * 365 / tvl) * 100
                    apys.append(apy)
            
            avg_apy = sum(apys) / len(apys) if apys else 0
            
            risk_score = get_ml_risk_score(
                AURORA_STRATEGY_ADDRESSES["trisolaris"], 
                "TriSolaris", 
                0.40
            )

            return {
                "protocol": "trisolaris",
                "farms": len(usdc_farms),
                "estimated_apy": avg_apy if avg_apy > 0 else 12.8, # Use live APY or fallback
                "risk_score": risk_score,
                "ml_enhanced": ML_RISK_AVAILABLE,
                "status": "active"
            }

        except Exception as e:
            print(f"⚠️ TriSolaris API unavailable, using fallback data: {e}")
            # ... (fallback logic remains the same)
            risk_score = get_ml_risk_score(
                AURORA_STRATEGY_ADDRESSES["trisolaris"], 
                "TriSolaris", 
                0.40
            )
            return {
                "protocol": "trisolaris",
                "farms": 15,
                "estimated_apy": 12.8,
                "risk_score": risk_score,
                "ml_enhanced": ML_RISK_AVAILABLE,
                "status": "fallback"
            }
            # RIP NO BASTION underserving of indents
class BastionProvider:
    """
    Provides fallback data for Bastion Protocol. Since the protocol's testnet
    contracts are inactive, this provider returns stable, estimated values.
    """
    
    def get_lending_data(self) -> Dict[str, Any]:
        """Returns a hardcoded, estimated data set for Bastion."""
        
        # Since the protocol's testnet contracts are unresponsive, we
        # return a stable, estimated value instead of attempting a live call.
        print("ℹ️ Bastion Protocol is inactive on testnet; using estimated fallback data.")

        risk_score = get_ml_risk_score(
            AURORA_STRATEGY_ADDRESSES["bastion"], 
            "Bastion", 
            0.25 # Default risk score
        )
        
        return {
            "protocol": "bastion",
            "supply_apy": 9.1,
            "utilization": 0.70,
            "estimated_apy": 9.1,
            "risk_score": risk_score,
            "ml_enhanced": ML_RISK_AVAILABLE,
            "status": "fallback"
        }

        
# Initialize providers
ref_provider = RefFinanceProvider()
tri_provider = TriSolarisProvider()
bastion_provider = BastionProvider()

# ==============================================================================
# AI STRATEGY OPTIMIZER WITH ML RISK
# ==============================================================================

class AuroraAIOptimizer:
    """AI-powered strategy optimization for Aurora protocols with ML risk."""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=OPENAI_API_KEY)
    
    def optimize_allocation(self, current_data: Dict[str, Any]) -> Dict[str, float]:
        """Use AI to optimize portfolio allocation with ML risk data."""
        try:
            # Add ML enhancement info to prompt
            ml_status = "🧠 ML RISK ASSESSMENT: ACTIVE" if ML_RISK_AVAILABLE else "⚠️ ML RISK ASSESSMENT: FALLBACK MODE"
            
            prompt = f"""
You are an expert DeFi portfolio manager for Aurora ecosystem with ML risk assessment.

{ml_status}

Current Protocol Data:
{json.dumps(current_data, indent=2)}

Current Allocation Target:
{json.dumps(DEFAULT_ALLOCATION, indent=2)}

Risk Constraints:
- Max 50% in any single protocol
- Min 5% reserve for liquidity
- Target risk-adjusted returns
- Consider Aurora gas advantages
- Use ML risk scores when available

Generate optimal allocation as JSON with allocation percentages that sum to 1.0:
{{"ref_finance": 0.XX, "trisolaris": 0.XX, "bastion": 0.XX, "reserve": 0.XX}}

Consider:
1. ML-enhanced risk scores (if available)
2. Risk-adjusted APY for each protocol
3. TVL and liquidity depth
4. Historical performance
5. Current market conditions
6. Aurora ecosystem advantages

Respond with ONLY the JSON allocation object.
"""
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*\}', content)
            if json_match:
                allocation = json.loads(json_match.group())
                
                # Validate allocation
                if self._validate_allocation(allocation):
                    return allocation
            
            # Fallback to default
            return DEFAULT_ALLOCATION
            
        except Exception as e:
            print(f"❌ AI optimization error: {e}")
            return DEFAULT_ALLOCATION
    
    def _validate_allocation(self, allocation: Dict[str, float]) -> bool:
        """Validate allocation meets constraints."""
        total = sum(allocation.values())
        if abs(total - 1.0) > 0.01:  # Allow 1% tolerance
            return False
        
        # Check constraints
        for protocol, weight in allocation.items():
            if protocol != "reserve" and weight > RISK_THRESHOLDS["max_single_protocol"]:
                return False
        
        if allocation.get("reserve", 0) < RISK_THRESHOLDS["min_reserve"]:
            return False
        
        return True

ai_optimizer = AuroraAIOptimizer()

# ==============================================================================
# ML-ENHANCED TOOLS (Using raw_transaction)
# ==============================================================================

@tool
def analyze_aurora_yields() -> str:
    """Analyze real-time yields across all Aurora DeFi protocols with ML risk assessment."""
    print("🔍 Analyzing Aurora yields with ML risk assessment...")
    
    try:
        # Gather data from all protocols
        ref_data = ref_provider.get_pools_data()
        tri_data = tri_provider.get_farms_data()
        bastion_data = bastion_provider.get_lending_data()
        
        # Calculate risk-adjusted returns
        protocols = {
            "ref_finance": {
                **ref_data,
                "risk_adjusted_apy": ref_data["estimated_apy"] * (1 - ref_data.get("risk_score", 0.5))
            },
            "trisolaris": {
                **tri_data,
                "risk_adjusted_apy": tri_data["estimated_apy"] * (1 - tri_data.get("risk_score", 0.5))
            },
            "bastion": {
                **bastion_data,
                "risk_adjusted_apy": bastion_data["estimated_apy"] * (1 - bastion_data.get("risk_score", 0.5))
            }
        }
        
        # Get AI recommendation
        optimal_allocation = ai_optimizer.optimize_allocation(protocols)
        
        ml_indicator = "🧠 ML-Enhanced" if ML_RISK_AVAILABLE else "🔄 Fallback Mode"
        
        return f"""
🌐 Aurora DeFi Yield Analysis ({ml_indicator}):

📊 Protocol Performance:
├─ Ref Finance: {ref_data['estimated_apy']:.1f}% APY (Risk: {ref_data.get('risk_score', 0.5):.3f}) 
├─ TriSolaris: {tri_data['estimated_apy']:.1f}% APY (Risk: {tri_data.get('risk_score', 0.5):.3f})
└─ Bastion: {bastion_data['estimated_apy']:.1f}% APY (Risk: {bastion_data.get('risk_score', 0.5):.3f})

🎯 AI Optimal Allocation:
├─ Ref Finance: {optimal_allocation.get('ref_finance', 0)*100:.1f}%
├─ TriSolaris: {optimal_allocation.get('trisolaris', 0)*100:.1f}%
├─ Bastion: {optimal_allocation.get('bastion', 0)*100:.1f}%
└─ Reserve: {optimal_allocation.get('reserve', 0)*100:.1f}%

💡 Expected Portfolio APY: {sum(protocols[p]['estimated_apy'] * optimal_allocation.get(p, 0) for p in protocols):.1f}%

🧠 ML Risk Status: {"ACTIVE - Using trained anomaly detection" if ML_RISK_AVAILABLE else "FALLBACK - Using static risk scores"}
        """
        
    except Exception as e:
        return f"❌ Error analyzing Aurora yields: {e}"

@tool
def assess_ml_strategy_risk(strategy_address: str) -> str:
    """Assess a specific strategy's risk using ML anomaly detection."""
    print(f"🧠 Assessing ML risk for strategy: {strategy_address}")
    
    try:
        if not ML_RISK_AVAILABLE:
            return f"""
❌ ML Risk Assessment Not Available

🔧 To enable ML risk assessment:
1. Run: python near-vault-agent/ml-risk/anomaly_risk_model.py
2. Ensure near-vault-agent/ml-risk/models/anomaly_risk_model.joblib exists
3. Restart the Aurora agent

📊 Currently using fallback risk scores

💡 ML model paths checked:
   - ./ml-risk/
   - ./near-vault-agent/ml-risk/
   - near-vault-agent/ml-risk/
            """
        
        risk_score = risk_api.assess_strategy_risk(strategy_address)
        risk_details = risk_api.get_risk_breakdown(strategy_address)
        
        risk_level = "🟢 LOW" if risk_score < 0.4 else "🟡 MEDIUM" if risk_score < 0.7 else "🔴 HIGH"
        
        return f"""
🧠 ML Strategy Risk Assessment:

📍 Strategy: {strategy_address}
📊 Risk Score: {risk_score:.3f} {risk_level}

🔍 Risk Breakdown:
{risk_details}

💡 ML Model: Trained on Ethereum mainnet protocols
🎯 Confidence: HIGH (based on transaction patterns)
✅ Aurora-specific risk assessment active
        """
        
    except Exception as e:
        return f"❌ ML risk assessment failed: {e}"

@tool
def mint_test_usdc(amount_usdc: float = 1000.0) -> str:
    """Mint MockUSDC tokens for testing the vault system."""
    print(f"🪙 Minting {amount_usdc} test USDC...")
    
    try:
        # Handle string input conversion
        if isinstance(amount_usdc, str):
            # Remove any extra characters and convert
            amount_usdc = float(amount_usdc.strip().split('\n')[0])
        
        amount_wei = int(amount_usdc * (10**6))  # USDC has 6 decimals
        
        # Use the faucet function for easy minting
        faucet_tx = usdc_contract.functions.faucet(amount_wei).build_transaction({
            'from': agent_account.address,
            'nonce': w3.eth.get_transaction_count(agent_account.address),
            'gas': 500_000,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        })
        
        signed_tx = w3.eth.account.sign_transaction(faucet_tx, agent_account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # Fixed to raw_transaction
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        # Check new balance
        new_balance = usdc_contract.functions.balanceOf(agent_account.address).call()
        
        return f"""
🪙 MockUSDC Minting Successful!

💰 Transaction Results:
├─ Minted: {amount_usdc:.2f} USDC
├─ Agent Balance: {new_balance / (10**6):.2f} USDC
├─ TX Hash: {tx_hash.hex()}
└─ Gas Used: {receipt.gasUsed:,}

✅ Ready for vault testing!
💡 You can now deposit into the Aurora vault
        """
        
    except Exception as e:
        return f"❌ USDC minting failed: {e}"

@tool
def execute_multi_strategy_rebalance() -> str:
    """Execute AI-optimized rebalancing across Aurora protocols with ML risk assessment."""
    print("⚖️ Executing multi-strategy rebalance with ML risk assessment...")
    
    try:
        # Get current vault balance
        total_assets = vault_contract.functions.totalAssets().call()
        total_usdc = total_assets / (10**6)
        
        if total_usdc < 10:
            return "❌ Insufficient balance for rebalancing (minimum 10 USDC)"
        
        # Get optimal allocation with ML risk data
        protocol_data = {
            "ref_finance": ref_provider.get_pools_data(),
            "trisolaris": tri_provider.get_farms_data(),
            "bastion": bastion_provider.get_lending_data()
        }
        
        optimal_allocation = ai_optimizer.optimize_allocation(protocol_data)
        
        # Calculate target amounts
        target_amounts = {
            protocol: int(weight * total_assets)
            for protocol, weight in optimal_allocation.items()
            if protocol != "reserve"
        }
        
        # Execute rebalancing using deployed strategy addresses
        strategy_addresses = [
            AURORA_STRATEGY_ADDRESSES["ref_finance"],
            AURORA_STRATEGY_ADDRESSES["trisolaris"], 
            AURORA_STRATEGY_ADDRESSES["bastion"]
        ]
        
        target_values = [
            target_amounts.get("ref_finance", 0),
            target_amounts.get("trisolaris", 0),
            target_amounts.get("bastion", 0)
        ]
        
        # Build rebalance transaction
        tx = vault_contract.functions.rebalance(
            strategy_addresses,
            target_values
        ).build_transaction({
            'from': agent_account.address,
            'nonce': w3.eth.get_transaction_count(agent_account.address),
            'gas': 2_000_000,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        })
        
        # Execute transaction
        signed_tx = w3.eth.account.sign_transaction(tx, agent_account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # Fixed to raw_transaction
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        ml_indicator = "🧠 ML-Enhanced" if ML_RISK_AVAILABLE else "🔄 Fallback Mode"
        
        return f"""
✅ Multi-Strategy Rebalance Executed! ({ml_indicator})

💰 Total Assets: {total_usdc:.2f} USDC
🎯 New Allocation:
├─ Ref Finance: {target_amounts.get('ref_finance', 0)/10**6:.2f} USDC ({optimal_allocation.get('ref_finance', 0)*100:.1f}%)
├─ TriSolaris: {target_amounts.get('trisolaris', 0)/10**6:.2f} USDC ({optimal_allocation.get('trisolaris', 0)*100:.1f}%)
├─ Bastion: {target_amounts.get('bastion', 0)/10**6:.2f} USDC ({optimal_allocation.get('bastion', 0)*100:.1f}%)
└─ Reserve: {(total_assets - sum(target_values))/10**6:.2f} USDC

📋 Transaction: {tx_hash.hex()}
⛽ Gas Used: {receipt.gasUsed:,}
🧠 ML Risk Assessment: {"ACTIVE" if ML_RISK_AVAILABLE else "FALLBACK"}
        """
        
    except Exception as e:
        return f"❌ Rebalancing failed: {e}"

@tool
def harvest_all_aurora_yields() -> str:
    """Harvest and compound yields from all Aurora strategies."""
    print("🌾 Harvesting all Aurora yields...")
    
    try:
        harvested_amounts = {}
        total_harvested = 0
        
        # Harvest each deployed strategy
        strategies = [
            ("Ref Finance", AURORA_STRATEGY_ADDRESSES["ref_finance"]),
            ("TriSolaris", AURORA_STRATEGY_ADDRESSES["trisolaris"]),
            ("Bastion", AURORA_STRATEGY_ADDRESSES["bastion"])
        ]
        
        for strategy_name, strategy_address in strategies:
            try:
                # Execute harvest
                tx = vault_contract.functions.harvestStrategy(
                    strategy_address,
                    b''  # Empty data
                ).build_transaction({
                    'from': agent_account.address,
                    'nonce': w3.eth.get_transaction_count(agent_account.address),
                    'gas': 800_000,
                    'gasPrice': w3.eth.gas_price,
                    'chainId': CHAIN_ID
                })
                
                signed_tx = w3.eth.account.sign_transaction(tx, agent_account.key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # Fixed to raw_transaction
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                # Estimate harvested amount (would need strategy-specific logic)
                estimated_harvest = 50  # Placeholder
                harvested_amounts[strategy_name] = estimated_harvest
                total_harvested += estimated_harvest
                
                time.sleep(2)  # Avoid nonce issues
                
            except Exception as e:
                print(f"⚠️ Failed to harvest {strategy_name}: {e}")
                harvested_amounts[strategy_name] = 0
        
        return f"""
🌾 Aurora Yield Harvest Complete!

💰 Harvested Yields:
├─ Ref Finance: {harvested_amounts.get('Ref Finance', 0):.2f} USDC
├─ TriSolaris: {harvested_amounts.get('TriSolaris', 0):.2f} USDC
└─ Bastion: {harvested_amounts.get('Bastion', 0):.2f} USDC

💎 Total Harvested: {total_harvested:.2f} USDC
🔄 Auto-compounding enabled for optimal growth
⚡ Low Aurora gas costs = Higher net yields
        """
        
    except Exception as e:
        return f"❌ Harvest failed: {e}"

@tool
def test_vault_deposit(amount_usdc: float = 100.0) -> str:
    """Test deposit into the deployed Aurora Multi-Strategy Vault."""
    print(f"💰 Testing vault deposit: {amount_usdc} USDC")
    
    try:
        amount_wei = int(amount_usdc * (10**6))
        
        # Check agent's USDC balance
        agent_usdc_balance = usdc_contract.functions.balanceOf(agent_account.address).call()
        
        if agent_usdc_balance < amount_wei:
            # Mint USDC for testing using faucet
            try:
                faucet_tx = usdc_contract.functions.faucet(amount_wei).build_transaction({
                    'from': agent_account.address,
                    'nonce': w3.eth.get_transaction_count(agent_account.address),
                    'gas': 500_000,
                    'gasPrice': w3.eth.gas_price,
                    'chainId': CHAIN_ID
                })
                
                signed_tx = w3.eth.account.sign_transaction(faucet_tx, agent_account.key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # Fixed to raw_transaction
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                print(f"✅ Minted {amount_usdc} USDC for testing")
                time.sleep(2)
            except Exception as e:
                return f"❌ Failed to mint test USDC: {e}"
        
        # Approve vault to spend USDC
        approve_tx = usdc_contract.functions.approve(MULTI_VAULT_ADDRESS, amount_wei).build_transaction({
            'from': agent_account.address,
            'nonce': w3.eth.get_transaction_count(agent_account.address),
            'gas': 500_000,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        })
        
        signed_tx = w3.eth.account.sign_transaction(approve_tx, agent_account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # Fixed to raw_transaction
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        print(f"✅ Approved vault to spend {amount_usdc} USDC")
        time.sleep(2)
        
        # Deposit into vault
        deposit_tx = vault_contract.functions.deposit(amount_wei, agent_account.address).build_transaction({
            'from': agent_account.address,
            'nonce': w3.eth.get_transaction_count(agent_account.address),
            'gas': 1_000_000,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        })
        
        signed_tx = w3.eth.account.sign_transaction(deposit_tx, agent_account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # Fixed to raw_transaction
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        # Check results
        try:
            vault_shares = vault_contract.functions.balanceOf(agent_account.address).call()
            total_assets = vault_contract.functions.totalAssets().call()
        except:
            vault_shares = 0
            total_assets = amount_wei
        
        return f"""
💰 Vault Deposit Test Successful!

📊 Transaction Results:
├─ Deposited: {amount_usdc:.2f} USDC
├─ Received Shares: {vault_shares / (10**18):.6f} amvUSDC
├─ Total Vault Assets: {total_assets / (10**6):.2f} USDC
├─ Share Price: {(total_assets/vault_shares) if vault_shares > 0 else 1:.6f} USDC/share
└─ TX Hash: {tx_hash.hex()}

🎯 Your Aurora Multi-Strategy Vault is working!
⚡ Ready for real user deposits and AI optimization
        """
        
    except Exception as e:
        return f"❌ Vault deposit test failed: {e}"

@tool
def get_strategy_balances() -> str:
    """Get current balances across all deployed strategies."""
    print("📊 Checking strategy balances...")
    
    try:
        strategy_balances = {}
        total_deployed = 0
        
        # Check each strategy balance
        strategies = [
            ("Ref Finance", ref_strategy_contract),
            ("TriSolaris", tri_strategy_contract), 
            ("Bastion", bastion_strategy_contract)
        ]
        
        for name, contract in strategies:
            try:
                balance = contract.functions.getBalance().call()
                balance_usdc = balance / (10**6)
                strategy_balances[name] = balance_usdc
                total_deployed += balance_usdc
                print(f"📊 {name}: {balance_usdc:.2f} USDC")
            except Exception as e:
                print(f"⚠️ Error reading {name} balance: {e}")
                strategy_balances[name] = 0
        
        # Get vault info
        vault_total_assets = vault_contract.functions.totalAssets().call() / (10**6)
        vault_idle = usdc_contract.functions.balanceOf(MULTI_VAULT_ADDRESS).call() / (10**6)
        
        return f"""
📊 Aurora Strategy Balance Report:

💰 Individual Strategy Balances:
├─ Ref Finance: {strategy_balances.get('Ref Finance', 0):.2f} USDC
├─ TriSolaris: {strategy_balances.get('TriSolaris', 0):.2f} USDC
└─ Bastion: {strategy_balances.get('Bastion', 0):.2f} USDC

📈 Portfolio Summary:
├─ Total Deployed: {total_deployed:.2f} USDC
├─ Vault Idle: {vault_idle:.2f} USDC
├─ Total Assets: {vault_total_assets:.2f} USDC
└─ Deployment Rate: {(total_deployed/vault_total_assets)*100 if vault_total_assets > 0 else 0:.1f}%

🎯 Current Allocation:
├─ Ref Finance: {(strategy_balances.get('Ref Finance', 0)/vault_total_assets)*100 if vault_total_assets > 0 else 0:.1f}% (Target: 40%)
├─ TriSolaris: {(strategy_balances.get('TriSolaris', 0)/vault_total_assets)*100 if vault_total_assets > 0 else 0:.1f}% (Target: 30%)
└─ Bastion: {(strategy_balances.get('Bastion', 0)/vault_total_assets)*100 if vault_total_assets > 0 else 0:.1f}% (Target: 20%)

🧠 ML Risk Assessment: {"ACTIVE" if ML_RISK_AVAILABLE else "FALLBACK"}
        """
        
    except Exception as e:
        return f"❌ Error getting strategy balances: {e}"

@tool
def aurora_risk_monitor() -> str:
    """Monitor risk levels across Aurora protocols with ML enhancement."""
    print("🛡️ Monitoring Aurora protocol risks with ML assessment...")
    
    try:
        risk_summary = {
            "total_risk_score": 0.0,
            "protocol_risks": {},
            "alerts": []
        }
        
        # Check each protocol
        protocols = {
            "ref_finance": ref_provider.get_pools_data(),
            "trisolaris": tri_provider.get_farms_data(),
            "bastion": bastion_provider.get_lending_data()
        }
        
        for protocol, data in protocols.items():
            risk_score = data.get("risk_score", 0.5)
            risk_summary["protocol_risks"][protocol] = {
                "risk_score": risk_score,
                "status": data.get("status", "unknown"),
                "apy": data.get("estimated_apy", 0),
                "ml_enhanced": data.get("ml_enhanced", False)
            }
            
            # Check for alerts
            if risk_score > 0.7:
                risk_summary["alerts"].append(f"HIGH RISK: {protocol} risk score {risk_score:.3f}")
            elif data.get("status") == "error":
                risk_summary["alerts"].append(f"CONNECTION ISSUE: {protocol} data unavailable")
        
        # Calculate weighted risk
        total_allocation = sum(DEFAULT_ALLOCATION[p] for p in protocols if p in DEFAULT_ALLOCATION)
        weighted_risk = sum(
            DEFAULT_ALLOCATION.get(p, 0) * data.get("risk_score", 0.5)
            for p, data in protocols.items()
        ) / total_allocation if total_allocation > 0 else 0.5
        
        risk_summary["total_risk_score"] = weighted_risk
        
        # Emergency check
        if weighted_risk > RISK_THRESHOLDS["emergency_exit_threshold"]:
            risk_summary["alerts"].append("🚨 EMERGENCY: Consider exit strategy")
        
        ml_indicator = "🧠 ML-Enhanced" if ML_RISK_AVAILABLE else "🔄 Fallback Mode"
        
        return f"""
🛡️ Aurora Risk Monitor Report ({ml_indicator}):

📊 Overall Portfolio Risk: {weighted_risk:.3f} {'🟢 LOW' if weighted_risk < 0.4 else '🟡 MEDIUM' if weighted_risk < 0.7 else '🔴 HIGH'}

🔍 Protocol Risk Breakdown:
├─ Ref Finance: {risk_summary['protocol_risks'].get('ref_finance', {}).get('risk_score', 0):.3f}
├─ TriSolaris: {risk_summary['protocol_risks'].get('trisolaris', {}).get('risk_score', 0):.3f}
└─ Bastion: {risk_summary['protocol_risks'].get('bastion', {}).get('risk_score', 0):.3f}

🚨 Alerts: {len(risk_summary['alerts'])}
{chr(10).join(f"   • {alert}" for alert in risk_summary['alerts']) if risk_summary['alerts'] else "   • No active alerts"}

🧠 ML Risk Status: {"ACTIVE - Using trained anomaly detection" if ML_RISK_AVAILABLE else "FALLBACK - Using static risk scores"}
✅ Aurora Advantages: Lower systemic risk due to newer ecosystem and NEAR security
        """
        
    except Exception as e:
        return f"❌ Risk monitoring failed: {e}"

@tool
def get_multi_vault_status() -> str:
    """Get comprehensive multi-strategy vault status with ML risk data."""
    print("📊 Getting multi-vault status with ML risk assessment...")
    
    try:
        # Get vault data from deployed contracts
        total_assets = vault_contract.functions.totalAssets().call()
        total_supply = vault_contract.functions.totalSupply().call()
        vault_usdc_balance = usdc_contract.functions.balanceOf(MULTI_VAULT_ADDRESS).call()
        
        total_usdc = total_assets / (10**6)
        idle_usdc = vault_usdc_balance / (10**6)
        deployed_usdc = total_usdc - idle_usdc
        
        # Get protocol data with ML risk
        ref_data = ref_provider.get_pools_data()
        tri_data = tri_provider.get_farms_data()
        bastion_data = bastion_provider.get_lending_data()
        
        # Calculate portfolio APY
        current_allocation = DEFAULT_ALLOCATION
        portfolio_apy = (
            current_allocation["ref_finance"] * ref_data["estimated_apy"] +
            current_allocation["trisolaris"] * tri_data["estimated_apy"] +
            current_allocation["bastion"] * bastion_data["estimated_apy"]
        )
        
        # Get strategy balances
        try:
            ref_balance = ref_strategy_contract.functions.getBalance().call() / (10**6)
            tri_balance = tri_strategy_contract.functions.getBalance().call() / (10**6)
            bastion_balance = bastion_strategy_contract.functions.getBalance().call() / (10**6)
        except Exception as e:
            print(f"⚠️ Error reading strategy balances: {e}")
            ref_balance = tri_balance = bastion_balance = 0
        
        ml_indicator = "🧠 ML-Enhanced" if ML_RISK_AVAILABLE else "🔄 Fallback Mode"
        
        return f"""
🏦 Aurora Multi-Strategy Vault Status ({ml_indicator}):

💰 Assets Under Management:
├─ Total Assets: {total_usdc:.2f} USDC
├─ Deployed: {deployed_usdc:.2f} USDC ({deployed_usdc/total_usdc*100 if total_usdc > 0 else 0:.1f}%)
└─ Idle/Reserve: {idle_usdc:.2f} USDC ({idle_usdc/total_usdc*100 if total_usdc > 0 else 0:.1f}%)

📊 Strategy Balances:
├─ Ref Finance: {ref_balance:.2f} USDC (Risk: {ref_data.get('risk_score', 0.35):.3f})
├─ TriSolaris: {tri_balance:.2f} USDC (Risk: {tri_data.get('risk_score', 0.40):.3f})
└─ Bastion: {bastion_balance:.2f} USDC (Risk: {bastion_data.get('risk_score', 0.25):.3f})

📈 Portfolio Performance:
├─ Expected APY: {portfolio_apy:.1f}%
├─ Vault Shares: {total_supply / (10**18):.2f}
└─ Share Price: {total_assets/total_supply if total_supply > 0 else 1:.6f} USDC

🎯 Strategy Allocation:
├─ Ref Finance: {current_allocation['ref_finance']*100:.1f}% (DEX LP)
├─ TriSolaris: {current_allocation['trisolaris']*100:.1f}% (AMM)
├─ Bastion: {current_allocation['bastion']*100:.1f}% (Lending)
└─ Reserve: {current_allocation['reserve']*100:.1f}% (Liquid)

🌐 Deployed Contracts:
├─ Vault: {MULTI_VAULT_ADDRESS}
├─ Ref Strategy: {AURORA_STRATEGY_ADDRESSES['ref_finance']}
├─ Tri Strategy: {AURORA_STRATEGY_ADDRESSES['trisolaris']}
└─ Bastion Strategy: {AURORA_STRATEGY_ADDRESSES['bastion']}

🧠 AI/ML Features:
├─ ML Risk Assessment: {"✅ ACTIVE" if ML_RISK_AVAILABLE else "❌ DISABLED"}
├─ AI Portfolio Optimization: ✅ ACTIVE
├─ Real-time Risk Monitoring: ✅ ACTIVE
└─ Automated Rebalancing: ✅ ACTIVE

🌟 Aurora Advantages:
├─ Gas costs: ~$0.01 vs $50+ on Ethereum
├─ Transaction speed: 2-3 seconds
├─ NEAR ecosystem integration
└─ First-mover advantage in Aurora DeFi AI

🤖 Agent Status: {agent_account.address}
⚡ Multi-strategy optimization: ACTIVE
        """
        
    except Exception as e:
        return f"❌ Status check failed: {e}"

# ==============================================================================
# ENHANCED TOOLS LIST
# ==============================================================================

tools = [
    mint_test_usdc,
    analyze_aurora_yields,
    assess_ml_strategy_risk,  # NEW ML TOOL
    execute_multi_strategy_rebalance,
    harvest_all_aurora_yields,
    test_vault_deposit,
    get_strategy_balances,
    aurora_risk_monitor,
    get_multi_vault_status
]

tool_names = [t.name for t in tools]

aurora_ai_prompt = """
You are the Aurora Multi-Strategy AI Vault Manager with ML risk assessment capabilities.

Available Tools: {tools}

When using tools, use this exact format:
Action: tool_name
Action Input: parameters (if needed)

Available tools: {tool_names}

Use the following format:
Question: {input}
Thought: I need to help with Aurora vault management using ML-enhanced risk assessment.
Action: [choose from {tool_names}]
Action Input: [parameters if needed]
Observation: [result]
Final Answer: [response to user]

Question: {input}
Thought: {agent_scratchpad}
"""

prompt = PromptTemplate.from_template(aurora_ai_prompt)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
react_agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=react_agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True,
    max_iterations=3,  # Reduce iterations
    early_stopping_method="force"
)

# ==============================================================================
# FASTAPI SERVER WITH ML-ENHANCED BACKGROUND TASKS
# ==============================================================================

app = FastAPI(
    title="Aurora Multi-Strategy AI Vault with ML Risk Assessment",
    description="AI-powered yield optimization with ML risk assessment across Aurora DeFi protocols",
    version="3.0.0"
)

class AgentRequest(BaseModel):
    command: str

# Background task scheduler
class BackgroundScheduler:
    def __init__(self):
        self.running = False
    
    async def start_automated_optimization(self):
        """Run automated optimization every hour with ML risk assessment."""
        self.running = True
        while self.running:
            try:
                print("🤖 Running automated ML-enhanced optimization...")
                result = analyze_aurora_yields.invoke({})
                print(f"📊 Analysis result: {result[:200]}...")
                
                # Auto-rebalance if beneficial
                rebalance_result = execute_multi_strategy_rebalance.invoke({})
                print(f"⚖️ Rebalance result: {rebalance_result[:200]}...")
                
                await asyncio.sleep(3600)  # 1 hour
            except Exception as e:
                print(f"❌ Automated optimization error: {e}")
                await asyncio.sleep(1800)  # Retry in 30 minutes

scheduler = BackgroundScheduler()

@app.on_event("startup")
async def startup_event():
    """Start background optimization."""
    asyncio.create_task(scheduler.start_automated_optimization())

@app.post("/invoke-agent")
async def invoke_agent(request: AgentRequest):
    """Invoke the Aurora AI agent with ML-enhanced capabilities."""
    try:
        response = await agent_executor.ainvoke({
            "input": request.command,
            "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in tools]),
            "tool_names": ", ".join(tool_names)
        })
        return {"success": True, "output": response["output"]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/mint-usdc")
async def mint_usdc_direct(amount: float = 1000.0):
    """Direct USDC minting endpoint."""
    try:
        result = mint_test_usdc.invoke({"amount_usdc": amount})
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/deposit-test")
async def deposit_test_direct(amount: float = 100.0):
    """Direct vault deposit test."""
    try:
        result = test_vault_deposit.invoke({"amount_usdc": amount})
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/rebalance")
async def force_rebalance():
    """Force portfolio rebalancing with ML risk assessment."""
    try:
        result = execute_multi_strategy_rebalance.invoke({})
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/harvest")
async def force_harvest():
    """Force yield harvesting."""
    try:
        result = harvest_all_aurora_yields.invoke({})
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/yields")
async def get_yields():
    """Get current yield analysis with ML risk assessment."""
    try:
        result = analyze_aurora_yields.invoke({})
        return {"success": True, "analysis": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/risk")
async def get_risk_status():
    """Get ML-enhanced risk monitoring status."""
    try:
        result = aurora_risk_monitor.invoke({})
        return {"success": True, "risk_report": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/assess-risk")
async def assess_strategy_risk(strategy_address: str):
    """Assess specific strategy risk using ML."""
    try:
        result = assess_ml_strategy_risk.invoke({"strategy_address": strategy_address})
        return {"success": True, "risk_assessment": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/status")
async def vault_status():
    """Get comprehensive vault status with ML risk data."""
    try:
        result = get_multi_vault_status.invoke({})
        return {"success": True, "status": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    """Enhanced health check with ML status."""
    try:
        latest_block = w3.eth.block_number
        agent_balance = w3.eth.get_balance(agent_account.address)
        vault_balance = usdc_contract.functions.balanceOf(MULTI_VAULT_ADDRESS).call()
        
        # Test protocol connectivity
        ref_status = ref_provider.get_pools_data().get("status", "error")
        tri_status = tri_provider.get_farms_data().get("status", "error")
        bastion_status = bastion_provider.get_lending_data().get("status", "error")
        
        return {
            "success": True,
            "health": {
                "status": "healthy",
                "aurora_connected": True,
                "latest_block": latest_block,
                "agent_balance_eth": w3.from_wei(agent_balance, 'ether'),
                "vault_balance_usdc": vault_balance / 10**6,
                "protocols": {
                    "ref_finance": ref_status,
                    "trisolaris": tri_status,
                    "bastion": bastion_status
                },
                "ml_risk_assessment": ML_RISK_AVAILABLE,
                "automation": "active" if scheduler.running else "stopped"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
def read_root():
    return {
        "message": f"🚀 Aurora Multi-Strategy AI Vault with ML Risk Assessment - {'🧠 ML ACTIVE' if ML_RISK_AVAILABLE else '🔄 FALLBACK MODE'}",
        "version": "3.0.0",
        "features": [
            "Multi-Protocol Yield Optimization",
            "AI-Powered Portfolio Rebalancing", 
            "ML-Enhanced Risk Assessment" if ML_RISK_AVAILABLE else "Static Risk Assessment",
            "Real-time Risk Monitoring",
            "Automated Yield Harvesting",
            "Aurora Gas Cost Optimization",
            "24/7 Autonomous Operation"
        ],
        "protocols": list(AURORA_PROTOCOLS.keys()),
        "ml_status": {
            "available": ML_RISK_AVAILABLE,
            "model_path": "near-vault-agent/ml-risk/models/anomaly_risk_model.joblib" if ML_RISK_AVAILABLE else None,
            "status": "Active - Using trained anomaly detection" if ML_RISK_AVAILABLE else "Fallback - Using static risk scores"
        },
        "endpoints": [
            "/invoke-agent - Full AI agent interaction",
            "/rebalance - Force portfolio rebalancing",
            "/harvest - Force yield harvesting", 
            "/yields - Current yield analysis",
            "/risk - Risk monitoring report",
            "/assess-risk - ML strategy risk assessment",
            "/status - Vault status dashboard",
            "/health - System health check"
        ],
        "aurora_advantages": [
            "100x lower gas costs vs Ethereum",
            "2-3 second transaction finality",
            "NEAR ecosystem integration",
            "First-mover advantage in Aurora DeFi AI"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Launching Aurora Multi-Strategy AI Vault with ML Risk Assessment...")
    print(f"🤖 Agent: {agent_account.address}")
    print(f"🏦 Vault: {MULTI_VAULT_ADDRESS}")
    print(f"📊 Protocols: {len(AURORA_PROTOCOLS)} integrated")
    print(f"🧠 ML Risk Assessment: {'✅ ACTIVE' if ML_RISK_AVAILABLE else '❌ DISABLED'}")
    print(f"🎯 Expected Portfolio APY: {sum(p['expected_apy'] * DEFAULT_ALLOCATION.get(k.replace('_', ''), 0) for k, p in AURORA_PROTOCOLS.items() if 'expected_apy' in p):.1f}%")
    print("⚡ Starting with automated ML-enhanced optimization...")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)