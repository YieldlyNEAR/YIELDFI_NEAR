const hre = require("hardhat");
const { ethers } = hre;
require('dotenv').config();

async function main() {
  console.log("\n--- STEP 2: CREATING THE VAULT ---\n");
  const [deployer] = await ethers.getSigners();
  const usdcAddress = process.env.USDC_TOKEN_ADDRESS;
  const factoryAddress = process.env.VAULT_FACTORY_ADDRESS;

  if (!usdcAddress || !factoryAddress) {
    throw new Error("Missing USDC_TOKEN_ADDRESS or VAULT_FACTORY_ADDRESS in .env file");
  }

  console.log(`✅ Using VaultFactory at: ${factoryAddress}`);
  const vaultFactory = await ethers.getContractAt("VaultFactory", factoryAddress);

  console.log("\n🏭 Calling createVault...");
  const vaultTx = await vaultFactory.createVault({
    asset: usdcAddress,
    name: "Aurora Yield Lottery Vault",
    symbol: "ayLV",
    manager: deployer.address,
    agent: deployer.address,
  });

  const receipt = await vaultTx.wait();
  const vaultCreatedEvent = receipt.events.find(e => e.event === "VaultCreated");
  const vaultAddress = vaultCreatedEvent.args.vaultAddress;
  
  console.log(`✅ New Vault created successfully!`);

  console.log("\n\n✅ --- VAULT CREATED --- ✅");
  console.log("------------------------------------");
  console.log("ACTION REQUIRED:");
  console.log("1. Copy the new Vault address.");
  console.log("2. Paste it into your .env file:");
  console.log(`VAULT_ADDRESS=${vaultAddress}`);
  console.log("------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
