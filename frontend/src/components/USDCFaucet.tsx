import React, { useState, useEffect } from 'react'
import { useAccount, useWriteContract, useWaitForTransactionReceipt } from 'wagmi'
import { useContractData } from '../hooks/useContractData'
import { CONTRACT_ADDRESSES, MOCK_USDC_ABI } from '../config/contracts'
import { parseUSDC } from '../utils/format'
import { Droplets, Loader2, CheckCircle, AlertCircle, Wallet } from 'lucide-react'

export const USDCFaucet: React.FC = () => {
  const { address } = useAccount()
  const [faucetAmount, setFaucetAmount] = useState('1000')
  const [isFauceting, setIsFauceting] = useState(false)
  const [transactionError, setTransactionError] = useState<string | null>(null)
  const [transactionSuccess, setTransactionSuccess] = useState<string | null>(null)

  const { refetch } = useContractData(address)
  const { writeContract, data: hash, isPending, error } = useWriteContract()
  const { isLoading: isConfirming, isSuccess } = useWaitForTransactionReceipt({
    hash,
  })

  // Reset states when transaction completes
  useEffect(() => {
    if (isSuccess) {
      setIsFauceting(false)
      setTransactionError(null)
      setTransactionSuccess(`Successfully received ${faucetAmount} USDC from faucet!`)
      refetch()
      
      // Clear success message after 5 seconds
      setTimeout(() => setTransactionSuccess(null), 5000)
    }
  }, [isSuccess, refetch, faucetAmount])

  // Handle errors
  useEffect(() => {
    if (error) {
      setIsFauceting(false)
      setTransactionError(error.message || 'Faucet transaction failed')
      setTimeout(() => setTransactionError(null), 5000)
    }
  }, [error])

  const handleFaucet = async () => {
    if (!address || !faucetAmount) return

    setIsFauceting(true)
    setTransactionError(null)
    setTransactionSuccess(null)

    try {
      const amount = parseUSDC(faucetAmount)

      await writeContract({
        address: CONTRACT_ADDRESSES.MOCK_USDC,
        abi: MOCK_USDC_ABI,
        functionName: 'faucet',
        args: [amount],
      })
    } catch (error: any) {
      console.error('Faucet failed:', error)
      setIsFauceting(false)
      setTransactionError(error?.message || 'Faucet transaction failed')
    }
  }

  if (!address) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center">
        <Wallet className="w-8 h-8 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-500 text-sm">Connect your wallet to use the faucet</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Status Messages */}
      {transactionError && (
        <div className="px-6 py-3 bg-red-50 border-b border-red-200 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span className="text-sm text-red-700">{transactionError}</span>
        </div>
      )}
      
      {transactionSuccess && (
        <div className="px-6 py-3 bg-green-50 border-b border-green-200 flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-green-500" />
          <span className="text-sm text-green-700">{transactionSuccess}</span>
        </div>
      )}

      <div className="p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-[#9797ff] bg-opacity-10 rounded-lg">
            <Droplets className="w-5 h-5 text-[#9797ff]" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-black">USDC Faucet for Testing</h3>
            <p className="text-sm text-gray-600">Get test USDC to try the Aurora Multi-Strategy Vault</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Faucet Amount (USDC)
            </label>
            <input
              type="number"
              value={faucetAmount}
              onChange={(e) => setFaucetAmount(e.target.value)}
              placeholder="1000"
              step="1"
              min="1"
              max="10000"
              className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#9797ff] focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">Maximum 10,000 USDC per request</p>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-gray-700">Contract:</span>
              <span className="text-gray-600 font-mono text-xs">{CONTRACT_ADDRESSES.MOCK_USDC}</span>
            </div>
            <div className="flex items-center justify-between text-sm mt-2">
              <span className="font-medium text-gray-700">Network:</span>
              <span className="text-gray-600">Aurora Testnet</span>
            </div>
          </div>

          <button
            onClick={handleFaucet}
            disabled={isFauceting || isPending || isConfirming || !faucetAmount}
            className="w-full px-4 py-3 bg-[#9797ff] text-white rounded-lg hover:bg-[#8585ff] transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {isFauceting || isPending || isConfirming ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Requesting USDC...</span>
              </>
            ) : (
              <>
                <Droplets className="w-4 h-4" />
                <span>Get {faucetAmount} USDC</span>
              </>
            )}
          </button>
        </div>

        <p className="text-xs text-gray-500 mt-4 text-center">
          This is a testnet faucet. USDC has no real value on Aurora Testnet.
        </p>
      </div>
    </div>
  )
}