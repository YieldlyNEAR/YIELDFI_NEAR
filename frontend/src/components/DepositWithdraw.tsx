import React, { useState, useEffect } from 'react'
import { useAccount, useWriteContract, useWaitForTransactionReceipt, useReadContract } from 'wagmi'
import { useContractData } from '../hooks/useContractData'
import { CONTRACT_ADDRESSES, AURORA_MULTI_VAULT_ABI, MOCK_USDC_ABI } from '../config/contracts'
import { formatUSDC, parseUSDC, formatVaultShares, parseVaultShares } from '../utils/format'
import { ArrowDownCircle, ArrowUpCircle, Loader2, CheckCircle, AlertCircle, Wallet } from 'lucide-react'

export const DepositWithdraw: React.FC = () => {
  const { address } = useAccount()
  const [activeTab, setActiveTab] = useState<'deposit' | 'withdraw'>('deposit')
  const [depositAmount, setDepositAmount] = useState('')
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [currentStep, setCurrentStep] = useState<'idle' | 'approving' | 'depositing' | 'withdrawing'>('idle')
  const [transactionError, setTransactionError] = useState<string | null>(null)
  const [transactionSuccess, setTransactionSuccess] = useState<string | null>(null)

  const { usdcBalance, vaultShares, refetch } = useContractData(address)
  const { writeContract, data: hash, isPending, error } = useWriteContract()
  const { isLoading: isConfirming, isSuccess } = useWaitForTransactionReceipt({
    hash,
  })

  // Check current allowance
  const { data: allowance } = useReadContract({
    address: CONTRACT_ADDRESSES.MOCK_USDC,
    abi: MOCK_USDC_ABI,
    functionName: 'allowance',
    args: address ? [address, CONTRACT_ADDRESSES.AURORA_MULTI_VAULT] : undefined,
  })

  // Reset states when transaction completes
  useEffect(() => {
    if (isSuccess) {
      setCurrentStep('idle')
      setTransactionError(null)
      setTransactionSuccess(
        currentStep === 'depositing' ? 'Deposit successful!' : 
        currentStep === 'withdrawing' ? 'Withdrawal successful!' : 
        'Transaction successful!'
      )
      setDepositAmount('')
      setWithdrawAmount('')
      refetch()
      
      // Clear success message after 5 seconds
      setTimeout(() => setTransactionSuccess(null), 5000)
    }
  }, [isSuccess, currentStep, refetch])

  // Handle errors
  useEffect(() => {
    if (error) {
      setCurrentStep('idle')
      setTransactionError(error.message || 'Transaction failed')
      setTimeout(() => setTransactionError(null), 5000)
    }
  }, [error])

  const needsApproval = (amount: string) => {
    if (!allowance || !amount) return true
    const amountBigInt = parseUSDC(amount)
    return allowance < amountBigInt
  }

  const handleApprove = async () => {
    if (!depositAmount || !address) return
    
    setCurrentStep('approving')
    setTransactionError(null)
    setTransactionSuccess(null)
    
    try {
      await writeContract({
        address: CONTRACT_ADDRESSES.MOCK_USDC,
        abi: MOCK_USDC_ABI,
        functionName: 'approve',
        args: [CONTRACT_ADDRESSES.AURORA_MULTI_VAULT, parseUSDC(depositAmount)],
      })
    } catch (error: any) {
      console.error('Approval failed:', error)
      setCurrentStep('idle')
      setTransactionError(error?.message || 'Approval failed')
    }
  }

  const handleDeposit = async () => {
    if (!depositAmount || !address) return
    
    setCurrentStep('depositing')
    setTransactionError(null)
    setTransactionSuccess(null)
    
    try {
      await writeContract({
        address: CONTRACT_ADDRESSES.AURORA_MULTI_VAULT,
        abi: AURORA_MULTI_VAULT_ABI,
        functionName: 'deposit',
        args: [parseUSDC(depositAmount), address],
      })
    } catch (error: any) {
      console.error('Deposit failed:', error)
      setCurrentStep('idle')
      setTransactionError(error?.message || 'Deposit failed')
    }
  }

  const handleWithdraw = async () => {
    if (!withdrawAmount || !address) return
    
    setCurrentStep('withdrawing')
    setTransactionError(null)
    setTransactionSuccess(null)
    
    try {
      // Convert shares to assets for withdrawal
      const assetsToWithdraw = parseUSDC(withdrawAmount) // Simplified - should use convertToAssets
      
      await writeContract({
        address: CONTRACT_ADDRESSES.AURORA_MULTI_VAULT,
        abi: AURORA_MULTI_VAULT_ABI,
        functionName: 'withdraw',
        args: [assetsToWithdraw, address, address],
      })
    } catch (error: any) {
      console.error('Withdraw failed:', error)
      setCurrentStep('idle')
      setTransactionError(error?.message || 'Withdrawal failed')
    }
  }

  const setMaxDeposit = () => {
    setDepositAmount(formatUSDC(usdcBalance))
  }

  const setMaxWithdraw = () => {
    setWithdrawAmount(formatUSDC(vaultShares)) // Simplified - should convert shares to assets
  }

  if (!address) {
    return (
      <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 text-center">
        <Wallet className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500 mb-2">Connect your wallet to get started</p>
        <p className="text-sm text-gray-400">Deposit USDC to earn optimized yields across Aurora DeFi</p>
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

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-100">
        <button
          onClick={() => setActiveTab('deposit')}
          className={`flex-1 px-6 py-4 text-center font-medium transition-colors ${
            activeTab === 'deposit'
              ? 'text-black bg-[#00ec97] bg-opacity-10 border-b-2 border-[#00ec97]'
              : 'text-gray-500 hover:text-black hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center justify-center space-x-2">
            <ArrowDownCircle className="w-5 h-5" />
            <span>Deposit</span>
          </div>
        </button>
        <button
          onClick={() => setActiveTab('withdraw')}
          className={`flex-1 px-6 py-4 text-center font-medium transition-colors ${
            activeTab === 'withdraw'
              ? 'text-black bg-[#17d9d4] bg-opacity-10 border-b-2 border-[#17d9d4]'
              : 'text-gray-500 hover:text-black hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center justify-center space-x-2">
            <ArrowUpCircle className="w-5 h-5" />
            <span>Withdraw</span>
          </div>
        </button>
      </div>

      <div className="p-6">
        {activeTab === 'deposit' ? (
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Deposit Amount (USDC)
                </label>
                <button
                  onClick={setMaxDeposit}
                  className="text-xs text-[#00ec97] hover:text-[#00d485] font-medium"
                >
                  MAX
                </button>
              </div>
              <input
                type="number"
                value={depositAmount}
                onChange={(e) => setDepositAmount(e.target.value)}
                placeholder="0.00"
                step="0.000001"
                min="0"
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00ec97] focus:border-transparent"
              />
              <p className="text-sm text-gray-500 mt-2">
                Available: {formatUSDC(usdcBalance)} USDC
              </p>
            </div>

            <div className="flex space-x-3">
              {needsApproval(depositAmount) ? (
                <>
                  <button
                    onClick={handleApprove}
                    disabled={!depositAmount || currentStep !== 'idle' || isPending || isConfirming}
                    className="flex-1 px-4 py-3 bg-gray-100 text-black rounded-lg hover:bg-gray-200 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                  >
                    {currentStep === 'approving' || (isPending && currentStep !== 'depositing') ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Approving...</span>
                      </>
                    ) : (
                      <span>1. Approve</span>
                    )}
                  </button>
                  <button
                    onClick={handleDeposit}
                    disabled={true}
                    className="flex-1 px-4 py-3 bg-gray-200 text-gray-400 rounded-lg font-medium cursor-not-allowed flex items-center justify-center space-x-2"
                  >
                    <span>2. Deposit</span>
                  </button>
                </>
              ) : (
                <button
                  onClick={handleDeposit}
                  disabled={!depositAmount || currentStep !== 'idle' || isPending || isConfirming}
                  className="w-full px-4 py-3 bg-[#00ec97] text-black rounded-lg hover:bg-[#00d485] transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {currentStep === 'depositing' || (isPending && currentStep === 'depositing') ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Depositing...</span>
                    </>
                  ) : (
                    <span>Deposit</span>
                  )}
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Withdraw Amount (USDC)
                </label>
                <button
                  onClick={setMaxWithdraw}
                  className="text-xs text-[#17d9d4] hover:text-[#14c4c0] font-medium"
                >
                  MAX
                </button>
              </div>
              <input
                type="number"
                value={withdrawAmount}
                onChange={(e) => setWithdrawAmount(e.target.value)}
                placeholder="0.00"
                step="0.000001"
                min="0"
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#17d9d4] focus:border-transparent"
              />
              <p className="text-sm text-gray-500 mt-2">
                Available: {formatUSDC(vaultShares)} USDC (estimated)
              </p>
            </div>

            <button
              onClick={handleWithdraw}
              disabled={!withdrawAmount || currentStep !== 'idle' || isPending || isConfirming}
              className="w-full px-4 py-3 bg-[#17d9d4] text-black rounded-lg hover:bg-[#14c4c0] transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {currentStep === 'withdrawing' || (isPending && currentStep === 'withdrawing') ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Withdrawing...</span>
                </>
              ) : (
                <span>Withdraw</span>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}