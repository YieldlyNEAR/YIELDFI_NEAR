const hre = require("hardhat");
const { ethers } = hre;
require('dotenv').config();

async function main() {
  console.log("\n--- STEP 3: DEPLOYING AND LINKING STRATEGY ---\n");
  const usdcAddress = process.env.USDC_TOKEN_ADDRESS;
  const vaultAddress = process.env.VAULT_ADDRESS;

  if (!usdcAddress || !vaultAddress) {
    throw new Error("Missing USDC_TOKEN_ADDRESS or VAULT_ADDRESS in .env file");
  }

  console.log(`✅ Targeting Vault at: ${vaultAddress}`);

  // Deploy the Strategy
  console.log("\n🚀 Deploying NearVrfYieldStrategy...");
  const NearVrfStrategy = await ethers.getContractFactory("NearVrfYieldStrategy");
  const nearStrategy = await NearVrfStrategy.deploy(
    vaultAddress,
    usdcAddress,
    ethers.constants.AddressZero
  );
  await nearStrategy.deployed();
  const nearStrategyAddress = nearStrategy.address;
  console.log(`✅ NearVrfYieldStrategy deployed at: ${nearStrategyAddress}`);

  // Link the Strategy
  console.log("\n🔗 Adding the new strategy to the Vault...");
  const vault = await ethers.getContractAt("Vault", vaultAddress);
  const addStrategyTx = await vault.addStrategy(nearStrategyAddress);
  await addStrategyTx.wait();
  console.log("✅ Strategy linked successfully!");
  
  console.log("\n\n🎉 --- AURORA DEPLOYMENT COMPLETE --- 🎉");
  console.log("------------------------------------");
  console.log(`   Mock USDC Token:      ${usdcAddress}`);
  console.log(`   Vault Factory:        ${process.env.VAULT_FACTORY_ADDRESS}`);
  console.log(`   Lottery Vault:        ${vaultAddress}`);
  console.log(`   NEAR VRF Strategy:    ${nearStrategyAddress}`);
  console.log("------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});