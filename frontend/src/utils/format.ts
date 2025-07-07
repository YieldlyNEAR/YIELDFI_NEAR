import { formatEther, parseEther } from 'viem'

export const formatAddress = (address: string): string => {
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

export const formatBalance = (balance: bigint, decimals: number = 6): string => {
  const divisor = BigInt(10 ** decimals)
  const whole = balance / divisor
  const remainder = balance % divisor
  
  if (remainder === 0n) {
    return whole.toString()
  }
  
  const remainderStr = remainder.toString().padStart(decimals, '0')
  const trimmedRemainder = remainderStr.replace(/0+$/, '')
  
  return `${whole}.${trimmedRemainder}`
}

export const formatPercentage = (value: number): string => {
  return `${value.toFixed(4)}%`
}

export const parseUSDC = (value: string): bigint => {
  const num = parseFloat(value)
  return BigInt(Math.floor(num * 1000000)) // USDC has 6 decimals
}

export const formatUSDC = (value: bigint): string => {
  return formatBalance(value, 6)
}

// New function for vault shares (18 decimals)
export const formatVaultShares = (value: bigint): string => {
  return formatBalance(value, 18)
}

export const parseVaultShares = (value: string): bigint => {
  const num = parseFloat(value)
  return BigInt(Math.floor(num * 1000000000000000000)) // 18 decimals
}