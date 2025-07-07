import React from 'react'
import { useContractData } from '../hooks/useContractData'
import { formatUSDC } from '../utils/format'
import { TrendingUp, Target, Users, Zap } from 'lucide-react'

export const Dashboard: React.FC = () => {
  const { totalAssets, strategies, estimatedAPY, isLoading } = useContractData()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
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

  // Calculate total deployed across strategies
  const totalDeployed = Array.isArray(strategies) 
    ? strategies.reduce((acc: bigint, strategy: any) => acc + BigInt(strategy.balance || 0), 0n)
    : 0n

  const deploymentRate = totalAssets > 0n ? Number(totalDeployed * 100n / totalAssets) : 0

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">Total Assets (AUM)</h3>
          <div className="p-2 bg-[#00ec97] bg-opacity-10 rounded-lg">
            <TrendingUp className="w-5 h-5 text-[#00ec97]" />
          </div>
        </div>
        <p className="text-3xl font-semibold text-black">${formatUSDC(totalAssets)}</p>
        <p className="text-sm text-gray-500 mt-1">Assets under management</p>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">Portfolio APY</h3>
          <div className="p-2 bg-[#17d9d4] bg-opacity-10 rounded-lg">
            <Target className="w-5 h-5 text-[#17d9d4]" />
          </div>
        </div>
        <p className="text-3xl font-semibold text-black">{estimatedAPY.toFixed(1)}%</p>
        <p className="text-sm text-gray-500 mt-1">Expected annual yield</p>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">Active Strategies</h3>
          <div className="p-2 bg-[#9797ff] bg-opacity-10 rounded-lg">
            <Users className="w-5 h-5 text-[#9797ff]" />
          </div>
        </div>
        <p className="text-3xl font-semibold text-black">
          {Array.isArray(strategies) ? strategies.filter((s: any) => s.active).length : 0}
        </p>
        <p className="text-sm text-gray-500 mt-1">Aurora DeFi protocols</p>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">Deployment Rate</h3>
          <div className="p-2 bg-[#ff7966] bg-opacity-10 rounded-lg">
            <Zap className="w-5 h-5 text-[#ff7966]" />
          </div>
        </div>
        <p className="text-3xl font-semibold text-black">{deploymentRate.toFixed(1)}%</p>
        <p className="text-sm text-gray-500 mt-1">Capital deployed</p>
      </div>
    </div>
  )
}