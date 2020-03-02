# MelonJS

[![Build status](https://img.shields.io/travis/melonproject/melonjs)](https://travis-ci.org/melonproject/melonjs) [![Package version](https://img.shields.io/npm/v/@melonproject/melonjs)](https://www.npmjs.com/package/@melonproject/melonjs) ![License](https://img.shields.io/npm/l/@melonproject/melonjs)

**MelonJS** is a convenient JavaScript interface for interacting with the Melon Protocol smart contracts on the Ethereum blockchain. It allows users to call functions on the contracts at every point of a fund's life cycle. We envision this functionality enabling a wide variety of apps, from fund creation and investor relations management to trading bots and automatic portfolio rebalancing.

## Summary

MelonJS allows you to create instances of and call functions on the following Melon contracts:

* Accounting
* Fee Manager
* Participation
* Policy Manager
* Shares
* Trading
* Vault
* CompleteSetup

## Installation and Development

This library is published as an [npm package](https://www.npmjs.com/package/@melonproject/melonjs). You can install it through npm or yarn.

```bash
# Using yarn
yarn add @melonproject/melonjs

# Using npm
npm install @melonproject/melonjs
```

Before you can start developing, you'll need to have [Node.js](https://nodejs.org) and [Yarn](https://yarnpkg.com) installed.

Installing only takes two commands and you're ready to roll:

```bash
# Install all library dependencies.
yarn install

# Generate the abi and bytecode files for the smart contracts.
yarn codegen
```

You are now ready to start development. Check out the `package.json` scripts for useful commands for testing, test coverage, building and watch mode.

## Usage

### Building Blocks

Throughout these examples, we'll be using `address` variables to refer to the deployed versions of various Melon Protocol contracts specific an active fund. Though these are accessible via the blockchain and the `Hub` contract, they're also indexed on IPFS and accessible freely through the MelonGQL package. We'll also be using the BigNumber.js library to handle all token math.

It's worth defining some primitives that will be used frequently when interacting with both the Ethereum blockchain in general and the Melon Protocol in particular.

#### Environment

This class contextualizes where you're doing the work. Its constructor function requires the network on which you're working \(this will be a testnet of some sort or the Ethereum mainnet if you're cooking with gas\) and a deployment `config` file that specifies the addresses of the current Melon Protocol contracts, the ERC-20 tokens that are tradeable on Melon, and the exchanges upon which they're traded. A copy of one of these files can be found in the `/examples` directory in [this repo](https://github.com/melonproject/melonjs/tree/master/examples).

```javascript
const { Eth } = require('web3-eth');
const { HttpProvider } = require('web3-providers');
const { DeployedEnvironment } = require('@melonproject/melonjs');

// Instantiate the environment where you'll create your fund
const eth = new Eth(new HttpProvider('https://mainnet.infura.io/v3/9136e09ace01493b86fed528cb6a87a5', {
  confirmTransactionBlocks: 1,
}}));
const deployment = fs.readFileSync('./deployment.json');
const environment = new DeployedEnvironment(eth, deployment);
```

#### Contract

The `contract` class is MelonJS' base unit for all interactions with the blockchain. Though every Melon Protocol contract has various layers of abstraction, `contract` gives each some base functionality:

* creating a `deployment` of the contract
* querying the blockchain
* creating a `transaction`

`Transaction` is a class all its own. From start to finish, executing a transaction has four steps.

**Instantiation** - A contract must create a new transaction of a given type.

**Validation** - `transaction.validate()` is optional, though calling it provides named error messages which can be helpful for debugging or to show on any sort of front end application.

**Preparation** - `transaction.prepare()` is an asynchronous function that returns an object denoting the fees a transaction is projected to require shaped like this:

```text
{
  gas: number,
  gasPrice?: number,
  amgu?: number,
  incentive?: number,
  value?: number,
  from?: string,
}
```

If no arguments are passed to `.prepare()`, it will check the [ethGasStation](https://ethgasstation.info/) for estimated network gas prices, and the Melon Protocol for any applicable AMGU or incentive fees. However, we recommend passing

```text
{ gasPrice: number }
```

to `.prepare()` with a number you believe will guarantee transaction success.

**Completion** - Pass the resolution of `.prepare()` to `transaction.send()`, which returns a Web3 `Promievent`. Check [their docs](https://web3js.readthedocs.io/en/v1.2.6/callbacks-promises-events.html) for details, but these are promises with multiple stages of asynchronicity, each of which can be listened for to trigger UI interactions. 

These steps can be chained together into something like this:

```javascript
const transaction = SomeContract.create(environment, args)

// the TransactionReceipt type is imported from Web3
const receipt = await new Promise<TransactionReceipt>( (resolve, reject) => {
  transaction.validate()
    .then(() => transaction.prepare({ gasPrice: GAS_PRICE })) // of your choosing, or omit this
    .then((options) => {
      const tx = transaction.send(options);

      tx.once('transactionHash', hash => console.log(`Pending: ${hash}`));
      tx.once('receipt', receipt => resolve(receipt));
      tx.once('error', error => reject(error));
    })
    .catch(error) => reject(error));
    });

console.log(`Success: ${receipt.transactionHash}`);
```

The final result of the PromiEvent is a receipt that has some useful information. 

```bash
{
  "status": true,
  "transactionHash": "0x9fc76417374aa880d4449a1f7f31ec597f00b1f6f3dd2d66f4c9c6c445836d8b",
  "transactionIndex": 0,
  "blockHash": "0xef95f2f1ed3ca60b048b4bf67cde2195961e0bba6f70bcbea9a2c4e133e34b46",
  "blockNumber": 3,
  "contractAddress": "0x11f4d0A3c12e86B4b5F39B213F7E19D048276DAe",
  "cumulativeGasUsed": 314159,
  "gasUsed": 30234,
  "logs": [{
         // logs as returned by getPastLogs, etc.
     }
```

### Setting Up a Melon Fund

Given an `environment` and a config file, you can spin up your own Melon fund.

```javascript
const BigNumber = require('bignumber.js');
// sender is the current user's wallet address
async function beginSetup(environment, config, sender, gasPrice) {
  // instantiate the current version (per your environment) of the Melon protocol
  const version = new Version(environment, environment.deployment.melon.addr.Version);

  // define the variables for your fund. See the fundConfig file in the example directory in this repo for guidance here.
  const denominationAssetAddress = environment.deployment.tokens.addr[config.QuoteToken];
  const defaultAssets = config.AllowedTokens.map(t => environment.deployment.tokens.addr[t]);
  const managementFeeRate = new BigNumber(config.ManagementFee).times('1000000000000000000');
  const performanceFeeRate = new BigNumber(config.PerformanceFee).times('1000000000000000000');

  let exchanges = [];
  let adapters = [];

  // do this however you like, but the goal is to have two arrays of addresses, one for your exchanges, and the other for the corresponding adapter that the protocol uses to interact with them.

  if (config.Exchanges.includes('OasisDex')) {
    exchanges.push(environment.deployment.oasis.addr.OasisDexExchange);
    adapters.push(environment.deployment.melon.addr.OasisDexAdapter);
  }
  // ... etc for all possible exchanges

  // pass your newly-defined variables to the `beginSetup` function to create the transaction and you're on your way.

  const transaction = version.beginSetup(sender, {
    name: config.FundName,
    fees: [environment.deployment.melon.addr.ManagementFee, environment.deployment.melon.addr.PerformanceFee],
    feeRates: [managementFeeRate, performanceFeeRate],
    feePeriods: [new BigNumber(0), new BigNumber(90 * 60 * 60 * 24)],
    exchanges: exchanges,
    adapters: adapters,
    denominationAsset: denominationAssetAddress,
    defaultAssets: defaultAssets,
  });


  const receipt = ... // pass the transaction through the flow described above

  return receipt;
}
```

At this point, you'll need to call the setupSpokeContract methods individually on `version` in this order:

* createAccounting
* createFeeManager
* createParticipation
* createPolicyManager
* createShares
* createTrading

```javascript
const accountingTx = version.createAccounting(sender);
const accountingReceipt = ... // pass the transaction through the flow above to generate the receipt 

console.log(accountingReceipt);
```

...and so on. 

Once the spokes are all instantiated, call `version.completeSetup(sender)` to tie everything together. 

### The Participation Contract

Investing in a Melon is a three step process. The first two steps are handled by the party requesting the investment. The third step is handled by either that party, the fund manager, or an interested third party. More discussion of the game theory dynamics and potential attack vectors of the investment process can be found [here](https://medium.com/melonprotocol/protecting-participants-ee55a752287).

| Step | Contract | User |
| :--- | :--- | :--- |
| approve | ERC20 | investor |
| request | `Participation` | investor |
| execute | `Particiaption` | various |

The first step is to approve the fund's participation contract to transfer of a specific amount tokens from the investor's address.

```javascript
const { StandardToken } = require('@melonproject/melonjs')
const tokenAddress = string // address here is that of the ERC-20 that the user is trying to invest in the fund.
const contract = new StandardToken(environment, tokenAddress)
const accountAddress = string // the address of the user trying to make the investment
const participationAddress = string // the address of your fund's participation contract
const approvalAmount = bigNumber // a number equal to the amount of the ERC-20 that the user is trying to invest, with the correct number of decimals for that given token. On our front end, we use a helper function called toTokenBaseUnit to generate these bigNumbers
const transaction = contract.approve(accountAddress, participationAddress, approvalAmount)

// At this point, we can pass the transaction through the flow we described above.
const receipt = await new Promise<TransactionReceipt>( (resolve, reject) => {
  transaction.validate()
    .then(() => tx.prepare({ gasPrice: GAS_PRICE })) // of your choosing, or omit this
    .then((options) => {
      const tx = tx.send(options);

      tx.once('transactionHash', hash => console.log(`Pending: ${hash}`));
      tx.once('receipt', receipt => resolve(receipt));
      tx.once('error', error => reject(error));
    })
    .catch(error) => reject(error));
    });

console.log(`Success: ${receipt.transactionHash}`);
```

Next, we have to request the shares from the `Participation` contract.

```javascript
const { Participation } = require('@melonproject/melonjs');

const participationAddress = string; // the address of the fund's participation contract
const tokenAddress = string; // the address of the token with which the user is asking to invest
const userAddress = string; // the address of the user making the investment request

const contract = new Participation(environment, participationAddress);
const investmentAmount = BigNumber; // the amount of ERC-20 token the user is offering to invest, with the appropriate number of decimals for that token
const sharesAmount = BigNumber; // the computed number of shares the user is requesting given the amount of the investment token, with the correct number of decimals (18)
const transaction = contract.requestInvestment(userAddress, sharesAmount, investmentAmount, tokenAddress);

// At this point, we can pass the transaction through the flow we described above.
const receipt = await new Promise<TransactionReceipt>( (resolve, reject) => {
  transaction.validate()
    .then(() => tx.prepare({ gasPrice: GAS_PRICE })) // of your choosing, or omit this
    .then((options) => {
      const tx = tx.send(options);

      tx.once('transactionHash', hash => console.log(`Pending: ${hash}`));
      tx.once('receipt', receipt => resolve(receipt));
      tx.once('error', error => reject(error));
    })
    .catch(error) => reject(error));
    });

console.log(`Success: ${receipt.transactionHash}`);
```

Finally, we execute the investment request. With the exception of the first investment in a fund, this will require waiting until after the next price feed update, and the function can be called by anybody \(see the blog post linked above\).

```javascript
const { Participation } = require('@melonproject/melonjs');
const participationAddress = string; // the address of the fund's participation contract
const userAddress = string; // the address of the user making the investment request
const executorAddress = string; // the address of the account calling the function

const contract = new Participation(environment, participationAddress);
const transaction = contract.executeRequestFor(executorAddress, userAddress);

const receipt = ...etc // as above
```

Redeeming one's shares from a Melon fund is fairly simple and requires only one step.

```javascript
const { Participation } = require('@melonproject/melonjs');

const participationAddress = string; // the address of the fund's participation contract
const userAddress = string; // the address of the user making the redemption request

const contract = new Participation(environment, participationAddress)

// the redemption transaction will either be .redeem(), hwich redeems all shares, or .redeemQuantity, which redeems a partial balance of the user's shares. Note that the shareQuantity must be a BigNumber with an appropriate number of decimal places.
const transaction = contract.redeem(userAddress) || contract.redeemQuantity(userAddress, shareQuantity)

const receipt = etc ... // the usual transaction confirmation flow detailed in the first section of this usage guide.
```

We can also use the `Participation` contract to check a fund's current investors.

```javascript
const { Participation } = require('@melonproject/melonjs');
const participationAddress = string; // the address of the fund's participation contract
const contract = new Participation(environment, participationAddress)
const investors = await contract.getHistoricalInvestors()
// investors will be an array of addresses of investors in the fund
```

### The Trading Contract

The Melon Protocol is directly integrated with the smart contracts of various trading venues. MelonJS provides an avenue to interact with those exchanges to query prices and trade tokens. These two concerns are handled by separate classes.

```javascript
const { KyberNetworkProxy } = require('@melonproject/melonjs');
const makerToken = string; // address of the token you own
const takerToken = string; // address of the token you want to own
const makerQty = BigNumber; // amount of the makerToken that you'd like to swap for the destToken with the appropriate number of decimal places
const priceChecking = new KyberNetworkProxy(environment, environment.deployment.kyber.addr.KyberNetworkProxy);
const expectedRate = await priceChecking.getExpectedRate(makerToken, takerToken, makerQty);
```

`expectedRate` is an object shaped like so:

```text
{
  expectedRate: new BigNumber(expectedRate),
  slippageRate: new BigNumber(slippageRate),
}
```

Once you've got that, you can move on to the fun part.

```javascript
const { Trading, KyberTradingAdapter } = require('@melonproject/melonjs');
const tradingAddress = string; // address of the fund's trading contract
const trading = new Trading(environment, tradingAddress); // tradingContract is the string address of the trading contract belonging to the fund in question. This will define a Trading class specific to the fund.

const orderArgs =  {
  makerAsset: Address; // address of the makerToken
  takerAsset: Address; // address of the takerToken
  makerQuantity: BigNumber; // amount of the makerToken with the appropriate number of decimal places ***Note that if you're calling these functions sequentially, makerQuantity shoudld be equal to the user -specified takerQuantity multiplied by the expectedRate that was fetched from the KyberNetworkProxy
  takerQuantity: BigNumber; // amount of the takerToken with the appropriate number of decimal places
}

const adapter = await KyberTradingAdapter.create(environment, exchange, trading);

const transaction = adapter.takeOrder(from, orderArgs) // The from argument is the wallet address that's initiating the transaction, and kyberTakeOrderArgs an object in the shape noted above. takeOrder() returns a Transaction, which you can pass through the flow we described in the Transaction primitive section above.

const receipt = etc ... // the usual transaction confirmation flow detailed in the first section of this usage guide.
```

### The Accounting and FeeManager Contracts

The Accounting contract provides several methods to check the performance of a fund. It also works in tandem with FeeManager to manage and distribute management and performance fees. 

The fund's management fee is redeemable at any time, via the FeeManager contract.

```javascript
const { FeeManager } = require('@melonproject/melonjs')

const feeManagerAddress = string; // address of the fund's trading contract
const fundAddress = string; // address of the fund manager

const feeManager = new FeeManager(environment, feeManagerAddress);

const transaction = feeManager.rewardManagementFees(fundAddress);

const receipt = etc ... // the usual transaction confirmation flow detailed in the first section of this usage guide.
```

To reward both the accrued management and performance fees, call the Accounting contract.

```javascript
const { Accounting } = require('@melonproject/melonjs')

const accountingAddress = string; // address of the fund's Accounting contract
const fundAddress = string; // address of the fund 

const accounting = new Account(environment, accountingAddress);

const transaction = accounting.triggerRewardAllFees(fundAddress)

const receipt = etc ... // the usual transaction confirmation flow detailed in the first section of this usage guide
```

You can also use the Accounting contract to query the fund's holdings.

```javascript
const fundHoldings = accounting.getFundHoldings()
// fundHoldings will be an array of objects shaped like this:
// [{address: string, amount: BigNumber}...]
```

You'll have to do the work to put an asset's name to the address.

The Accounting contract will also do some handy calculation work for you, providing a description of the Fund across various metrics.

```javascript
const fundStats = accounting.getCalculationResults()

// fundStats will be an object shaped like this:

{     
  sharePrice: BigNumber,
  gav: BigNumber
  nav: BigNumber
  feesInDenominationAsset: BigNumber
  feesInShares: BigNumber
  gavPerShareNetManagementFee: BigNumber
}

```

### The Policy Contracts

Policies are rules to which the fund manager must adhere. They come in a few different flavors. Each specific policy has its own contract \(`AssetWhitelist`, `MaxConcentration`, etc..\). The arguments passed to these contracts' deployment methods vary based on what the policy is enforcing and are fairly intuitive. For instance, `AssetWhiteList`'s deployment method accepts an array of addresses, `MaxConcentration` accepts a BigNumber, and so on. A full discussion of policies and their enforcement dynamics can be found [here](https://docs.melonport.com/chapters/fund.html#policies).

**One thing to note: to deploy specific policy contracts, you must pass the corresponding byte code to the that contract's deployment method.** Luckily, MelonJS provides that for you as well. 

Let's create a `MaxPositions` policy, whose purpose is fairly self-explanatory. 

```javascript
const { MaxPositions } = require('@melonproject/melonjs');
const { MaxPositionsBytecode } = require('@melonproject/melonjs/abis/MaxPositions.bin');

const fundAddress = string // the address of the fund 
const manager = new PolicyManager(environment, policyManagerAddress)

const numberOfPositions = new BigNumber(5);
const transaction = MaxPositions.deploy(environment, MaxPositionsByteCode, fundAddress, numberOfPositions);

transaction.validate()
  .then(() => transaction.prepare({ gasPrice: GAS_PRICE })) // of your choosing, or omit this
  .then((options) => {
    const tx = transaction.send(options);

    tx.once('transactionHash', hash => console.log(`Pending: ${hash}`));
    tx.once('receipt', receipt => resolve(receipt));
    tx.once('error', error => reject(error));
  })
  .catch(error) => reject(error));
  });
```

Once you've deployed the Policy contract, you need to register it with your fund using the PolicyManager contract that you created when you set up the fund.

```javascript
const {PolicyManager } = require('@melonproject/melonjs');

const maxPositionsAddress = receipt.contractAddress // the address of the contract you just deployed
const maxPositionsSignature = string // the signature of the max positions policy
const policyManagerAddress = string // the address of the fund's policy manager contract
const fundAddress = string // the address of the fund


const manager = new PolicyManager(environment, policyManagerAddress)
const transaction = manager.registerPolicy(fundAddress, maxPositionsSignature, maxPositionsAddress
```

## Testing

The tests contained in this repository use an in-memory ganache test chain.

In order to execute the tests, simply run:

```bash
yarn test
```

## Contributing

Third party contributions to this project are welcome and encouraged. If you want to contribute, please open an issue before submitting a pull requests so we can discuss the proposed changes and/or additions.

Please note that all repositories hosted under this organization follow our [Code of Conduct](https://github.com/melonproject/melonjs/blob/master/CODE_OF_CONDUCT.md), make sure to review and follow it.

