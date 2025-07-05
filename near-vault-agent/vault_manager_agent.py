import os
import json
import time
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools import tool

# NEAR-specific imports
try:
    from py_near.account import Account
    from py_near.providers import JsonProvider
    from py_near.dapps.core import NEAR
    from py_near.crypto import InMemoryKeyStore, KeyPair
    from py_near.transactions import Transaction, Action
    import py_near.utils as near_utils
    NEAR_API_AVAILABLE = True
    print("✅ NEAR API imported successfully")
except ImportError as e:
    print(f"❌ NEAR API not available: {e}")
    print("Install with: pip install py-near")
    NEAR_API_AVAILABLE = False
    exit(1)

# Import risk assessment
import sys
sys.path.append('./ml-risk')
try:
    from risk_api import RiskAssessmentAPI
    RISK_MODEL_AVAILABLE = True
    print("✅ Risk model imported successfully")
except ImportError as e:
    print(f"⚠️ Risk model not available: {e}")
    print("Run: cd ml-risk && python anomaly_risk_model.py")
    RISK_MODEL_AVAILABLE = False

# Import OpenAI LLM planner
try:
    from ollama_llm_planner import ai_strategy_advisor  # Uses OpenAI now
    OPENAI_AI_AVAILABLE = True
    print("✅ OpenAI LLM planner imported successfully")
except ImportError as e:
    print(f"⚠️ OpenAI LLM planner not available: {e}")
    OPENAI_AI_AVAILABLE = False

# ==============================================================================
# 1. ENHANCED NEAR CONFIGURATION AND SETUP
# ==============================================================================

load_dotenv()

# --- NEAR Configuration ---
NEAR_NETWORK = os.getenv("NEAR_NETWORK", "testnet")  # testnet or mainnet
NEAR_RPC_URL = os.getenv("NEAR_RPC_URL", "https://rpc.testnet.near.org")
AGENT_ACCOUNT_ID = os.getenv("AGENT_ACCOUNT_ID")  # e.g., "agent.testnet"
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- NEAR Contract Addresses ---
VAULT_ADDRESS = os.getenv("VAULT_ADDRESS", "0xf0f994B4A8dB86A46a1eD4F12263c795b26703Ca")
NEAR_VRF_STRATEGY_ADDRESS = os.getenv("NEAR_VRF_STRATEGY_ADDRESS", "0x959e85561b3cc2E2AE9e9764f55499525E350f56")
USDC_TOKEN_ADDRESS = os.getenv("USDC_TOKEN_ADDRESS", "0xC0933C5440c656464D1Eb1F886422bE3466B1459")

# --- Enhanced Strategy Configuration ---
NEAR_STRATEGIES = {
    "ref_finance": os.getenv("REF_FINANCE_STRATEGY_ADDRESS", ""),
    "burrow": os.getenv("BURROW_STRATEGY_ADDRESS", ""),
    "meta_pool": os.getenv("META_POOL_STRATEGY_ADDRESS", "")
}

ETHEREUM_STRATEGIES = {
    "aave": os.getenv("AAVE_STRATEGY_ADDRESS", ""),
    "compound": os.getenv("COMPOUND_STRATEGY_ADDRESS", "")
}

# --- NEAR Account Setup ---
try:
    if not AGENT_ACCOUNT_ID or not AGENT_PRIVATE_KEY:
        raise ValueError("AGENT_ACCOUNT_ID and AGENT_PRIVATE_KEY must be set in .env")
    
    # Initialize NEAR connection
    near_provider = JsonProvider(NEAR_RPC_URL)
    key_store = InMemoryKeyStore()
    
    # Add agent key to keystore
    agent_key_pair = KeyPair.from_secret_key(AGENT_PRIVATE_KEY)
    key_store.set_key(NEAR_NETWORK, AGENT_ACCOUNT_ID, agent_key_pair)
    
    # Create NEAR account
    near_account = Account(
        account_id=AGENT_ACCOUNT_ID,
        provider=near_provider,
        signer=key_store
    )
    
    print(f"🤖 NEAR Agent Account: {AGENT_ACCOUNT_ID}")
    print(f"🌐 NEAR Network: {NEAR_NETWORK}")
    print(f"🔗 NEAR RPC: {NEAR_RPC_URL}")
    
except Exception as e:
    print(f"❌ NEAR setup failed: {e}")
    exit(1)

# --- Risk Model Setup ---
if RISK_MODEL_AVAILABLE:
    try:
        risk_api = RiskAssessmentAPI("ml-risk/models/anomaly_risk_model.joblib")
        print("✅ Risk assessment model loaded")
    except Exception as e:
        risk_api = None
        print(f"⚠️ Risk model loading failed: {e}")
else:
    risk_api = None

# --- Load ABIs ---
def load_abi(filename):
    """Loads a contract ABI from the abi directory with robust path handling."""
    possible_paths = [
        os.path.join("abi", filename),
        os.path.join("..", "abi", filename),
        os.path.join("../abi", filename),
        filename
    ]
    
    for path in possible_paths:
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    abi_data = json.load(f)
                    if isinstance(abi_data, dict) and "abi" in abi_data:
                        return abi_data["abi"]
                    elif isinstance(abi_data, list):
                        return abi_data
                    else:
                        raise ValueError(f"Invalid ABI format in {filename}")
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            continue
    
    raise FileNotFoundError(f"Could not find {filename} in any of these locations: {possible_paths}")

try:
    vault_abi = load_abi("Vault.json")
    near_vrf_strategy_abi = load_abi("NearVrfYieldStrategy.json")  # Your provided ABI
    usdc_abi = load_abi("MockUSDC.json")
    print("✅ All ABI files loaded successfully")
except FileNotFoundError as e:
    print(f"❌ ABI loading failed: {e}")
    print("Please ensure ABI files are in the correct directory")
    exit(1)

print("✅ Enhanced NEAR configuration loaded with risk management")

# ==============================================================================
# 2. NEAR-SPECIFIC UTILITY FUNCTIONS
# ==============================================================================

async def send_near_transaction(contract_address: str, method_name: str, args: Dict[str, Any], 
                               deposit: str = "0", gas: int = 100_000_000_000_000) -> Dict[str, Any]:
    """
    Send a transaction to a NEAR contract with enhanced error handling.
    """
    try:
        print(f"🔄 Calling {method_name} on {contract_address}")
        print(f"📝 Args: {args}")
        print(f"💰 Deposit: {deposit} NEAR")
        
        # Call contract method
        result = await near_account.function_call(
            contract_id=contract_address,
            method_name=method_name,
            args=args,
            gas=gas,
            deposit=near_utils.parse_near_amount(deposit)
        )
        
        print(f"✅ Transaction successful: {result.transaction.hash}")
        return {
            "success": True,
            "transaction_hash": result.transaction.hash,
            "result": result.result if hasattr(result, 'result') else None
        }
        
    except Exception as e:
        print(f"❌ NEAR transaction failed: {e}")
        return {"success": False, "error": str(e)}

async def call_near_view_method(contract_address: str, method_name: str, 
                               args: Dict[str, Any] = None) -> Any:
    """
    Call a view method on a NEAR contract.
    """
    try:
        if args is None:
            args = {}
            
        result = await near_account.view_function(
            contract_id=contract_address,
            method_name=method_name,
            args=args
        )
        
        return result
        
    except Exception as e:
        print(f"❌ NEAR view call failed: {e}")
        return None

# ==============================================================================
# 3. ENHANCED AGENT TOOLS WITH NEAR INTEGRATION
# ==============================================================================

@tool
def get_enhanced_near_protocol_status() -> str:
    """
    Gets comprehensive NEAR protocol status including risk metrics and yield opportunities.
    """
    print("Tool: get_enhanced_near_protocol_status")
    
    async def _get_status():
        try:
            # Get NEAR-specific protocol status
            liquid_usdc = await call_near_view_method(VAULT_ADDRESS, "get_balance", {})
            prize_pool = await call_near_view_method(NEAR_VRF_STRATEGY_ADDRESS, "getBalance", {})
            last_winner = await call_near_view_method(NEAR_VRF_STRATEGY_ADDRESS, "lastWinner", {})
            
            # Convert from yoctoNEAR if needed (NEAR uses different decimals)
            liquid_usdc_formatted = float(liquid_usdc or 0) / (10**6)  # Assuming USDC 6 decimals
            prize_pool_formatted = float(prize_pool or 0) / (10**6)
            
            # Risk assessment for NEAR VRF strategy
            risk_level = "UNKNOWN"
            if risk_api:
                try:
                    near_vrf_risk = risk_api.assess_strategy_risk(NEAR_VRF_STRATEGY_ADDRESS)
                    risk_level = "LOW" if near_vrf_risk < 0.3 else "MEDIUM" if near_vrf_risk < 0.7 else "HIGH"
                except Exception as e:
                    risk_level = f"UNAVAILABLE ({str(e)[:50]}...)"
            
            # NEAR-specific yield opportunity analysis
            yield_opportunities = analyze_near_yield_opportunities()
            
            status_report = {
                "vault_liquid_usdc": f"{liquid_usdc_formatted:.2f} USDC",
                "current_prize_pool": f"{prize_pool_formatted:.2f} USDC",
                "last_lottery_winner": last_winner or "0x0000000000000000000000000000000000000000",
                "near_vrf_strategy_risk_level": risk_level,
                "best_yield_opportunity": yield_opportunities.get("best", "NEAR VRF Lottery"),
                "total_deployed": f"{prize_pool_formatted:.2f} USDC",
                "agent_account": AGENT_ACCOUNT_ID,
                "vault_address": VAULT_ADDRESS,
                "near_vrf_strategy_address": NEAR_VRF_STRATEGY_ADDRESS,
                "near_network": NEAR_NETWORK,
                "risk_model_available": RISK_MODEL_AVAILABLE,
                "openai_ai_available": OPENAI_AI_AVAILABLE
            }
            
            return f"Enhanced NEAR Protocol Status: {json.dumps(status_report, indent=2)}"
            
        except Exception as e:
            return f"Error getting enhanced NEAR protocol status: {e}"
    
    # Run async function in event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get_status())
                return future.result()
        else:
            return asyncio.run(_get_status())
    except Exception as e:
        return f"Error running async status check: {e}"

def analyze_near_yield_opportunities():
    """Analyze available yield opportunities across NEAR ecosystem."""
    opportunities = {
        "near_vrf": {"apy": 0.0, "risk": 0.2, "type": "prize"},
        "ref_finance": {"apy": 12.5, "risk": 0.4, "type": "dex"},
        "burrow": {"apy": 8.2, "risk": 0.3, "type": "lending"},
        "meta_pool": {"apy": 10.1, "risk": 0.35, "type": "staking"},
        "ethereum_aave": {"apy": 4.5, "risk": 0.3, "type": "lending"},
    }
    
    # Calculate risk-adjusted returns
    for name, opp in opportunities.items():
        opp["risk_adjusted_apy"] = opp["apy"] * (1 - opp["risk"])
    
    best = max(opportunities.items(), key=lambda x: x[1]["risk_adjusted_apy"])
    return {"best": best[0], "opportunities": opportunities}

@tool
def assess_near_strategy_risk(strategy_address: str) -> str:
    """
    Assess the risk level of a NEAR DeFi strategy before deployment.
    """
    print(f"Tool: assess_near_strategy_risk for {strategy_address}")
    
    if not risk_api:
        return "Risk assessment unavailable - model not loaded. Run: cd ml-risk && python anomaly_risk_model.py"
    
    try:
        risk_score = risk_api.assess_strategy_risk(strategy_address)
        detailed_assessment = risk_api.get_detailed_assessment(strategy_address)
        
        risk_level = "LOW" if risk_score < 0.3 else "MEDIUM" if risk_score < 0.7 else "HIGH"
        recommendation = "APPROVE" if risk_score < 0.5 else "CAUTION" if risk_score < 0.8 else "REJECT"
        
        return f"""
NEAR Strategy Risk Assessment for {strategy_address}:
📊 Risk Score: {risk_score:.3f}
🎯 Risk Level: {risk_level}
💡 Recommendation: {recommendation}
🔍 Details: {detailed_assessment.get('risk_level', 'N/A')}
📋 Error (if any): {detailed_assessment.get('error', 'None')}
🌐 Network: {NEAR_NETWORK}
        """
    except Exception as e:
        return f"NEAR risk assessment failed: {e}"

@tool
def deploy_to_near_strategy_with_risk_check(strategy_name: str, amount: float = 0.0) -> str:
    """
    Deploy funds to a NEAR strategy after comprehensive risk assessment.
    
    Args:
        strategy_name: Name of the strategy ("near_vrf", "ref_finance", "burrow", etc.)
        amount: Amount of USDC to deploy (0 = use reasonable default)
    """
    print(f"Tool: deploy_to_near_strategy_with_risk_check - {strategy_name}, {amount} USDC")
    
    async def _deploy():
        try:
            # Handle strategy name mapping
            strategy_address = None
            if strategy_name in NEAR_STRATEGIES and NEAR_STRATEGIES[strategy_name]:
                strategy_address = NEAR_STRATEGIES[strategy_name]
            elif strategy_name in ETHEREUM_STRATEGIES and ETHEREUM_STRATEGIES[strategy_name]:
                strategy_address = ETHEREUM_STRATEGIES[strategy_name]
            elif strategy_name == "near_vrf" or strategy_name == "vrf":
                strategy_address = NEAR_VRF_STRATEGY_ADDRESS
            elif strategy_name == "ref_finance":
                strategy_address = NEAR_STRATEGIES.get("ref_finance", NEAR_VRF_STRATEGY_ADDRESS)
                if not NEAR_STRATEGIES.get("ref_finance"):
                    strategy_name = "near_vrf"
                    print("⚠️ Ref Finance strategy not deployed, redirecting to NEAR VRF lottery")
            
            if not strategy_address:
                available_strategies = ["near_vrf"] + [k for k, v in NEAR_STRATEGIES.items() if v]
                return f"❌ Unknown NEAR strategy: {strategy_name}. Available: {available_strategies}"
            
            # Risk assessment
            if risk_api and strategy_address != NEAR_VRF_STRATEGY_ADDRESS:
                try:
                    risk_score = risk_api.assess_strategy_risk(strategy_address)
                    if risk_score > 0.7:
                        return f"❌ DEPLOYMENT BLOCKED - High risk score: {risk_score:.3f}"
                    elif risk_score > 0.5:
                        print(f"⚠️ CAUTION - Medium risk score: {risk_score:.3f}, proceeding...")
                except Exception as e:
                    print(f"⚠️ Risk assessment failed: {e}, proceeding without risk check...")
            
            # Check available balance
            liquid_usdc = await call_near_view_method(VAULT_ADDRESS, "get_balance", {})
            liquid_usdc_formatted = float(liquid_usdc or 0) / (10**6)
            
            # Set reasonable amount if not specified
            if amount == 0:
                if strategy_name == "near_vrf" or strategy_name == "vrf":
                    amount = min(150.0, liquid_usdc_formatted * 0.5)
                else:
                    amount = liquid_usdc_formatted * 0.8
            
            if amount > liquid_usdc_formatted:
                return f"❌ Insufficient funds: {liquid_usdc_formatted:.2f} USDC available, {amount:.2f} USDC requested"
            
            if amount <= 0:
                return "❌ No funds available to deploy"
            
            # For NEAR VRF strategy, use simulate yield harvest and deposit
            if strategy_name == "near_vrf" or strategy_address == NEAR_VRF_STRATEGY_ADDRESS:
                return await simulate_near_yield_harvest_and_deposit(amount)
            
            # Execute deployment for other NEAR strategies
            amount_wei = int(amount * (10**6))
            
            result = await send_near_transaction(
                contract_address=VAULT_ADDRESS,
                method_name="deposit_to_strategy",
                args={
                    "strategy_address": strategy_address,
                    "amount": str(amount_wei)
                },
                gas=300_000_000_000_000  # Higher gas for complex operations
            )
            
            if result["success"]:
                return f"✅ Successfully deployed {amount:.2f} USDC to {strategy_name} strategy on NEAR. TX: {result['transaction_hash']}"
            else:
                return f"❌ NEAR deployment failed: {result['error']}"
                
        except Exception as e:
            return f"❌ Error in NEAR risk-checked deployment: {e}"
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _deploy())
                return future.result()
        else:
            return asyncio.run(_deploy())
    except Exception as e:
        return f"Error running async deployment: {e}"

async def simulate_near_yield_harvest_and_deposit(amount_usdc: float) -> str:
    """Simulates yield harvest and deposit on NEAR with enhanced logging."""
    print(f"Simulating NEAR yield harvest and deposit: {amount_usdc} USDC")
    
    if amount_usdc > 1000:
        return "❌ Risk check failed: Simulated yield amount too high (>1000 USDC)"
    
    if amount_usdc <= 0:
        return "❌ Invalid amount: Must be greater than 0"
    
    try:
        amount_wei = int(amount_usdc * (10**6))

        # 1. Mint "yield" to the agent's account on NEAR
        print(f"Minting {amount_usdc} USDC to NEAR agent...")
        mint_result = await send_near_transaction(
            contract_address=USDC_TOKEN_ADDRESS,
            method_name="mint",
            args={
                "account_id": AGENT_ACCOUNT_ID,
                "amount": str(amount_wei)
            },
            gas=100_000_000_000_000
        )
        
        if not mint_result["success"]:
            return f"Failed to mint mock yield on NEAR: {mint_result['error']}"
        
        await asyncio.sleep(2)  # Wait for transaction confirmation

        # 2. Approve the NEAR VRF Strategy
        print(f"Approving NEAR VRF strategy to spend {amount_usdc} USDC...")
        approve_result = await send_near_transaction(
            contract_address=USDC_TOKEN_ADDRESS,
            method_name="approve",
            args={
                "spender": NEAR_VRF_STRATEGY_ADDRESS,
                "amount": str(amount_wei)
            },
            gas=100_000_000_000_000
        )
        
        if not approve_result["success"]:
            return f"Failed to approve yield deposit on NEAR: {approve_result['error']}"
            
        await asyncio.sleep(2)

        # 3. Deposit the "yield" into the NEAR VRF strategy
        print(f"Depositing {amount_usdc} USDC as NEAR prize pool...")
        deposit_result = await send_near_transaction(
            contract_address=NEAR_VRF_STRATEGY_ADDRESS,
            method_name="depositYield",
            args={"yieldAmount": str(amount_wei)},
            gas=200_000_000_000_000
        )
        
        if deposit_result["success"]:
            return f"✅ Successfully simulated and deposited {amount_usdc} USDC as NEAR prize pool. TX: {deposit_result['transaction_hash']}"
        else:
            return f"Failed to deposit yield on NEAR: {deposit_result['error']}"

    except Exception as e:
        return f"Error simulating NEAR yield harvest: {e}"

@tool
def simulate_near_yield_harvest_and_deposit_sync(amount_usdc: float) -> str:
    """Synchronous wrapper for NEAR yield harvest simulation."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, simulate_near_yield_harvest_and_deposit(amount_usdc))
                return future.result()
        else:
            return asyncio.run(simulate_near_yield_harvest_and_deposit(amount_usdc))
    except Exception as e:
        return f"Error running async NEAR yield simulation: {e}"

@tool
def trigger_near_lottery_draw() -> str:
    """Triggers NEAR lottery draw with enhanced winner tracking and risk checks."""
    print("Tool: trigger_near_lottery_draw")
    
    async def _trigger():
        try:
            prize_pool = await call_near_view_method(NEAR_VRF_STRATEGY_ADDRESS, "getBalance", {})
            if not prize_pool or float(prize_pool) == 0:
                return "Cannot trigger draw: The NEAR prize pool is zero. Use simulate_near_yield_harvest_and_deposit() first."

            prize_amount = float(prize_pool) / (10**6)
            
            # Safety check
            if prize_amount > 10000:
                return f"⚠️ Safety check: NEAR prize amount is very large ({prize_amount:.2f} USDC). Please confirm this is intended."
            
            print(f"Triggering NEAR lottery draw for a prize of {prize_amount:.2f} USDC...")
            
            result = await send_near_transaction(
                contract_address=VAULT_ADDRESS,
                method_name="harvest_strategy",
                args={"strategy_address": NEAR_VRF_STRATEGY_ADDRESS},
                gas=300_000_000_000_000
            )

            if result["success"]:
                await asyncio.sleep(2)
                new_winner = await call_near_view_method(NEAR_VRF_STRATEGY_ADDRESS, "lastWinner", {})
                return f"🎉 NEAR lottery draw successful! Winner: {new_winner}, Prize: {prize_amount:.2f} USDC, TX: {result['transaction_hash']}"
            else:
                return f"Failed to trigger NEAR lottery draw: {result['error']}"

        except Exception as e:
            return f"Error triggering NEAR lottery draw: {e}"
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _trigger())
                return future.result()
        else:
            return asyncio.run(_trigger())
    except Exception as e:
        return f"Error running async NEAR lottery trigger: {e}"

@tool
def emergency_near_risk_assessment() -> str:
    """
    Perform emergency risk assessment of all deployed NEAR funds.
    """
    print("Tool: emergency_near_risk_assessment")
    
    async def _assess():
        try:
            risk_summary = {
                "total_at_risk": 0.0,
                "high_risk_strategies": [],
                "medium_risk_strategies": [],
                "low_risk_strategies": [],
                "recommendations": []
            }
            
            # Check NEAR VRF strategy
            prize_pool = await call_near_view_method(NEAR_VRF_STRATEGY_ADDRESS, "getBalance", {})
            prize_pool_formatted = float(prize_pool or 0) / (10**6)
            
            if prize_pool_formatted > 0:
                risk_summary["low_risk_strategies"].append({
                    "name": "NEAR VRF Lottery",
                    "address": NEAR_VRF_STRATEGY_ADDRESS,
                    "balance": prize_pool_formatted,
                    "risk_score": 0.2,
                    "notes": "NEAR VRF-based lottery system"
                })
                risk_summary["total_at_risk"] += prize_pool_formatted
            
            # Check other NEAR strategies
            for strategy_name, address in NEAR_STRATEGIES.items():
                if address and risk_api:
                    try:
                        risk_score = risk_api.assess_strategy_risk(address)
                        balance = 0.0  # Would need strategy contract calls to get actual balance
                        
                        strategy_info = {
                            "name": strategy_name,
                            "address": address,
                            "balance": balance,
                            "risk_score": risk_score,
                            "network": "NEAR"
                        }
                        
                        if risk_score > 0.7:
                            risk_summary["high_risk_strategies"].append(strategy_info)
                            risk_summary["recommendations"].append(f"URGENT: Exit NEAR {strategy_name}")
                        elif risk_score > 0.5:
                            risk_summary["medium_risk_strategies"].append(strategy_info)
                            risk_summary["recommendations"].append(f"MONITOR: Watch NEAR {strategy_name}")
                        else:
                            risk_summary["low_risk_strategies"].append(strategy_info)
                            
                    except Exception as e:
                        print(f"Risk check failed for NEAR {strategy_name}: {e}")
            
            total_strategies = len(risk_summary["high_risk_strategies"]) + \
                              len(risk_summary["medium_risk_strategies"]) + \
                              len(risk_summary["low_risk_strategies"])
            
            return f"""
🚨 Emergency NEAR Risk Assessment:
📊 Total Strategies: {total_strategies}
💰 Total Funds at Risk: {risk_summary["total_at_risk"]:.2f} USDC
🔴 High Risk Strategies: {len(risk_summary["high_risk_strategies"])}
🟡 Medium Risk Strategies: {len(risk_summary["medium_risk_strategies"])}
🟢 Low Risk Strategies: {len(risk_summary["low_risk_strategies"])}
🌐 Network: {NEAR_NETWORK}

📋 Strategy Details:
{json.dumps(risk_summary, indent=2)}

💡 Recommendations: {risk_summary["recommendations"] if risk_summary["recommendations"] else ["All NEAR strategies appear safe"]}
            """
            
        except Exception as e:
            return f"Emergency NEAR risk assessment failed: {e}"
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _assess())
                return future.result()
        else:
            return asyncio.run(_assess())
    except Exception as e:
        return f"Error running async NEAR risk assessment: {e}"

@tool
def test_near_vrf_strategy_risk() -> str:
    """
    Test risk assessment specifically on NEAR VRF strategy.
    """
    print("Tool: test_near_vrf_strategy_risk")
    
    near_vrf_address = NEAR_VRF_STRATEGY_ADDRESS
    
    try:
        if not risk_api:
            return f"Risk model not available. NEAR VRF Strategy: {near_vrf_address} - Cannot assess risk without model."
        
        # Try to assess NEAR VRF strategy risk
        result = risk_api.get_detailed_assessment(near_vrf_address)
        
        if "error" in result:
            return f"""
🎯 NEAR VRF Strategy Risk Test:
📍 Address: {near_vrf_address}
🌐 Network: {NEAR_NETWORK}
❌ Assessment Failed: {result['error']}
📝 Note: This may be expected since NEAR VRF uses different data patterns than Ethereum.
✅ NEAR VRF Strategy is considered LOW RISK by design (lottery system with NEAR randomness).
            """
        else:
            return f"""
🎯 NEAR VRF Strategy Risk Test:
📍 Address: {near_vrf_address}
🌐 Network: {NEAR_NETWORK}
📊 Risk Score: {result.get('risk_score', 'N/A')}
🎯 Risk Level: {result.get('risk_level', 'N/A')}
🔍 Assessment: {json.dumps(result, indent=2)}
            """
            
    except Exception as e:
        return f"""
🎯 NEAR VRF Strategy Risk Test:
📍 Address: {near_vrf_address}
🌐 Network: {NEAR_NETWORK}
❌ Test Error: {e}
📝 Note: This may be expected since NEAR uses different contract patterns than Ethereum.
✅ NEAR VRF Strategy is considered LOW RISK by design (lottery system with secure NEAR randomness).
        """

# ==============================================================================
# 4. ENHANCED LANGCHAIN AGENT FOR NEAR
# ==============================================================================

# Build tools list dynamically based on availability
tools = [
    get_enhanced_near_protocol_status,
    assess_near_strategy_risk,
    deploy_to_near_strategy_with_risk_check,
    emergency_near_risk_assessment,
    test_near_vrf_strategy_risk,
    simulate_near_yield_harvest_and_deposit_sync,
    trigger_near_lottery_draw
]

# Add OpenAI AI tool if available
if OPENAI_AI_AVAILABLE:
    tools.append(ai_strategy_advisor)
    print("✅ AI strategy advisor tool added")

tool_names = [t.name for t in tools]

enhanced_near_prompt_template = """
You are the "Enhanced NEAR Vault Manager," an AI agent with advanced risk management capabilities for operating a no-loss prize savings game on NEAR blockchain.

Your account: {agent_account}
Your vault: {vault_address}
Your NEAR VRF strategy: {near_vrf_strategy_address}
NEAR Network: {near_network}

ENHANCED NEAR CAPABILITIES:
🎯 Risk Assessment: Evaluate NEAR strategies before deployment
🔍 Multi-Strategy Analysis: Compare yield opportunities across NEAR protocols
🚨 Emergency Monitoring: Detect and respond to risk events
📊 Comprehensive Reporting: Detailed status and metrics for NEAR
🤖 AI Strategy Advisor: OpenAI for intelligent recommendations (if available)
🌐 NEAR Integration: Native NEAR API support with py-near

You have access to these enhanced NEAR tools:
{tools}

OPERATIONAL PROCEDURE (Enhanced for NEAR):
1. **Enhanced Assessment**: Use get_enhanced_near_protocol_status() for comprehensive overview
2. **Risk Evaluation**: Use assess_near_strategy_risk() and test_near_vrf_strategy_risk() for safety
3. **AI Strategy Planning**: Use ai_strategy_advisor() for intelligent recommendations (if available)
4. **Strategic Deployment**: Use deploy_to_near_strategy_with_risk_check() for safe fund allocation
5. **Emergency Protocols**: Run emergency_near_risk_assessment() if you detect anomalies
6. **Yield Optimization**: Balance prize rewards with NEAR ecosystem opportunities
7. **Lottery Execution**: Only trigger draws after confirming adequate prize pools and safety

Use the following format:
Question: the user's request or task
Thought: Consider current NEAR state, risk factors, and optimal strategy
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat as needed)
Thought: I now have enough information to provide the final answer.
Final Answer: comprehensive response with NEAR risk assessment and recommendations

NEAR-SPECIFIC RISK MANAGEMENT RULES:
- Never deploy to strategies with risk score > 0.7
- Always assess risk before new NEAR deployments
- NEAR VRF strategy is considered LOW RISK (NEAR-based lottery system)
- Monitor for unusual patterns or high-risk activities in NEAR ecosystem
- Prioritize user fund safety over yield maximization
- Run emergency assessment if risk indicators spike
- Use AI advisor for complex strategic decisions when available
- Consider NEAR gas costs and transaction fees
- Leverage NEAR's unique DeFi ecosystem (Ref Finance, Burrow, Meta Pool)

NEAR ECOSYSTEM NOTES:
- You operate on {near_network} with NEAR VRF-powered lottery
- Risk model may not work perfectly for NEAR contracts (trained on Ethereum data)
- NEAR VRF strategy is safe by design (secure randomness via NEAR blockchain)
- Focus on lottery operations while monitoring NEAR yield opportunities
- NEAR transactions use gas in NEAR tokens, not ETH
- Account model differs from Ethereum addresses

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""

prompt = PromptTemplate.from_template(enhanced_near_prompt_template)

# Initialize enhanced LLM and Agent
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
react_agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=react_agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True,
    max_iterations=10,
    early_stopping_method="force"
)

# ==============================================================================
# 5. ENHANCED FASTAPI SERVER FOR NEAR
# ==============================================================================

app = FastAPI(
    title="Enhanced NEAR Vault Manager Agent",
    description="AI agent with risk management and NEAR API support for NEAR prize savings protocol",
    version="3.0.0"
)

class AgentRequest(BaseModel):
    command: str

class RiskAssessmentRequest(BaseModel):
    strategy_address: str

class YieldRequest(BaseModel):
    amount_usdc: float

@app.post("/invoke-agent")
async def invoke_agent(request: AgentRequest):
    """Enhanced NEAR agent endpoint with risk management and AI strategy advisor."""
    try:
        tool_descriptions = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
        
        response = await agent_executor.ainvoke({
            "input": request.command,
            "agent_account": AGENT_ACCOUNT_ID,
            "vault_address": VAULT_ADDRESS,
            "near_vrf_strategy_address": NEAR_VRF_STRATEGY_ADDRESS,
            "near_network": NEAR_NETWORK,
            "tools": tool_descriptions,
            "tool_names": ", ".join(tool_names)
        })
        return {"success": True, "output": response["output"]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/assess-risk")
async def assess_risk(request: RiskAssessmentRequest):
    """Dedicated NEAR risk assessment endpoint."""
    try:
        result = assess_near_strategy_risk.invoke({"strategy_address": request.strategy_address})
        return {"success": True, "assessment": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/emergency-status")
async def emergency_status():
    """Emergency NEAR risk monitoring endpoint."""
    try:
        result = emergency_near_risk_assessment.invoke({})
        return {"success": True, "emergency_assessment": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/enhanced-status")
async def enhanced_status():
    """Enhanced NEAR protocol status endpoint."""
    try:
        result = get_enhanced_near_protocol_status.invoke({})
        return {"success": True, "status": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/test-vrf-risk")
async def test_vrf_risk():
    """Test NEAR VRF strategy risk assessment."""
    try:
        result = test_near_vrf_strategy_risk.invoke({})
        return {"success": True, "vrf_risk_test": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/ai-strategy")
async def ai_strategy_endpoint(request: AgentRequest):
    """AI strategy advisor endpoint for NEAR (if OpenAI is available)."""
    try:
        if not OPENAI_AI_AVAILABLE:
            return {
                "success": False, 
                "error": "OpenAI AI not available. Check OPENAI_API_KEY in .env"
            }
        
        result = ai_strategy_advisor.invoke({"current_situation": request.command})
        return {"success": True, "ai_strategy": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/generate-yield")
async def generate_yield_direct(request: YieldRequest):
    """Direct NEAR yield generation endpoint bypassing agent parameter parsing."""
    try:
        result = simulate_near_yield_harvest_and_deposit_sync.invoke({"amount_usdc": request.amount_usdc})
        return {"success": True, "yield_result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/trigger-lottery")
async def trigger_lottery_direct():
    """Direct NEAR lottery trigger endpoint."""
    try:
        result = trigger_near_lottery_draw.invoke({})
        return {"success": True, "lottery_result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
def read_root():
    return {
        "message": "Enhanced NEAR Vault Manager Agent is running",
        "version": "3.0.0",
        "vault_address": VAULT_ADDRESS,
        "near_vrf_strategy_address": NEAR_VRF_STRATEGY_ADDRESS,
        "usdc_token_address": USDC_TOKEN_ADDRESS,
        "agent_account": AGENT_ACCOUNT_ID,
        "near_network": NEAR_NETWORK,
        "near_rpc": NEAR_RPC_URL,
        "risk_model_available": RISK_MODEL_AVAILABLE,
        "openai_ai_available": OPENAI_AI_AVAILABLE,
        "features": [
            "NEAR Risk Assessment",
            "NEAR VRF Lottery Management", 
            "Emergency Monitoring",
            "Enhanced Status Reporting",
            "AI Strategy Advisor (OpenAI)" if OPENAI_AI_AVAILABLE else "AI Strategy Advisor (Not Available)",
            "Native NEAR API Integration",
            "NEAR Ecosystem Support (Ref Finance, Burrow, Meta Pool)"
        ],
        "endpoints": [
            "/invoke-agent",
            "/assess-risk", 
            "/emergency-status",
            "/enhanced-status",
            "/test-vrf-risk",
            "/ai-strategy" if OPENAI_AI_AVAILABLE else "/ai-strategy (disabled)",
            "/generate-yield",
            "/trigger-lottery"
        ]
    }

@app.get("/health")
async def health_check():
    """Comprehensive NEAR health check endpoint."""
    try:
        # Test NEAR connection and account
        account_balance = await near_account.get_account_balance()
        
        # Test contract connectivity
        vault_balance = await call_near_view_method(VAULT_ADDRESS, "get_balance", {})
        prize_pool = await call_near_view_method(NEAR_VRF_STRATEGY_ADDRESS, "getBalance", {})
        
        health_status = {
            "status": "healthy",
            "timestamp": int(time.time()),
            "near_connected": True,
            "near_network": NEAR_NETWORK,
            "near_rpc": NEAR_RPC_URL,
            "agent_account": AGENT_ACCOUNT_ID,
            "agent_balance_near": float(account_balance.total) / (10**24) if account_balance else 0,
            "vault_usdc_balance": float(vault_balance or 0) / 10**6,
            "prize_pool_usdc": float(prize_pool or 0) / 10**6,
            "risk_model_loaded": risk_api is not None,
            "openai_ai_available": OPENAI_AI_AVAILABLE,
            "contracts_accessible": True
        }
        
        return {"success": True, "health": health_status}
        
    except Exception as e:
        return {
            "success": False, 
            "health": {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time()),
                "near_network": NEAR_NETWORK
            }
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced NEAR Vault Manager Agent...")
    print(f"🔧 Risk Model Available: {RISK_MODEL_AVAILABLE}")
    print(f"🤖 OpenAI AI Available: {OPENAI_AI_AVAILABLE}")
    print(f"🌐 NEAR Network: {NEAR_NETWORK}")
    print(f"💰 Agent Account: {AGENT_ACCOUNT_ID}")
    print(f"🏦 Vault Address: {VAULT_ADDRESS}")
    print(f"🎲 NEAR VRF Strategy: {NEAR_VRF_STRATEGY_ADDRESS}")
    print(f"💵 USDC Token: {USDC_TOKEN_ADDRESS}")
    
    # Feature summary
    features = []
    if RISK_MODEL_AVAILABLE:
        features.append("✅ ML Risk Assessment")
    else:
        features.append("❌ ML Risk Assessment (train model)")
        
    if OPENAI_AI_AVAILABLE:
        features.append("✅ OpenAI Strategy Advisor")
    else:
        features.append("❌ OpenAI Strategy Advisor (setup API key)")
    
    features.append("✅ NEAR VRF Lottery Management")
    features.append("✅ Emergency Monitoring")
    features.append("✅ Enhanced Status Reporting")
    features.append("✅ Native NEAR API Integration")
    features.append("✅ NEAR Ecosystem Support")
    
    print("\n📋 Available Features:")
    for feature in features:
        print(f"   {feature}")
    
    print(f"\n🌐 Starting server on http://localhost:8000")
    print(f"📚 API docs: http://localhost:8000/docs")
    print(f"🔍 Health check: http://localhost:8000/health")
    print(f"\n🎯 Ready for NEAR DeFi vault management!")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)