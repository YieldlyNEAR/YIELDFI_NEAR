const hre = require("hardhat");
const { ethers, network } = hre;

async function main() {
  console.log(`\n🛰️  Deploying contracts to Aurora Testnet: ${network.name}`);

  // 1. Get Deployer & Balance
  // =============================
  const [deployer] = await ethers.getSigners();
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log(`➤ Deployer: ${deployer.address}`);
  // Corrected for ethers v5: use ethers.utils.formatEther
  console.log(`➤ Balance: ${ethers.utils.formatEther(balance)} ETH\n`);

  // 2. Use the already deployed MockUSDC Token
  // ============================================
  // This step is skipped to avoid the CreateContractLimit error.
  const usdcAddress = "0xC0933C5440c656464D1Eb1F886422bE3466B1459"; // Address from your previous deployment
  console.log(`✅ Using existing MockUSDC token at: ${usdcAddress}\n`);

  // 3. Deploy VaultFactory
  // =============================
  const defaultManager = deployer.address;
  const defaultAgent = deployer.address;
  const treasury = deployer.address;
  // Corrected for ethers v5: use ethers.utils.parseEther
  const creationFee = ethers.utils.parseEther("0");

  console.log("🚀 Deploying VaultFactory...");
  const VaultFactory = await ethers.getContractFactory("VaultFactory");
  const vaultFactory = await VaultFactory.deploy(
    defaultManager,
    defaultAgent,
    treasury,
    creationFee
  );
  await vaultFactory.deployed();
  const factoryAddress = vaultFactory.address;
  console.log(`✅ VaultFactory deployed at: ${factoryAddress}\n`);

  // 4. Create a New Vault using the Factory
  // ==========================================
  console.log("🏭 Using VaultFactory to create a new Vault for Aurora...");
  const vaultTx = await vaultFactory.createVault({
    asset: usdcAddress,
    name: "Aurora Yield Lottery Vault",
    symbol: "ayLV",
    manager: deployer.address,
    agent: deployer.address,
  });
  
  const receipt = await vaultTx.wait();
  // In ethers v5, events are often found in the 'events' array
  const vaultCreatedEvent = receipt.events.find(
    (event) => event.event === "VaultCreated"
  );

  if (!vaultCreatedEvent) {
    throw new Error("❌ Vault creation failed: Could not find VaultCreated event.");
  }
  
  const vaultAddress = vaultCreatedEvent.args.vaultAddress;
  console.log(`✅ New Vault created successfully at: ${vaultAddress}\n`);
  
  const vault = await ethers.getContractAt("Vault", vaultAddress);

  // 5. Deploy the NearVrfYieldStrategy
  // ======================================
  console.log("🚀 Deploying NearVrfYieldStrategy...");
  const NearVrfStrategy = await ethers.getContractFactory("NearVrfYieldStrategy"); 
  const nearStrategy = await NearVrfStrategy.deploy(
    vaultAddress,
    usdcAddress,
    ethers.constants.AddressZero // Use ethers.constants.AddressZero for v5
  );
  await nearStrategy.deployed();
  const nearStrategyAddress = nearStrategy.address;
  console.log(`✅ NearVrfYieldStrategy deployed at: ${nearStrategyAddress}\n`);
  
  // 6. Connect the Strategy to the Vault
  // =====================================
  console.log("🔗 Adding the new Aurora/NEAR VRF strategy to the Vault...");
  const addStrategyTx = await vault.addStrategy(nearStrategyAddress);
  await addStrategyTx.wait();
  console.log("✅ Strategy added and configured successfully!\n");

  // Final Summary
  // =====================================
  console.log("🎉 --- AURORA DEPLOYMENT SUMMARY --- 🎉");
  console.log("------------------------------------");
  console.log(`   Mock USDC Token:      ${usdcAddress}`);
  console.log(`   Vault Factory:        ${factoryAddress}`);
  console.log(`   Lottery Vault:        ${vaultAddress}`);
  console.log(`   NEAR VRF Strategy:    ${nearStrategyAddress}`);
  console.log("------------------------------------\n");
  
  console.log("🔮 NEAR VRF Integration Details:");
  console.log(`   The NearVrfYieldStrategy uses the NEAR pre-compile at:`);
  console.log(`   0x0000000000000000000000000000000000000042`);
  console.log(`   This provides secure, on-chain randomness on the Aurora network.\n`);
  
  console.log("🎯 Next Steps on Aurora:");
  console.log("   1. Use the MockUSDC contract to mint test tokens.");
  console.log("   2. Approve the Vault to spend your USDC.");
  console.log("   3. Deposit USDC into the Vault.");
  console.log("   4. Use your NEAR agent to manage the protocol!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
