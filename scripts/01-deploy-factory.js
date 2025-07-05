const hre = require("hardhat");
const { ethers } = hre;

async function main() {
  console.log("\n--- STEP 1: DEPLOYING VAULT FACTORY ---\n");
  const [deployer] = await ethers.getSigners();
  console.log(`➤ Deployer: ${deployer.address}\n`);

  const existingUsdcAddress = "0xC0933C5440c656464D1Eb1F886422bE3466B1459";
  console.log(`✅ Using existing MockUSDC token at: ${existingUsdcAddress}`);

  // Deploy VaultFactory
  console.log("\n🚀 Deploying VaultFactory...");
  const VaultFactory = await ethers.getContractFactory("VaultFactory");
  const vaultFactory = await VaultFactory.deploy(
    deployer.address, // defaultManager
    deployer.address, // defaultAgent
    deployer.address, // treasury
    0 // creationFee
  );
  await vaultFactory.deployed();
  console.log(`✅ VaultFactory deployed at: ${vaultFactory.address}`);

  console.log("\n\n✅ --- FACTORY DEPLOYED --- ✅");
  console.log("------------------------------------");
  console.log("ACTION REQUIRED:");
  console.log("1. Make sure your .env file has the correct USDC address:");
  console.log(`USDC_TOKEN_ADDRESS=${existingUsdcAddress}`);
  console.log("2. Add the new Vault Factory address to your .env file:");
  console.log(`VAULT_FACTORY_ADDRESS=${vaultFactory.address}`);
  console.log("------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
