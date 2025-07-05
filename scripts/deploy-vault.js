const hre = require("hardhat");
const { ethers } = hre;

async function main() {
  console.log("\n--- STEP 1: DEPLOYING THE VAULT DIRECTLY ---\n");
  const [deployer] = await ethers.getSigners();
  console.log(`➤ Deployer: ${deployer.address}\n`);

  const existingUsdcAddress = "0xC0933C5440c656464D1Eb1F886422bE3466B1459";
  console.log(`✅ Using existing MockUSDC token at: ${existingUsdcAddress}`);

  // Deploy Vault directly
  console.log("\n🚀 Deploying Vault...");
  const Vault = await ethers.getContractFactory("Vault");
  const vault = await Vault.deploy(
    existingUsdcAddress,          // assetToken
    "Aurora Yield Lottery Vault", // name
    "ayLV",                       // symbol
    deployer.address,             // manager
    deployer.address              // agent
  );
  await vault.deployed();
  console.log(`✅ Vault deployed at: ${vault.address}`);

  console.log("\n\n✅ --- VAULT DEPLOYED --- ✅");
  console.log("------------------------------------");
  console.log("ACTION REQUIRED:");
  console.log("1. Make sure your .env file has the correct USDC address:");
  console.log(`USDC_TOKEN_ADDRESS=${existingUsdcAddress}`);
  console.log("2. Add the new Vault address to your .env file:");
  console.log(`VAULT_ADDRESS=${vault.address}`);
  console.log("------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});