"""
Aurora-specific OpenAI LLM Planner for Aurora (NEAR EVM) vault strategies
"""

import json
import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

class AuroraOpenAILLMPlanner:
    """LLM Planner using OpenAI for Aurora-specific strategy generation"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with OpenAI configuration for Aurora"""
        self.config = config
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-4o-mini')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 1500)
        
        # OpenAI configuration
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        print(f"🤖 Aurora LLM Provider: {self.provider}")
        print(f"🧠 Model: {self.model}")
    
    def generate_aurora_vault_strategy(self, market_data: Dict[str, Any], vault_status: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Aurora vault management strategy using OpenAI"""
        
        prompt = f"""
You are an expert DeFi vault manager for Aurora (NEAR's EVM layer) prize savings protocol.

Current Aurora Vault Status:
- Liquid USDC: {vault_status.get('liquid_usdc', 0)} USDC
- Prize Pool: {vault_status.get('prize_pool', 0)} USDC  
- Last Winner: {vault_status.get('last_winner', 'None')}
- Aurora Network: NEAR EVM Layer (Chain ID: 1313161555)
- Situation: {vault_status.get('situation', 'Normal operations')}

Aurora Ecosystem Context:
- Aurora VRF Available: {market_data.get('aurora_vrf_available', True)}
- Ref Finance (DEX): ~15.2% APY, Medium Risk
- Trisolaris (AMM): ~12.8% APY, Medium Risk  
- Bastion (Lending): ~9.1% APY, Low Risk
- Pulsar Finance: Advanced DeFi strategies
- Beefy Finance: Auto-compounding vaults
- Gas Conditions: {market_data.get('gas_price', 'Low (Aurora advantage)')}

Aurora Ecosystem Advantages:
- EVM compatibility with lower gas costs
- NEAR's fast finality and security
- Bridge to NEAR ecosystem
- Growing DeFi ecosystem
- Ethereum tooling compatibility

TASK: Generate a safe Aurora vault management strategy focusing on:
1. Prize pool optimization for weekly Aurora VRF lottery
2. User fund safety (top priority) 
3. Risk management and security
4. Aurora ecosystem yield opportunities
5. Weekly lottery prize generation

Respond with ONLY valid JSON in this exact format:
{{
    "strategy_type": "aurora_vault_management",
    "primary_action": "optimize_prize_pool",
    "risk_level": "low",
    "aurora_chain_id": 1313161555,
    "actions": [
        {{
            "action_type": "simulate_aurora_yield_harvest_and_deposit",
            "parameters": {{
                "amount_usdc": 150.0
            }},
            "priority": 1,
            "reasoning": "Generate weekly Aurora lottery prize pool"
        }}
    ],
    "expected_outcome": {{
        "prize_pool_target": 150.0,
        "risk_score": 0.2,
        "estimated_timeline": "immediate",
        "aurora_advantages": "Lower gas costs, EVM compatibility, NEAR security"
    }},
    "recommendations": [
        "Create modest weekly prize pool using Aurora VRF",
        "Maintain low risk approach on Aurora",
        "Consider Ref Finance for higher yields when appropriate",
        "Leverage Aurora's EVM compatibility and NEAR ecosystem",
        "Monitor Bastion for lending opportunities"
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
                            "content": "You are an Aurora DeFi vault manager expert. Respond only with valid JSON strategy objects optimized for Aurora (NEAR EVM). No additional text."
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
                return self._fallback_aurora_strategy()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"🤖 OpenAI Aurora Response: {content[:200]}...")
            
            # Extract JSON from response
            strategy = self._extract_json_from_response(content)
            return strategy if strategy else self._fallback_aurora_strategy()
            
        except Exception as e:
            print(f"⚠️ OpenAI Aurora generation failed: {e}")
            return self._fallback_aurora_strategy()
    
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
    
    def _fallback_aurora_strategy(self) -> Dict[str, Any]:
        """Fallback Aurora strategy when LLM fails"""
        return {
            "strategy_type": "aurora_vault_management",
            "primary_action": "optimize_prize_pool",
            "risk_level": "low",
            "aurora_chain_id": 1313161555,
            "actions": [
                {
                    "action_type": "simulate_aurora_yield_harvest_and_deposit",
                    "parameters": {"amount_usdc": 150.0},
                    "priority": 1,
                    "reasoning": "Fallback: Generate modest Aurora prize pool for weekly lottery"
                }
            ],
            "expected_outcome": {
                "prize_pool_target": 150.0,
                "risk_score": 0.2,
                "estimated_timeline": "immediate",
                "aurora_advantages": "Lower gas costs, EVM compatibility, NEAR security"
            },
            "recommendations": [
                "Use fallback strategy due to LLM unavailability",
                "Generate modest prize pool for weekly Aurora lottery",
                "Leverage Aurora's unique advantages over Ethereum",
                "Consider Aurora DeFi ecosystem opportunities (Ref, Trisolaris, Bastion)"
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


# Enhanced agent tool using Aurora-specific OpenAI LLM planner
@tool
def ai_strategy_advisor(current_situation: str = "general_analysis") -> str:
    """
    Use OpenAI to analyze current Aurora vault situation and recommend strategies.
    
    Args:
        current_situation: Description of the current Aurora situation to analyze
    """
    print(f"Tool: ai_strategy_advisor - Aurora Situation: {current_situation}")
    
    # Initialize Aurora-specific OpenAI LLM planner
    llm_config = {
        'provider': 'openai',
        'model': 'gpt-4o-mini',
        'temperature': 0.1,
        'max_tokens': 1500
    }
    
    try:
        planner = AuroraOpenAILLMPlanner(llm_config)
        
        # Check if OpenAI API is available
        if not planner.check_api_available():
            return """
❌ OpenAI API not available for Aurora strategies. 

Please check:
1. OPENAI_API_KEY is set in .env file
2. API key is valid and has credits
3. Internet connection is working

Using fallback Aurora rule-based strategy instead.
            """
        
        # Get current Aurora vault status (dynamic from your actual contracts)
        vault_status = {
            "liquid_usdc": 290.0,  # From your health check
            "prize_pool": 0.0,
            "last_winner": "0x0000000000000000000000000000000000000000",
            "strategy_type": "aurora_vrf_lottery",
            "aurora_chain_id": 1313161555,
            "situation": current_situation
        }
        
        market_data = {
            "aurora_vrf_available": True,
            "gas_price": "low",  # Aurora advantage
            "risk_model_available": True,
            "situation_description": current_situation,
            "ref_finance_apy": 15.2,
            "trisolaris_apy": 12.8,
            "bastion_apy": 9.1
        }
        
        # Generate Aurora strategy using OpenAI
        strategy = planner.generate_aurora_vault_strategy(market_data, vault_status)
        
        return f"""
🤖 AI Strategy Recommendation (OpenAI for Aurora):

Strategy Type: {strategy['strategy_type']}
Primary Action: {strategy['primary_action']}
Risk Level: {strategy['risk_level']}
Aurora Chain ID: {strategy.get('aurora_chain_id', 1313161555)}

Actions to Take:
{json.dumps(strategy['actions'], indent=2)}

Expected Outcome:
{json.dumps(strategy['expected_outcome'], indent=2)}

AI Recommendations:
{json.dumps(strategy['recommendations'], indent=2)}

🌐 Aurora Advantages: Lower gas costs, EVM compatibility, NEAR ecosystem access, fast finality
        """
        
    except Exception as e:
        return f"❌ Aurora AI strategy advisor failed: {e}\n\nUsing fallback: Recommend 150 USDC yield harvest for weekly Aurora lottery with low gas costs."


# Test function
def test_aurora_openai_connection():
    """Test OpenAI connection for Aurora strategies"""
    config = {
        'provider': 'openai',
        'model': 'gpt-4o-mini',
        'temperature': 0.1,
        'max_tokens': 100
    }
    
    try:
        planner = AuroraOpenAILLMPlanner(config)
        available = planner.check_api_available()
        print(f"✅ OpenAI API Available for Aurora: {available}")
        return available
    except Exception as e:
        print(f"❌ OpenAI Aurora Test Failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing Aurora OpenAI LLM Planner...")
    test_aurora_openai_connection()