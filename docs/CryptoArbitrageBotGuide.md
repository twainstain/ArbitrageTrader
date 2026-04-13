# How to Create a Profitable Crypto Arbitrage Bot (2026)

> Based on [Dapp University's tutorial](https://www.youtube.com/watch?v=-PWyM6adiIE&t=37s) by Gregory from Dapp University.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1 - Project Setup](#step-1---project-setup)
4. [Step 2 - Smart Contract Layer (Flash Loan Arbitrage)](#step-2---smart-contract-layer-flash-loan-arbitrage)
5. [Step 3 - Price Oracle Integration](#step-3---price-oracle-integration)
6. [Step 4 - Bot Logic & Trade Execution](#step-4---bot-logic--trade-execution)
7. [Step 5 - Gas Optimization & Risk Management](#step-5---gas-optimization--risk-management)
8. [Step 6 - Testing & Deployment](#step-6---testing--deployment)
9. [Architecture Overview](#architecture-overview)
10. [Source Code Reference](#source-code-reference)
11. [Resources](#resources)

---

## Overview

A **crypto arbitrage bot** exploits price discrepancies of the same token across different decentralized exchanges (DEXs) such as Uniswap and Sushiswap. By buying low on one exchange and selling high on another — all within a single atomic transaction using **flash loans** — the bot generates profit with zero upfront capital (only gas fees required).

### How It Works

```
1. Bot monitors prices on multiple DEXs (Uniswap, Sushiswap, etc.)
2. Detects a price discrepancy for a token pair
3. Initiates a flash loan (borrow tokens with no collateral)
4. Buys the token on the cheaper exchange
5. Sells the token on the more expensive exchange
6. Repays the flash loan + fee
7. Keeps the profit
```

All of the above happens in a **single transaction** — if any step fails, the entire transaction reverts and you only lose the gas fee.

---

## Prerequisites

### Tools & Software

| Tool | Purpose |
|------|---------|
| **Node.js** (v16+) | JavaScript runtime |
| **npm** or **yarn** | Package management |
| **Hardhat** | Ethereum development framework |
| **Solidity** (^0.8.0) | Smart contract language |
| **Ethers.js** or **Web3.js** | Blockchain interaction library |
| **VS Code** | Code editor (with Solidity extension) |
| **MetaMask** | Browser wallet |
| **Infura** or **Alchemy** | RPC node provider |
| **Git** | Version control |

### Accounts & API Keys

- **Infura/Alchemy account** — for an RPC endpoint to connect to Ethereum
- **MetaMask wallet** — with a private key for signing transactions
- **Etherscan API key** — for contract verification (optional)
- **ETH for gas** — testnet ETH for testing, mainnet ETH for production

### Knowledge

- Basic Solidity & smart contract development
- Understanding of DeFi protocols (Uniswap, Aave, Sushiswap)
- JavaScript/Node.js fundamentals

---

## Step 1 - Project Setup

### Initialize the Project

```bash
mkdir crypto-arbitrage-bot
cd crypto-arbitrage-bot
npm init -y
```

### Install Dependencies

```bash
# Core dependencies
npm install ethers dotenv express moment lodash numeral

# Development dependencies
npm install --save-dev hardhat @nomiclabs/hardhat-ethers @nomiclabs/hardhat-waffle
npm install --save-dev chai mocha

# Smart contract libraries
npm install @openzeppelin/contracts @aave/v3-core
```

### Configure Environment Variables

Create a `.env` file:

```env
# Network Configuration
RPC_URL="https://mainnet.infura.io/v3/YOUR_INFURA_API_KEY"

# Wallet Configuration
PRIVATE_KEY="0xYOUR_PRIVATE_KEY_HERE"
ACCOUNT="0xYOUR_WALLET_ADDRESS_HERE"

# Bot Configuration
POLLING_INTERVAL=1000
MIN_PROFIT_THRESHOLD=0.01

# Optional
ETHERSCAN_API_KEY="YOUR_ETHERSCAN_KEY"
```

> **SECURITY WARNING:** Never commit your `.env` file or share your private key. Add `.env` to your `.gitignore`.

### Hardhat Configuration

Create `hardhat.config.js`:

```javascript
require("@nomiclabs/hardhat-waffle");
require("dotenv").config();

module.exports = {
  solidity: {
    compilers: [
      { version: "0.8.20" }
    ]
  },
  networks: {
    hardhat: {
      forking: {
        url: process.env.RPC_URL,
      }
    },
    mainnet: {
      url: process.env.RPC_URL,
      accounts: [process.env.PRIVATE_KEY]
    },
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: [process.env.PRIVATE_KEY]
    }
  }
};
```

### Project Structure

```
crypto-arbitrage-bot/
├── contracts/
│   └── FlashLoanArbitrage.sol
├── scripts/
│   └── deploy.js
├── src/
│   └── bot.js
├── test/
│   └── arbitrage.test.js
├── .env
├── .env.example
├── .gitignore
├── hardhat.config.js
└── package.json
```

---

## Step 2 - Smart Contract Layer (Flash Loan Arbitrage)

### Core Smart Contract

Create `contracts/FlashLoanArbitrage.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@aave/v3-core/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import "@aave/v3-core/contracts/interfaces/IPoolAddressesProvider.sol";

// Uniswap V2 Router Interface
interface IUniswapV2Router02 {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);

    function getAmountsOut(
        uint amountIn,
        address[] calldata path
    ) external view returns (uint[] memory amounts);
}

contract FlashLoanArbitrage is FlashLoanSimpleReceiverBase {
    address public owner;

    // DEX Router addresses (Ethereum Mainnet)
    IUniswapV2Router02 public immutable uniswapRouter;
    IUniswapV2Router02 public immutable sushiswapRouter;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor(
        address _addressProvider,
        address _uniswapRouter,
        address _sushiswapRouter
    ) FlashLoanSimpleReceiverBase(IPoolAddressesProvider(_addressProvider)) {
        owner = msg.sender;
        uniswapRouter = IUniswapV2Router02(_uniswapRouter);
        sushiswapRouter = IUniswapV2Router02(_sushiswapRouter);
    }

    /// @notice Initiates the flash loan for arbitrage
    /// @param _token The address of the token to borrow
    /// @param _amount The amount to borrow
    /// @param _buyOnUniswap If true, buy on Uniswap and sell on Sushiswap; vice versa if false
    /// @param _tokenB The intermediary token address for the swap path
    function requestFlashLoan(
        address _token,
        uint256 _amount,
        bool _buyOnUniswap,
        address _tokenB
    ) external onlyOwner {
        bytes memory params = abi.encode(_buyOnUniswap, _tokenB);
        POOL.flashLoanSimple(address(this), _token, _amount, params, 0);
    }

    /// @notice Called by Aave after receiving the flash loan
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(POOL), "Caller must be POOL");
        require(initiator == address(this), "Initiator must be this contract");

        (bool buyOnUniswap, address tokenB) = abi.decode(params, (bool, address));

        // Execute arbitrage trades
        _executeArbitrage(asset, amount, buyOnUniswap, tokenB);

        // Repay the flash loan (amount + premium/fee)
        uint256 amountOwed = amount + premium;
        IERC20(asset).approve(address(POOL), amountOwed);

        return true;
    }

    function _executeArbitrage(
        address tokenA,
        uint256 amount,
        bool buyOnUniswap,
        address tokenB
    ) internal {
        // Define the buy and sell routers
        IUniswapV2Router02 buyRouter = buyOnUniswap ? uniswapRouter : sushiswapRouter;
        IUniswapV2Router02 sellRouter = buyOnUniswap ? sushiswapRouter : uniswapRouter;

        // Step 1: Swap tokenA -> tokenB on the buy exchange
        address[] memory buyPath = new address[](2);
        buyPath[0] = tokenA;
        buyPath[1] = tokenB;

        IERC20(tokenA).approve(address(buyRouter), amount);
        uint[] memory buyAmounts = buyRouter.swapExactTokensForTokens(
            amount,
            0, // Accept any amount (calculated off-chain for safety)
            buyPath,
            address(this),
            block.timestamp + 300
        );

        // Step 2: Swap tokenB -> tokenA on the sell exchange
        uint256 tokenBAmount = buyAmounts[buyAmounts.length - 1];
        address[] memory sellPath = new address[](2);
        sellPath[0] = tokenB;
        sellPath[1] = tokenA;

        IERC20(tokenB).approve(address(sellRouter), tokenBAmount);
        sellRouter.swapExactTokensForTokens(
            tokenBAmount,
            0,
            sellPath,
            address(this),
            block.timestamp + 300
        );
    }

    /// @notice Withdraw profits
    function withdrawToken(address _token) external onlyOwner {
        uint256 balance = IERC20(_token).balanceOf(address(this));
        require(balance > 0, "No balance");
        IERC20(_token).transfer(owner, balance);
    }

    /// @notice Withdraw ETH
    function withdrawETH() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No ETH balance");
        payable(owner).transfer(balance);
    }

    receive() external payable {}
}
```

### Key Contract Addresses (Ethereum Mainnet)

| Contract | Address |
|----------|---------|
| **Aave V3 Pool Addresses Provider** | `0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e` |
| **Uniswap V2 Router** | `0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D` |
| **Sushiswap Router** | `0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F` |
| **WETH** | `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2` |
| **USDC** | `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` |
| **DAI** | `0x6B175474E89094C44Da98b954EedeAC495271d0F` |

---

## Step 3 - Price Oracle Integration

### Monitoring Prices on Multiple DEXs

Create `src/priceMonitor.js`:

```javascript
const { ethers } = require("ethers");
require("dotenv").config();

// Uniswap V2 Router ABI (simplified)
const ROUTER_ABI = [
  "function getAmountsOut(uint amountIn, address[] memory path) public view returns (uint[] memory amounts)"
];

// Contract addresses
const UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
const SUSHISWAP_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F";

class PriceMonitor {
  constructor(provider) {
    this.provider = provider;
    this.uniswapRouter = new ethers.Contract(UNISWAP_ROUTER, ROUTER_ABI, provider);
    this.sushiswapRouter = new ethers.Contract(SUSHISWAP_ROUTER, ROUTER_ABI, provider);
  }

  /**
   * Get the price of tokenA in terms of tokenB on a given DEX
   */
  async getPrice(router, amountIn, tokenA, tokenB) {
    try {
      const amounts = await router.getAmountsOut(amountIn, [tokenA, tokenB]);
      return amounts[1];
    } catch (error) {
      console.error("Error fetching price:", error.message);
      return null;
    }
  }

  /**
   * Check for arbitrage opportunity between Uniswap and Sushiswap
   */
  async checkArbitrage(tokenA, tokenB, amountIn) {
    const [uniswapPrice, sushiswapPrice] = await Promise.all([
      this.getPrice(this.uniswapRouter, amountIn, tokenA, tokenB),
      this.getPrice(this.sushiswapRouter, amountIn, tokenA, tokenB),
    ]);

    if (!uniswapPrice || !sushiswapPrice) return null;

    const uniPrice = parseFloat(ethers.formatUnits(uniswapPrice, 18));
    const sushiPrice = parseFloat(ethers.formatUnits(sushiswapPrice, 18));

    const diffPercent = ((Math.abs(uniPrice - sushiPrice) / Math.min(uniPrice, sushiPrice)) * 100);

    return {
      uniswapPrice: uniPrice,
      sushiswapPrice: sushiPrice,
      diffPercent: diffPercent.toFixed(4),
      buyOnUniswap: sushiPrice > uniPrice,
      profitable: diffPercent > 0.6 // Must exceed flash loan fee (0.05%) + gas + slippage
    };
  }
}

module.exports = PriceMonitor;
```

### Chainlink Price Feed (Optional Verification)

```solidity
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract PriceConsumer {
    AggregatorV3Interface internal priceFeed;

    constructor(address _priceFeed) {
        priceFeed = AggregatorV3Interface(_priceFeed);
    }

    function getLatestPrice() public view returns (int) {
        (, int price, , , ) = priceFeed.latestRoundData();
        return price;
    }
}
```

---

## Step 4 - Bot Logic & Trade Execution

### Main Bot Script

Create `src/bot.js`:

```javascript
const { ethers } = require("ethers");
const PriceMonitor = require("./priceMonitor");
require("dotenv").config();

// ========== CONFIGURATION ==========
const POLLING_INTERVAL = process.env.POLLING_INTERVAL || 1000; // ms
const MIN_PROFIT_THRESHOLD = process.env.MIN_PROFIT_THRESHOLD || 0.01; // ETH

// Token addresses (Ethereum Mainnet)
const WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";
const USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";
const DAI  = "0x6B175474E89094C44Da98b954EedeAC495271d0F";

// Flash loan contract ABI (simplified)
const FLASH_LOAN_ABI = [
  "function requestFlashLoan(address _token, uint256 _amount, bool _buyOnUniswap, address _tokenB) external"
];

// ========== SETUP ==========
const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
const priceMonitor = new PriceMonitor(provider);

const flashLoanContract = new ethers.Contract(
  process.env.FLASH_LOAN_CONTRACT_ADDRESS,
  FLASH_LOAN_ABI,
  wallet
);

// Token pairs to monitor
const TOKEN_PAIRS = [
  { tokenA: WETH, tokenB: DAI,  name: "WETH/DAI",  amount: ethers.parseEther("10") },
  { tokenA: WETH, tokenB: USDC, name: "WETH/USDC", amount: ethers.parseEther("10") },
];

// ========== CORE BOT LOGIC ==========
let isExecuting = false;

async function checkAndExecute() {
  if (isExecuting) return;
  isExecuting = true;

  try {
    for (const pair of TOKEN_PAIRS) {
      console.log(`\n--- Checking ${pair.name} ---`);

      const result = await priceMonitor.checkArbitrage(
        pair.tokenA,
        pair.tokenB,
        pair.amount
      );

      if (!result) {
        console.log("Could not fetch prices. Skipping...");
        continue;
      }

      console.log(`Uniswap:   ${result.uniswapPrice}`);
      console.log(`Sushiswap: ${result.sushiswapPrice}`);
      console.log(`Diff:      ${result.diffPercent}%`);

      if (result.profitable) {
        console.log(">>> ARBITRAGE OPPORTUNITY DETECTED! <<<");

        // Estimate gas cost
        const gasPrice = (await provider.getFeeData()).gasPrice;
        const estimatedGas = 500000n; // Conservative estimate
        const gasCost = gasPrice * estimatedGas;

        console.log(`Estimated gas cost: ${ethers.formatEther(gasCost)} ETH`);

        // Execute the flash loan arbitrage
        console.log("Executing flash loan...");
        const tx = await flashLoanContract.requestFlashLoan(
          pair.tokenA,
          pair.amount,
          result.buyOnUniswap,
          pair.tokenB,
          {
            gasLimit: 500000,
            gasPrice: gasPrice
          }
        );

        console.log(`Transaction submitted: ${tx.hash}`);
        const receipt = await tx.wait();
        console.log(`Transaction confirmed in block ${receipt.blockNumber}`);
        console.log(`Gas used: ${receipt.gasUsed.toString()}`);
      } else {
        console.log("No profitable opportunity. Waiting...");
      }
    }
  } catch (error) {
    console.error("Error:", error.message);
  }

  isExecuting = false;
}

// ========== BALANCE CHECKER ==========
async function checkBalances() {
  const ethBalance = await provider.getBalance(wallet.address);
  console.log(`\nETH Balance: ${ethers.formatEther(ethBalance)} ETH`);

  for (const pair of TOKEN_PAIRS) {
    const tokenContract = new ethers.Contract(
      pair.tokenB,
      ["function balanceOf(address) view returns (uint256)"],
      provider
    );
    const balance = await tokenContract.balanceOf(wallet.address);
    console.log(`${pair.name.split("/")[1]} Balance: ${ethers.formatUnits(balance, 18)}`);
  }
}

// ========== START BOT ==========
async function main() {
  console.log("=== Crypto Arbitrage Bot Started ===");
  console.log(`Wallet: ${wallet.address}`);
  console.log(`Polling interval: ${POLLING_INTERVAL}ms`);
  console.log(`Monitoring ${TOKEN_PAIRS.length} pairs\n`);

  await checkBalances();

  // Start polling
  setInterval(async () => {
    await checkAndExecute();
  }, POLLING_INTERVAL);
}

main().catch(console.error);
```

---

## Step 5 - Gas Optimization & Risk Management

### Gas Optimization Strategies

1. **Minimize storage operations** — storage reads/writes are the most expensive operations
2. **Batch operations** — combine multiple swaps into a single transaction
3. **Use `calldata` instead of `memory`** for function parameters that are read-only
4. **Dynamic gas pricing** — adjust gas price based on network conditions

```javascript
// Dynamic gas price estimation
async function getOptimalGasPrice(provider) {
  const feeData = await provider.getFeeData();
  return {
    gasPrice: feeData.gasPrice,
    maxFeePerGas: feeData.maxFeePerGas,
    maxPriorityFeePerGas: feeData.maxPriorityFeePerGas
  };
}
```

### Risk Management Checklist

- [ ] **Set maximum trade size** — limit exposure per trade
- [ ] **Slippage protection** — set minimum output amounts in swaps
- [ ] **Gas price ceiling** — skip trades when gas is too high
- [ ] **Circuit breaker** — pause bot after consecutive failures
- [ ] **Monitor mempool** — watch for front-running (MEV)
- [ ] **Use Flashbots** — submit transactions privately to avoid front-running
- [ ] **Nonce management** — prevent stuck/duplicate transactions

### Front-Running Protection with Flashbots

```javascript
const { FlashbotsBundleProvider } = require("@flashbots/ethers-provider-bundle");

// Submit transactions through Flashbots to avoid mempool exposure
const flashbotsProvider = await FlashbotsBundleProvider.create(
  provider,
  wallet,
  "https://relay.flashbots.net"
);
```

---

## Step 6 - Testing & Deployment

### Unit Tests

Create `test/arbitrage.test.js`:

```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("FlashLoanArbitrage", function () {
  let flashLoanArbitrage;
  let owner;

  beforeEach(async function () {
    [owner] = await ethers.getSigners();

    const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrage");
    flashLoanArbitrage = await FlashLoanArbitrage.deploy(
      "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e", // Aave Provider
      "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", // Uniswap Router
      "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"  // Sushiswap Router
    );
  });

  it("Should set the correct owner", async function () {
    expect(await flashLoanArbitrage.owner()).to.equal(owner.address);
  });

  it("Should only allow owner to request flash loan", async function () {
    const [, nonOwner] = await ethers.getSigners();
    await expect(
      flashLoanArbitrage.connect(nonOwner).requestFlashLoan(
        ethers.ZeroAddress, 0, true, ethers.ZeroAddress
      )
    ).to.be.revertedWith("Not owner");
  });
});
```

### Testing with Hardhat Fork

```bash
# Run tests against a mainnet fork
npx hardhat test --network hardhat

# Run the bot locally against a fork
npx hardhat run src/bot.js --network hardhat
```

### Deploy Script

Create `scripts/deploy.js`:

```javascript
const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrage");
  const contract = await FlashLoanArbitrage.deploy(
    "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e", // Aave V3 Provider
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", // Uniswap V2 Router
    "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"  // Sushiswap Router
  );

  await contract.waitForDeployment();
  console.log("FlashLoanArbitrage deployed to:", await contract.getAddress());
}

main().catch(console.error);
```

### Deployment Steps

```bash
# 1. Compile contracts
npx hardhat compile

# 2. Run tests
npx hardhat test

# 3. Deploy to testnet first (e.g., Sepolia)
npx hardhat run scripts/deploy.js --network sepolia

# 4. Verify contract on Etherscan
npx hardhat verify --network sepolia DEPLOYED_ADDRESS \
  "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e" \
  "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D" \
  "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"

# 5. Deploy to mainnet (when ready)
npx hardhat run scripts/deploy.js --network mainnet

# 6. Start the bot
node src/bot.js
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                   ARBITRAGE BOT                      │
│                                                      │
│  ┌──────────────┐    ┌─────────────────────────┐     │
│  │ Price Monitor │───>│  Arbitrage Detector     │     │
│  │ (polling)     │    │  (compare DEX prices)   │     │
│  └──────────────┘    └────────────┬────────────┘     │
│                                   │                   │
│                          Opportunity Found?           │
│                                   │                   │
│                                  YES                  │
│                                   │                   │
│                      ┌────────────▼────────────┐     │
│                      │  Gas Cost Estimator     │     │
│                      │  (is it still worth it?)│     │
│                      └────────────┬────────────┘     │
│                                   │                   │
│                                  YES                  │
│                                   │                   │
│  ┌────────────────────────────────▼──────────────┐   │
│  │          FLASH LOAN SMART CONTRACT            │   │
│  │                                                │   │
│  │  1. Borrow from Aave (flash loan)             │   │
│  │  2. Buy on cheaper DEX (Uniswap/Sushiswap)   │   │
│  │  3. Sell on expensive DEX                     │   │
│  │  4. Repay loan + 0.05% fee                   │   │
│  │  5. Keep profit                               │   │
│  └────────────────────────────────────────────────│   │
└──────────────────────────────────────────────────────┘

          ETHEREUM BLOCKCHAIN
┌──────────────────────────────────────────────────────┐
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ Uniswap  │  │ Sushiswap │  │ Aave Flash Loans │  │
│  │ V2       │  │           │  │ V3               │  │
│  └──────────┘  └───────────┘  └──────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## Source Code Reference

### Dapp University's Trading Bot Repository

- **Repository:** [github.com/dappuniversity/trading-bot](https://github.com/dappuniversity/trading-bot)
- **Price Bot:** [github.com/dappuniversity/price-bot](https://github.com/dappuniversity/price-bot)

### Original Bot (Simplified Reference)

The original Dapp University bot polls Uniswap for ETH/DAI prices and executes swaps when the price hits a target:

```javascript
// Simplified from dappuniversity/trading-bot/index.js
async function monitorPrice() {
  const daiAmount = await exchangeContract.methods
    .getEthToTokenInputPrice(ETH_AMOUNT).call();
  const price = web3.utils.fromWei(daiAmount.toString(), 'Ether');

  console.log('ETH Price:', price, 'DAI');

  if (price <= ETH_SELL_PRICE) {
    await sellEth(ETH_AMOUNT, daiAmount);
  }
}

// Poll every second
setInterval(monitorPrice, POLLING_INTERVAL);
```

---

## Resources

### Video Tutorial
- [How to create a profitable crypto arbitrage bot in 2026 — Dapp University](https://www.youtube.com/watch?v=-PWyM6adiIE&t=37s)

### Documentation
- [Aave V3 Flash Loans](https://docs.aave.com/developers/guides/flash-loans)
- [Uniswap V2 Docs](https://docs.uniswap.org/contracts/v2/overview)
- [Sushiswap Docs](https://docs.sushi.com/)
- [Hardhat Documentation](https://hardhat.org/docs)
- [Ethers.js Documentation](https://docs.ethers.org/v6/)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)
- [Flashbots Docs](https://docs.flashbots.net/)

### Related Tutorials
- [Build Crypto Arbitrage Flash Loan Bot (Complete Guide)](https://www.rapidinnovation.io/post/how-to-build-crypto-arbitrage-flash-loan-bot)
- [Flashbots Automated Arbitrage Bot](https://docs.flashbots.net/flashbots-mev-share/searchers/tutorials/flash-loan-arbitrage/bot)
- [Uniswap V3 Flash Swap Tutorial](https://medium.com/coinmonks/tutorial-of-flash-swaps-of-uniswap-v3-73c0c846b822)

### Community GitHub Projects
- [flash-arb-bot](https://github.com/manuelinfosec/flash-arb-bot) — Flash loan arbitrage between Uniswap and Sushiswap
- [UniV3FlashSwapDualArbBot](https://github.com/SimSimButDifferent/UniV3FlashSwapDualArbBot) — Uniswap V3 flash swap arbitrage
- [Trading-Bot](https://github.com/SquilliamX/Trading-Bot) — Flash loan-powered arbitrage with DyDx

---

> **Disclaimer:** This guide is for educational purposes. Crypto arbitrage involves financial risk. Always test on testnets first, start with small amounts, and understand the risks of smart contract bugs, front-running, and market volatility.
