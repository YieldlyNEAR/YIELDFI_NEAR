# YieldFi: AI-Powered Multi-Strategy Vault on Aurora

**Live Demo:** [https://lively-starburst-9bc69c.netlify.app](https://lively-starburst-9bc69c.netlify.app)

YieldFi is an intelligent, multi-protocol yield aggregator built on the Aurora network. It leverages a sophisticated AI agent, enhanced with a machine learning risk model, to dynamically manage and optimize a portfolio of digital assets across the Aurora DeFi ecosystem. The system automatically allocates user deposits to various strategies, such as lending on Bastion or providing liquidity on Ref Finance and Trisolaris, to maximize returns while actively managing risk.

---

## Core Features

* 🤖 **AI Portfolio Optimization:** The agent uses GPT-4o to analyze market data and ML-driven risk scores, making intelligent decisions to optimize allocations across Ref Finance, TriSolaris, and Bastion.

* ⚖️ **Automated Rebalancing:** The portfolio is automatically rebalanced on a set interval (currently 1 hour) to adapt to changing market conditions and maintain the optimal risk/reward profile.

* 🌾 **Cross-Protocol Yield Harvesting:** The agent automatically harvests earned rewards from all integrated protocols and compounds them back into the vault, maximizing overall APY.

* 🛡️ **Real-time Risk Monitoring:** The system continuously monitors protocol health and uses a custom-trained ML model to assess the real-time risk of each strategy, enabling emergency exit protocols if necessary.

* ⚡ **Aurora Gas Optimization:** By operating on Aurora, all transactions (deposits, withdrawals, rebalancing) are over 100x cheaper and significantly faster than on Ethereum mainnet.

* 📊 **Performance Analytics:** The agent provides on-demand analysis of the current portfolio, individual strategy performance, and data-driven recommendations.

---

## System Architecture

The YieldFi system consists of three main components:

### Solidity Smart Contracts (on Aurora)

A set of robust and secure smart contracts handle all on-chain logic, from user deposits to strategy execution.

* **AuroraMultiVault.sol:** The core ERC-4626 compatible vault that holds user funds and manages allocations.
* **RefFinanceStrategy.sol:** A strategy contract for interacting with Ref Finance.
* **TriSolarisStrategy.sol:** A strategy contract for interacting with Trisolaris.
* **BastionStrategy.sol:** A strategy contract for interacting with Bastion Protocol.

### Python AI Agent (Backend)

A powerful off-chain agent built with Python, FastAPI, and LangChain. This agent acts as the "brain" of the system, executing the optimization and management logic.

### Machine Learning Risk Model

A custom-trained anomaly detection model that provides real-time risk scores for each strategy, allowing the AI agent to make more informed, risk-aware decisions.

---

## Deployment on Aurora Testnet

The following contracts have been deployed and verified on the Aurora Testnet.

* 🏦 **Aurora Multi-Vault:** `0x15a616EB9df9fa0B8520C66a234f9BBD172847F5`
* 💵 **MockUSDC Token:** `0xC0933C5440c656464D1Eb1F886422bE3466B1459`
* 🔄 **Ref Finance Strategy:** `0x5D6ea21714Ce7E04a16A2776A7e7c6d8ec5a1bd0`
* 🔄 **TriSolaris Strategy:** `0x841eC1D601B1E9392ec9ba840eF1618beE8D9911`
* 🔄 **Bastion Strategy:** `0x215E95Fc16c460b9558C9213234B90971306e543`

---

## Getting Started: Running the Agent Locally

To run the AI agent and interact with the deployed contracts, follow these steps.

### 1. Setup Environment

Clone the repository and create a `.env` file in the root directory with the following variables:

```
NEAR_TESTNET_RPC_URL=https://testnet.aurora.dev
NEAR_TESTNET_CHAIN_ID=1313161555
AGENT_PRIVATE_KEY="YOUR_AGENT_WALLET_PRIVATE_KEY"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
GRAPH_API_KEY="YOUR_GRAPH_API_KEY"
```

### 2. Install Dependencies

Install the required Python packages.

```bash
pip install fastapi uvicorn web3 langchain-openai requests scikit-learn joblib
```

### 3. Run the AI Agent

Start the FastAPI server. The agent will begin its automated optimization loop immediately.

```bash
python near-vault-agent/aurora_multi_vault_agent_with_ml.py
```

### 4. Test the System

Once the server is running, you can interact with it using the API endpoints listed below.

---

## AI Agent API Endpoints

### Vault & Asset Management

**Mint Test USDC:**

```bash
curl -X POST "http://localhost:8000/mint-usdc?amount=1500"
```

**Deposit into Vault:**

```bash
curl -X POST "http://localhost:8000/deposit-test?amount=500"
```

### Core Agent Actions

**Force Rebalance:**

```bash
curl -X POST http://localhost:8000/rebalance
```

**Force Harvest:**

```bash
curl -X POST http://localhost:8000/harvest
```

**Invoke AI Agent (Natural Language):**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"command": "what is the current vault status?"}' http://localhost:8000/invoke-agent
```

### Reporting & Monitoring

**Get Vault Status:**

```bash
curl http://localhost:8000/status
```

**Analyze Yields:**

```bash
curl http://localhost:8000/yields
```

**Check Risk Report:**

```bash
curl http://localhost:8000/risk
```

**Assess a Specific Strategy's Risk:**

```bash
curl -X POST "http://localhost:8000/assess-risk?strategy_address=0x841eC1D601B1E9392ec9ba840eF1618beE8D9911"
```

---

## Meeting Submission Requirements

✅ **Working Demo on NEAR Testnet:** The system is fully deployed and operational on the Aurora Testnet. A live front-end is available at [Live Demo](https://lively-starburst-9bc69c.netlify.app).

✅ **Intent Definition and Handling:** Intents are defined as high-level goals for the agent (e.g., "maximize yield while maintaining a low-risk profile"). These are translated into actionable steps within the agent's logic. For example, the `execute_multi_strategy_rebalance` tool is a direct execution of this primary intent, using data from other tools (`analyze_aurora_yields`, `aurora_risk_monitor`) as inputs. Natural language commands sent to the `/invoke-agent` endpoint are parsed by LangChain to determine the user's intent and select the appropriate tool.

✅ **Core Agent Logic & Storage:** The agent's core logic resides in the Python backend. It uses a ReAct (Reason and Act) framework via LangChain to process information and decide on actions. It fetches on-chain state (total assets, balances) and off-chain data (live APYs, risk scores), synthesizes this information using an LLM, and forms a transaction to execute its decision (e.g., calling the rebalance function). All persistent state (user deposits, strategy balances) is stored on-chain within the `AuroraMultiVault` smart contract, ensuring transparency and decentralization.

✅ **Cross-Chain Signature Integration:** While this implementation focuses on Aurora, the architecture is prepared for cross-chain interactions. Signatures are handled by the `web3.py` library using the `AGENT_PRIVATE_KEY`. To interact with another chain (e.g., bridging to Ethereum), the agent would simply need a new provider for that chain's RPC and would use the same private key to sign transactions, assuming the same wallet address is funded on both networks.

---

## Future Work & Alternative Concepts

* **No-Loss Prize Savings Game:** An alternative model where all generated yield is pooled and awarded to a single, randomly selected depositor each week. This gamified approach to savings would require a secure on-chain source of randomness (like a VRF).

---
