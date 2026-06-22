require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: "0.8.21",
  networks: {
    arbitrumSepolia: {
      url: process.env.ARBITRUM_RPC_URL || "https://sepolia-rollup.arbitrum.io/rpc",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 421614,
    }
  },
  etherscan: {
    apiKey: process.env.ARBISCAN_API_KEY || ""
  }
};
