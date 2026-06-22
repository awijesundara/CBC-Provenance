const hre = require("hardhat");

async function main() {
  console.log("Deploying DIDRegistry contract...");
  
  const DIDRegistry = await hre.ethers.getContractFactory("DIDRegistry");
  const contract = await DIDRegistry.deploy();
  await contract.deployed();
  
  console.log("✅ DIDRegistry deployed to:", contract.address);
  console.log("\nDeployment Details:");
  console.log("- Chain ID: 421614 (Arbitrum Sepolia)");
  console.log("- Contract Address:", contract.address);
  console.log("\nNext steps:");
  console.log("1. Save contract address to .env as ARBITRUM_CONTRACT_ADDRESS");
  console.log("2. Deploy issuer: cd issuer && python vc_issuer.py");
  console.log("3. Deploy webhook: cd webhook && docker build -t cbc-webhook .");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
