import { useReadContract } from 'wagmi'
import { CONTRACT_ADDRESSES, AURORA_MULTI_VAULT_ABI, MOCK_USDC_ABI } from '../config/contracts'

export const useContractData = (userAddress?: string) => {
  // Total assets in vault (TVL)
  const { data: totalAssets, isLoading: totalAssetsLoading, refetch: refetchTotalAssets } = useReadContract({
    address: CONTRACT_ADDRESSES.AURORA_MULTI_VAULT,
    abi: AURORA_MULTI_VAULT_ABI,
    functionName: 'totalAssets',
  })

  // Total supply of vault shares
  const { data: totalSupply, isLoading: totalSupplyLoading, refetch: refetchTotalSupply } = useReadContract({
    address: CONTRACT_ADDRESSES.AURORA_MULTI_VAULT,
    abi: AURORA_MULTI_VAULT_ABI,
    functionName: 'totalSupply',
  })

  // Get strategies data
  const { data: strategies, isLoading: strategiesLoading, refetch: refetchStrategies } = useReadContract({
    address: CONTRACT_ADDRESSES.AURORA_MULTI_VAULT,
    abi: AURORA_MULTI_VAULT_ABI,
    functionName: 'getStrategies',
  })

  // User's USDC balance
  const { data: usdcBalance, isLoading: usdcBalanceLoading, refetch: refetchUsdcBalance } = useReadContract({
    address: CONTRACT_ADDRESSES.MOCK_USDC,
    abi: MOCK_USDC_ABI,
    functionName: 'balanceOf',
    args: userAddress ? [userAddress] : undefined,
    query: {
      enabled: !!userAddress,
    },
  })

  // User's vault shares (amvUSDC tokens)
  const { data: vaultShares, isLoading: vaultSharesLoading, refetch: refetchVaultShares } = useReadContract({
    address: CONTRACT_ADDRESSES.AURORA_MULTI_VAULT,
    abi: AURORA_MULTI_VAULT_ABI,
    functionName: 'balanceOf',
    args: userAddress ? [userAddress] : undefined,
    query: {
      enabled: !!userAddress,
    },
  })

  // Calculate current prize (for display purposes - this is now a multi-strategy vault)
  const currentPrize = 0n // No longer a lottery system

  // Calculate user's share percentage
  const sharePercentage = vaultShares && totalSupply && totalSupply > 0n
    ? (Number(vaultShares) / Number(totalSupply)) * 100
    : 0

  // Calculate estimated APY based on strategies
  const estimatedAPY = strategies && Array.isArray(strategies) 
    ? strategies.reduce((acc: number, strategy: any) => {
        // Simplified APY calculation - in real implementation, this would come from strategy contracts
        const strategyAPY = strategy.name === 'Ref Finance' ? 15.2 : 
                           strategy.name === 'TriSolaris' ? 12.8 : 
                           strategy.name === 'Bastion' ? 9.1 : 0
        const allocation = Number(strategy.allocation) / 10000 // Convert from basis points
        return acc + (strategyAPY * allocation)
      }, 0)
    : 12.5 // Default estimated APY

  // Refetch all data
  const refetch = () => {
    refetchTotalAssets()
    refetchTotalSupply()
    refetchStrategies()
    if (userAddress) {
      refetchUsdcBalance()
      refetchVaultShares()
    }
  }

  return {
    totalAssets: totalAssets || 0n,
    totalSupply: totalSupply || 0n,
    strategies: strategies || [],
    currentPrize,
    lastWinner: null, // No longer applicable
    usdcBalance: usdcBalance || 0n,
    vaultShares: vaultShares || 0n,
    sharePercentage,
    estimatedAPY,
    isLoading: totalAssetsLoading || totalSupplyLoading || strategiesLoading || 
               (userAddress && (usdcBalanceLoading || vaultSharesLoading)),
    refetch,
  }
}