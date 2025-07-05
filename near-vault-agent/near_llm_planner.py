"""
Enhanced NEAR LLM Planner with OpenAI support for NEAR-specific strategy recommendations
"""

import json
import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

class NearOpenAILLMPlanner:
    """LLM Planner using OpenAI for NEAR-specific strategy generation"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with OpenAI configuration for NEAR"""
        self.config = config
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-4o-mini')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 1500)
        
        # OpenAI configuration
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        print(f"🤖 NEAR LLM Provider: {self.provider}")
        print(f"🧠 Model: {self.model}")
    
    def generate_near_vault_strategy(self, market_data: Dict[str, Any], vault_status: Dict[str, Any]) -> Dict[str, Any]:
        """Generate NEAR vault management strategy using OpenAI"""
        
        prompt = f"""
You are an expert DeFi vault manager for a NEAR blockchain prize savings protocol.

Current NEAR Vault Status:
- Liquid USDC: {vault_status.get('liquid_usdc', 0)} USDC
- Prize Pool: {vault_status.get('prize_pool', 0)} USDC  
- Last Winner: {vault_status.get('last_winner', 'None')}
- NEAR Network: {vault_status.get('near_network', 'testnet')}
- Situation: {vault_status.get('situation', 'Normal operations')}

NEAR Market Context:
- NEAR VRF Available: {market_data.get('near_vrf_available', True)}
- Ref Finance APY: ~12.5%
- Burrow Lending APY: ~8.2%
- Meta Pool Staking APY: ~10.1%
- Risk Model Available: {market_data.get('risk_model_available', True)}
- Gas Conditions: {market_data.get('gas_price', 'Normal')}

NEAR Ecosystem Advantages:
- Lower gas costs than Ethereum
- Native VRF for secure randomness
- Rich DeFi ecosystem (Ref, Burrow, Meta Pool)
- Account-based model for better UX
- Fast finality (1-2 seconds)

TASK: Generate a safe NEAR vault management strategy focusing on:
1. Prize pool optimization for weekly NEAR VRF lottery
2. User fund safety (top priority) 
3. Risk management and security
4. NEAR ecosystem yield opportunities
5. Weekly lottery prize generation

Respond with ONLY valid JSON in this exact format:
{{
    "strategy_type": "near_vault_management",
    "primary_action": "optimize_prize_pool",
    "risk_level": "low",
    "near_network": "testnet",
    "actions": [
        {{
            "action_type": "simulate_near_yield_harvest_and_deposit_sync",
            "parameters": {{
                "amount_usdc": 150.0
            }},
            "priority": 1,
            "reasoning": "Generate weekly NEAR lottery prize pool"
        }}
    ],
    "expected_outcome": {{
        "prize_pool_target": 150.0,
        "risk_score": 0.2,
        "estimated_timeline": "immediate",
        "near_advantages": "Lower gas costs, native VRF"
    }},
    "recommendations": [
        "Create modest weekly prize pool using NEAR VRF",
        "Maintain low risk approach on NEAR",
        "Consider Ref Finance for higher yields",
        "Leverage NEAR's fast finality for better UX"
    ]
}}
"""
        
        return self._generate_with_openai(prompt)
    
    def _generate_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Generate strategy using OpenAI API"""
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a NEAR DeFi vault manager expert. Respond only with valid JSON strategy objects optimized for NEAR blockchain. No additional text."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ OpenAI API error: {response.status_code} - {response.text}")
                return self._fallback_near_strategy()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"🤖 OpenAI NEAR Response: {content[:200]}...")
            
            # Extract JSON from response
            strategy = self._extract_json_from_response(content)
            return strategy if strategy else self._fallback_near_strategy()
            
        except Exception as e:
            print(f"⚠️ OpenAI NEAR generation failed: {e}")
            return self._fallback_near_strategy()
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON strategy from LLM response"""
        try:
            # Try parsing as direct JSON
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # Look for JSON within the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        return None
    
    def _fallback_near_strategy(self) -> Dict[str, Any]:
        """Fallback NEAR strategy when LLM fails"""
        return {
            "strategy_type": "near_vault_management",
            "primary_action": "optimize_prize_pool",
            "risk_level": "low",
            "near_network": "testnet",
            "actions": [
                {
                    "action_type": "simulate_near_yield_harvest_and_deposit_sync",
                    "parameters": {"amount_usdc": 150.0},
                    "priority": 1,
                    "reasoning": "Fallback: Generate modest NEAR prize pool for weekly lottery"
                }
            ],
            "expected_outcome": {
                "prize_pool_target": 150.0,
                "risk_score": 0.2,
                "estimated_timeline": "immediate",
                "near_advantages": "Lower gas costs, native VRF"
            },
            "recommendations": [
                "Use fallback strategy due to LLM unavailability",
                "Generate modest prize pool for weekly NEAR lottery",
                "Leverage NEAR's unique advantages over Ethereum",
                "Consider NEAR DeFi ecosystem opportunities"
            ]
        }
    
    def check_api_available(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️ OpenAI API not available: {e}")
            return False


# Enhanced agent tool using NEAR-specific OpenAI LLM planner
@tool
def near_ai_strategy_advisor(current_situation: str = "general_analysis") -> str:
    """
    Use OpenAI to analyze current NEAR vault situation and recommend strategies.
    
    Args:
        current_situation: Description of the current NEAR situation to analyze
    """
    print(f"Tool: near_ai_strategy_advisor - Situation: {current_situation}")
    
    # Initialize NEAR-specific OpenAI LLM planner
    llm_config = {
        'provider': 'openai',
        'model': 'gpt-4o-mini',
        'temperature': 0.1,
        'max_tokens': 1500
    }
    
    try:
        planner = NearOpenAILLMPlanner(llm_config)
        
        # Check if OpenAI API is available
        if not planner.check_api_available():
            return """
❌ OpenAI API not available for NEAR strategies. 

Please check:
1. OPENAI_API_KEY is set in .env file
2. API key is valid and has credits
3. Internet connection is working

Using fallback NEAR rule-based strategy instead.
            """
        
        # Get current NEAR vault status (you could make this dynamic by calling other tools)
        vault_status = {
            "liquid_usdc": 290.0,  # From your health check
            "prize_pool": 0.0,
            "last_winner": "0x0000000000000000000000000000000000000000",
            "strategy_type": "near_vrf_lottery",
            "near_network": "testnet",
            "situation": current_situation
        }
        
        market_data = {
            "near_vrf_available": True,
            "gas_price": "low",  # NEAR advantage
            "risk_model_available": True,
            "situation_description": current_situation,
            "ref_finance_apy": 12.5,
            "burrow_apy": 8.2,
            "meta_pool_apy": 10.1
        }
        
        # Generate NEAR strategy using OpenAI
        strategy = planner.generate_near_vault_strategy(market_data, vault_status)
        
        return f"""
🤖 AI Strategy Recommendation (OpenAI for NEAR):

Strategy Type: {strategy['strategy_type']}
Primary Action: {strategy['primary_action']}
Risk Level: {strategy['risk_level']}
NEAR Network: {strategy.get('near_network', 'testnet')}

Actions to Take:
{json.dumps(strategy['actions'], indent=2)}

Expected Outcome:
{json.dumps(strategy['expected_outcome'], indent=2)}

AI Recommendations:
{json.dumps(strategy['recommendations'], indent=2)}

🌐 NEAR Advantages: Lower gas costs, native VRF, fast finality, rich DeFi ecosystem
        """
        
    except Exception as e:
        return f"❌ NEAR AI strategy advisor failed: {e}\n\nUsing fallback: Recommend 150 USDC yield harvest for weekly NEAR lottery with low gas costs."


# Test function
def test_near_openai_connection():
    """Test OpenAI connection for NEAR strategies"""
    config = {
        'provider': 'openai',
        'model': 'gpt-4o-mini',
        'temperature': 0.1,
        'max_tokens': 100
    }
    
    try:
        planner = NearOpenAILLMPlanner(config)
        available = planner.check_api_available()
        print(f"✅ OpenAI API Available for NEAR: {available}")
        return available
    except Exception as e:
        print(f"❌ OpenAI NEAR Test Failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing NEAR OpenAI LLM Planner...")
    test_near_openai_connection()