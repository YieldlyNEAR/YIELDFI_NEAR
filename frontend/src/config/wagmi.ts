import { createConfig, http } from 'wagmi'
import { auroraTestnet } from 'wagmi/chains'
import { metaMask, injected } from 'wagmi/connectors'

// Define Aurora Testnet chain configuration
const auroraTestnetConfig = {
  ...auroraTestnet,
  rpcUrls: {
    default: {
      http: ['https://testnet.aurora.dev'],
    },
    public: {
      http: ['https://testnet.aurora.dev'],
    },
  },
}

export const config = createConfig({
  chains: [auroraTestnetConfig],
  connectors: [
    metaMask({
      dappMetadata: {
        name: 'Aurora Prize Savings',
        url: 'https://aurora-prize-savings.com',
      },
    }),
    injected({
      target: 'metaMask',
    }),
  ],
  transports: {
    [auroraTestnet.id]: http('https://testnet.aurora.dev'),
  },
  ssr: false,
})

declare module 'wagmi' {
  interface Register {
    config: typeof config
  }
}