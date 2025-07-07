import React from 'react'
import { WagmiProvider } from 'wagmi'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { config } from './config/wagmi'
import { Header } from './components/Header'
import { Dashboard } from './components/Dashboard'
import { DepositWithdraw } from './components/DepositWithdraw'
import { UserStats } from './components/UserStats'
import { USDCFaucet } from './components/USDCFaucet'

const queryClient = new QueryClient()

function App() {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <div className="min-h-screen bg-[#f2f1e9]">
          <Header />
          
          <main className="max-w-7xl mx-auto px-6 py-8">
            <div className="mb-8">
              <h2 className="text-3xl font-semibold text-black mb-2">Aurora Multi-Strategy Vault</h2>
              <p className="text-gray-600">
                AI-powered yield optimization across Aurora DeFi protocols with automated rebalancing
              </p>
            </div>
            
            <Dashboard />
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              <div>
                <h3 className="text-xl font-semibold text-black mb-4">Manage Your Deposit</h3>
                <DepositWithdraw />
              </div>
              
              <div>
                <h3 className="text-xl font-semibold text-black mb-4">Your Portfolio</h3>
                <UserStats />
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-semibold text-black mb-4">USDC Faucet for Testing</h3>
              <USDCFaucet />
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-black mb-3">How It Works</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-[#00ec97] bg-opacity-10 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-[#00ec97] font-semibold">1</span>
                  </div>
                  <h4 className="font-medium text-black mb-2">Deposit USDC</h4>
                  <p className="text-sm text-gray-600">
                    Connect your wallet and deposit USDC into the multi-strategy vault
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 bg-[#17d9d4] bg-opacity-10 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-[#17d9d4] font-semibold">2</span>
                  </div>
                  <h4 className="font-medium text-black mb-2">AI Optimization</h4>
                  <p className="text-sm text-gray-600">
                    AI automatically allocates funds across Ref Finance, TriSolaris, and Bastion
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 bg-[#9797ff] bg-opacity-10 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-[#9797ff] font-semibold">3</span>
                  </div>
                  <h4 className="font-medium text-black mb-2">Earn Yield</h4>
                  <p className="text-sm text-gray-600">
                    Your funds generate optimized yields across multiple Aurora protocols
                  </p>
                </div>

                <div className="text-center">
                  <div className="w-12 h-12 bg-[#ff7966] bg-opacity-10 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-[#ff7966] font-semibold">4</span>
                  </div>
                  <h4 className="font-medium text-black mb-2">Auto-Rebalance</h4>
                  <p className="text-sm text-gray-600">
                    ML-enhanced risk assessment and automated portfolio rebalancing
                  </p>
                </div>
              </div>
            </div>
          </main>
        </div>
      </QueryClientProvider>
    </WagmiProvider>
  )
}

export default App