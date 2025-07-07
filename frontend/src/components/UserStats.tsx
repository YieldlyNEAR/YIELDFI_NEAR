import React from 'react'
import { useAccount } from 'wagmi'
import { useContractData } from '../hooks/useContractData'
import { formatUSDC, formatPercentage } from '../utils/format'
import { User, Target, TrendingUp, Zap } from 'lucide-react'

export const UserStats: React.FC = () => {
  const { address } = useAccount()
  const { vaultShares, sharePercentage, estimatedAPY, totalAssets, isLoading } = useContractData(address)

  if (!address) {
    return (
      <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 text-center">
        <p className="text-gray-500">Connect your wallet to view your stats</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded w-3/4"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Calculate estimated value in USDC (simplified)
  const estimatedValue = vaultShares // In a real implementation, use convertToAssets

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">Your Deposit</h3>
          <div className="p-2 bg-[#00ec97] bg-opacity-10 rounded-lg">
            <User className="w-5 h-5 text-[#00ec97]" />
          </div>
        </div>
        <p className="text-3xl font-semibold text-black">${formatUSDC(estimatedValue)}</p>
        <p className="text-sm text-gray-500 mt-1">Estimated value</p>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">Portfolio Share</h3>
          <div className="p-2 bg-[#17d9d4] bg-opacity-10 rounded-lg">
            <Target className="w-5 h-5 text-[#17d9d4]" />
          </div>
        </div>
        <p className="text-3xl font-semibold text-black">{sharePercentage.toFixed(4)}%</p>
        <p className="text-sm text-gray-500 mt-1">Of total vault</p>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">Expected APY</h3>
          <div className="p-2 bg-[#9797ff] bg-opacity-10 rounded-lg">
            <TrendingUp className="w-5 h-5 text-[#9797ff]" />
          </div>
        </div>
        <p className="text-3xl font-semibold text-black">{estimatedAPY.toFixed(1)}%</p>
        <p className="text-sm text-gray-500 mt-1">Annual percentage yield</p>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">Vault Shares</h3>
          <div className="p-2 bg-[#ff7966] bg-opacity-10 rounded-lg">
            <Zap className="w-5 h-5 text-[#ff7966]" />
          </div>
        </div>
        <p className="text-3xl font-semibold text-black">{formatUSDC(vaultShares)}</p>
        <p className="text-sm text-gray-500 mt-1">amvUSDC tokens</p>
      </div>
    </div>
  )
}