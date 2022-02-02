# STRV SMART CONTRACT TEST PROJECT

## Prerequisities

> **Language:** Solidity

> **Development and testing environment:** Brownie

> **Blockchains:** Local ganache-cli, Rinkeby testnet

> **Development time:** ~ 30 hours

## Comments

The final contract is called **MediavalSTRVGameV2** and is deployed on rinkeby testnet (see the contract address in brownie-config.yaml at `[networks][rinkeby][deployed_nft_game]`).

Testing was performed for local blockchain and rinkeby. All testing scripts for local environment can be seen at **tests** folder, for rinkeby in folder scripts in **deploy_game.py** file.

There are four main scripts:

1. **create_metadata.py** used for creating and uploading metadata to pinata cloud.
2. **deploy_game.py** used for test and deployment on rinkeby testnet.
3. **helpers.py** used as storage of helping function.

### Minting Equipment

In order to allow public minting, function `publicMint` is defined. After reaching max public minting supply (variable `mintedPublicly`), the function stops working. If public minting should be reopened, it can be done via changing given parameters by `setParametersOfPublicMint`. Another possible way to mint more equipment can be done by `mint` function, which can be used only by user with `MINTER_ROLE` assigned. Assignment of any role can be done only by admin (role = `DEFAULT_ADMIN_ROLE`). Roles are defined by `BurningContract.sol` which is modified `ERC1155PresetMinterPauser` contract.

### Burn Equipment

Burning of equipment is not restricted for users (can be changed by creating a role for it if needed). Each user can burn a shield in order to get sword with 80% chance by using function `burnToGainGear`. The 80% chance to win is calculated by using Chainlink's VRF Coordinator (see functions `sword_lottery` and `fulfillRandomness`). Parameters of the function can be changed via `setBurnGearParameters` function.

## Uncertainties, deficiencies

### Security, Best Practices

Unfortunately, I cannot declare that all smart contracts written are fully secure and written in accordance with the best practices. I am aware of my shortcomings and intend to work on them.

### Upgradability

My intentions were to create a proxy contract using OpenZeppelin as it is a better way for upgradibility of Smart Contracts, thus created two versions of game. Unfortunately I failed to deliver it, I got stucked during testing. Anyway, you can see my unfinished work in `tests/local/test_proxy.py`.

### Testing

Testing is another part which I need/want to improve a lot. For instance, it would be more robust if parametrizing tests were applied (studying in progress). Also, mainnet-fork environment could be used for testing and effective testing for rinkeby testnet is missing. All aforementioned I would like to use in future.
