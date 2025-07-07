import React, { useState } from 'react'
import { useAccount, useConnect, useDisconnect, useBalance } from 'wagmi'
import { formatAddress } from '../utils/format'
import { Wallet, AlertCircle, CheckCircle } from 'lucide-react'

export const Header: React.FC = () => {
  const { address, isConnected, isConnecting } = useAccount()
  const { connect, connectors, error: connectError, isPending } = useConnect()
  const { disconnect } = useDisconnect()
  const [connectionError, setConnectionError] = useState<string | null>(null)

  // Get ETH balance on Aurora Testnet
  const { data: balance } = useBalance({
    address: address,
  })

  const handleConnect = async () => {
    try {
      setConnectionError(null)
      const metaMaskConnector = connectors.find(connector => 
        connector.id === 'metaMask' || connector.name.toLowerCase().includes('metamask')
      )
      
      if (!metaMaskConnector) {
        setConnectionError('MetaMask connector not found. Please install MetaMask.')
        return
      }

      await connect({ connector: metaMaskConnector })
    } catch (error: any) {
      console.error('Connection error:', error)
      setConnectionError(error?.message || 'Failed to connect wallet')
    }
  }

  const handleDisconnect = () => {
    setConnectionError(null)
    disconnect()
  }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-[#00ec97] rounded-lg flex items-center justify-center">
            <Wallet className="w-5 h-5 text-black" />
          </div>
          <h1 className="text-2xl font-semibold text-black">Aurora Prize Savings</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Connection Error Display */}
          {connectionError && (
            <div className="flex items-center space-x-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-red-700">{connectionError}</span>
            </div>
          )}

          {/* Connect Error from Wagmi */}
          {connectError && (
            <div className="flex items-center space-x-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-red-700">
                {connectError.message || 'Connection failed'}
              </span>
            </div>
          )}

          {isConnected && address ? (
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-700">Connected</span>
              </div>
              
              <div className="text-right">
                <p className="text-sm text-gray-600">
                  {formatAddress(address)}
                </p>
                {balance && (
                  <p className="text-xs text-gray-500">
                    {parseFloat(balance.formatted).toFixed(4)} {balance.symbol}
                  </p>
                )}
              </div>
              
              <button
                onClick={handleDisconnect}
                className="px-4 py-2 bg-gray-100 text-black rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                Disconnect
              </button>
            </div>
          ) : (
            <button
              onClick={handleConnect}
              disabled={isConnecting || isPending}
              className="px-6 py-3 bg-[#00ec97] text-black rounded-lg hover:bg-[#00d485] transition-colors font-medium flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isConnecting || isPending ? (
                <>
                  <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                  <span>Connecting...</span>
                </>
              ) : (
                <>
                  <Wallet className="w-5 h-5" />
                  <span>Connect Wallet</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </header>
  )
}