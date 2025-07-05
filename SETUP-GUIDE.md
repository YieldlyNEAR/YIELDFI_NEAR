# Enhanced NEAR Vault Manager Agent Setup Guide

## Overview

This is a sophisticated AI-powered vault management system specifically designed for NEAR blockchain, featuring:
- 🤖 **OpenAI Strategy Recommendations** 
- 🔍 **ML Risk Assessment**
- 🎲 **NEAR VRF Lottery Management**
- 🚨 **Emergency Monitoring**
- 🌐 **Native NEAR API Integration**
- 📊 **NEAR Ecosystem Support** (Ref Finance, Burrow, Meta Pool)

## Prerequisites

- Python 3.9 - 3.11 (3.12+ not supported by NEAR AI)
- NEAR Account (create at [wallet.near.org](https://wallet.near.org))
- OpenAI API Key
- NEAR Testnet tokens for gas

## Installation

### 1. Clone and Setup Environment

```bash
# Create project directory
mkdir near-vault-agent
cd near-vault-agent

# Create virtual environment
python -m venv venv
source venv/activate  # On Windows: venv\Scripts\activate

# Install NEAR-specific requirements
pip install -r requirements.near.txt
```

### 2. NEAR Account Setup

```bash
# Install NEAR CLI (optional but helpful)
npm install -g near-cli

# Create testnet account at wallet.near.org
# Export your private key for the agent
```

### 3. Environment Configuration

Create `.env` file from the template:

```bash
cp .env.near .env
# Edit .env with your values
```

Required configuration:
- `AGENT_ACCOUNT_ID`: Your NEAR account (e.g., "agent.testnet")
- `AGENT_PRIVATE_KEY`: Your NEAR private key
- `OPENAI_API_KEY`: Your OpenAI API key

### 4. Contract ABIs

Ensure you have these ABI files in the `abi/` directory:
- `Vault.json` 
- `NearVrfYieldStrategy.json` (provided)
- `MockUSDC.json`

### 5. Risk Model Setup (Optional)

```bash
# Setup ML risk assessment
cd ml-risk
python anomaly_risk_model.py
cd ..
```

## Running the Agent

### Start the Enhanced NEAR Agent

```bash
python enhanced_near_vault_agent.py
```

You should see:
```
✅ NEAR API imported successfully
✅ Risk model imported successfully  
✅ OpenAI LLM planner imported successfully
🤖 NEAR Agent Account: your-agent.testnet
🌐 NEAR Network: testnet
🚀 Starting Enhanced NEAR Vault Manager Agent...
🌐 Starting server on http://localhost:8000
```

## Testing the Agent

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Enhanced Status

```bash
curl http://localhost:8000/enhanced-status
```

### 3. Generate NEAR Yield

```bash
curl -X POST http://localhost:8000/generate-yield \
  -H "Content-Type: application/json" \
  -d '{"amount_usdc": 150.0}'
```

### 4. AI Strategy Recommendations

```bash
curl -X POST http://localhost:8000/ai-strategy \
  -H "Content-Type: application/json" \
  -d '{"command": "Recommend best NEAR strategy for 150 USDC weekly lottery"}'
```

### 5. Trigger NEAR Lottery

```bash
curl -X POST http://localhost:8000/trigger-lottery
```

## NEAR-Specific Features

### NEAR Ecosystem Integration

The agent supports:
- **Ref Finance**: Leading NEAR DEX
- **Burrow**: NEAR lending protocol  
- **Meta Pool**: NEAR liquid staking
- **Native NEAR VRF**: Secure randomness

### NEAR API Advantages

- Native async/await support
- Account-based model
- Lower gas costs
- Built-in randomness (VRF)
- Rich DeFi ecosystem

### Risk Management for NEAR

- Ethereum-trained risk models adapted for NEAR
- NEAR-specific transaction patterns
- Cross-chain risk assessment
- Emergency exit protocols

## Frontend Integration

Your NEAR agent provides the same API endpoints as the Flow version:

```javascript
// Frontend integration example
const response = await fetch('/api/near-vault/enhanced-status')
const status = await response.json()

// Generate yield for lottery
const yieldResult = await fetch('/api/near-vault/generate-yield', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ amount_usdc: 150.0 })
})
```

## NEAR AI Platform Integration (Optional)

For enhanced AI capabilities:

```bash
# Install NEAR AI CLI
pip install nearai

# Login to NEAR AI
nearai login

# Deploy your agent to NEAR AI
nearai agent create --framework agentkit
```

## Troubleshooting

### Common Issues

1. **NEAR Connection Failed**
   - Check AGENT_ACCOUNT_ID and AGENT_PRIVATE_KEY
   - Verify NEAR account exists and has funds
   - Test NEAR_RPC_URL connectivity

2. **Transaction Failed**
   - Ensure agent account has NEAR tokens for gas
   - Check contract addresses are correct
   - Verify contract methods exist

3. **Risk Model Issues**
   - Train risk model: `cd ml-risk && python anomaly_risk_model.py`
   - Check ml-risk directory structure

### Getting NEAR Testnet Tokens

1. Visit [NEAR Testnet Faucet](https://near-faucet.io/)
2. Enter your agent account ID
3. Request testnet NEAR tokens

## API Documentation

Once running, view complete API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Production Deployment

For production:
1. Switch to NEAR mainnet
2. Use production RPC endpoints
3. Implement proper security measures
4. Set up monitoring and alerts
5. Consider NEAR AI platform hosting

## Support

- NEAR Documentation: https://docs.near.org
- NEAR API Python: https://py-near.readthedocs.io
- AgentKit: https://ai-agent-kit.vercel.app