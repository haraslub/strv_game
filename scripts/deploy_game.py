from scripts.helpers import LOCAL_BLOCKCHAIN_ENVIRONMENTS, fund_with_link, get_account, get_contract
from brownie import (
    MediavalSTRVGameV2,
    network, config, Contract, accounts,
)
from web3 import Web3
import time

RATE = 0.1
MINTER_ROLE = Web3.keccak(text="MINTER_ROLE")
PAUSER_ROLE = Web3.keccak(text="PAUSER_ROLE")

dict_gear_to_id = {
    "ARMOR": 0,
    "SHIELD": 1,
    "SWORD": 2,
}


def deploy_nft_game(owner):
    nft_game_contract = MediavalSTRVGameV2.deploy(
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["keyhash"],
        config["networks"][network.show_active()]["fee"],
        {"from": owner},
        publish_source=config["networks"][network.show_active()].get("verify", False),
        )
    print("NFT Mediaval STRV Game deployed.")
    # funding nft game contract with some LINK tokens for VRF
    tx = fund_with_link(nft_game_contract.address, amount=Web3.toWei(2, "ether"))
    tx.wait(1)
    return nft_game_contract


def main():
    owner = admin = get_account()
    nft_game_address = config["networks"][network.show_active()]["deployed_nft_game"]

    # if local deployment, a user needs to be defined, else get user account from .env
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        user = get_account(5)
    else:
        user = accounts.add(config["wallets"]["from_key_user"])

    # if contract already deployed on rinkeby (needs to be defined in config in networks/rinkeby/deployed_nft_game), 
    # get the contract from abi, else deploy it 
    if nft_game_address:
        nft_game = Contract.from_abi(
            MediavalSTRVGameV2._name, nft_game_address, MediavalSTRVGameV2.abi
        ) 
    else:
        nft_game = deploy_nft_game(owner)
        nft_game.grantRole(MINTER_ROLE, admin, {"from": admin})
        nft_game.mint(user, 1, 10, {"from": admin})
    
    print("New balances after using burn to gain gear function...")
    user_balance_0 = nft_game.balanceOf(user, dict_gear_to_id["ARMOR"])
    print("ID {}: {}".format(dict_gear_to_id["ARMOR"], user_balance_0))
    user_balance_1 = nft_game.balanceOf(user, dict_gear_to_id["SHIELD"])
    print("ID {}: {}".format(dict_gear_to_id["SHIELD"], user_balance_1))
    user_balance_2 = nft_game.balanceOf(user, dict_gear_to_id["SWORD"])
    print("ID {}: {}".format(dict_gear_to_id["SWORD"], user_balance_2))

    print("\nFunding contract with LINK again..")
    fund_with_link(nft_game.address, amount=Web3.toWei(2, "ether"))

    print("\nSetting new parameters for public minting..")
    NEW_RATE = Web3.toWei("0.01", "ether")
    AMOUNT_FOR_PUBLIC_MINT = 3
    NEW_MAX_AMOUNT_FOR_PUBLIC_MINT = nft_game.mintedPublicly() + AMOUNT_FOR_PUBLIC_MINT

    nft_game.setParametersOfPublicMint(NEW_MAX_AMOUNT_FOR_PUBLIC_MINT, [NEW_RATE, NEW_RATE, NEW_RATE], {"from": admin})

    print("Setting new parameters for burn to gain gear function..")
    NEW_ITEM_TO_BURN = dict_gear_to_id["SHIELD"]
    ITEM_TO_GAIN = dict_gear_to_id["ARMOR"]
    NEW_THRESHOLD = 50

    nft_game.setBurnGearParameters(NEW_THRESHOLD, NEW_ITEM_TO_BURN, ITEM_TO_GAIN, {"from": admin})

    print("Testing public minting..")
    nft_game.publicMint(NEW_ITEM_TO_BURN, AMOUNT_FOR_PUBLIC_MINT, {"from": user, "value": NEW_RATE*AMOUNT_FOR_PUBLIC_MINT})
    max_for_public_mint = nft_game.maxAvailableForPublicMint()
    print("Max for public mint should be {}: {}".format(
        NEW_MAX_AMOUNT_FOR_PUBLIC_MINT, max_for_public_mint == NEW_MAX_AMOUNT_FOR_PUBLIC_MINT
        ))

    print("\nTesting burn to gain gear function, it will take while...")
    WAIT_FOR_LINK_RESPONSE = 300
    AMOUNT_TO_BURN = nft_game.balanceOf(user, NEW_ITEM_TO_BURN)
    nft_game.burnToGainGear(NEW_ITEM_TO_BURN, AMOUNT_TO_BURN, {"from": user})
    print("\nWaiting for Chainlink node response (set to: {} secs)".format(WAIT_FOR_LINK_RESPONSE))
    time.sleep(WAIT_FOR_LINK_RESPONSE)

    print("\nNew balances after using burn to gain gear function...")
    user_balance_0 = nft_game.balanceOf(user, dict_gear_to_id["ARMOR"])
    print("ID {}: {}".format(dict_gear_to_id["ARMOR"], user_balance_0))
    user_balance_1 = nft_game.balanceOf(user, dict_gear_to_id["SHIELD"])
    print("ID {}: {}".format(dict_gear_to_id["SHIELD"], user_balance_1))
    user_balance_2 = nft_game.balanceOf(user, dict_gear_to_id["SWORD"])
    print("ID {}: {}".format(dict_gear_to_id["SWORD"], user_balance_2))

    print("\nReturning public minting parameters back")
    AMOUNT_TO_SET = 1000
    RATE_PUBLIC_MINT = Web3.toWei("0.1", "ether")
    nft_game.setParametersOfPublicMint(
        AMOUNT_TO_SET, [RATE_PUBLIC_MINT, RATE_PUBLIC_MINT, RATE_PUBLIC_MINT], {"from": admin}
        )
    max_for_public_mint = nft_game.maxAvailableForPublicMint()
    print("Max for public mint set to {} was successful: {}".format(AMOUNT_TO_SET, AMOUNT_TO_SET == max_for_public_mint))

    print("\nReturning original parameters to burn to gain fucntion..")
    ITEM_TO_BURN = dict_gear_to_id["SHIELD"]
    ITEM_TO_MINT = dict_gear_to_id["SWORD"]
    ORIGINAL_THRESHOLD = 80

    nft_game.setBurnGearParameters(ORIGINAL_THRESHOLD, ITEM_TO_BURN, ITEM_TO_MINT, {"from": admin})

    print("Testing witdrawal function...")
    balance_before = owner.balance()
    nft_game.withdraw({"from": owner})
    balance_after = owner.balance()
    print("Withdrawal successful: {} (before: {}; after: {};".format(
        balance_before < balance_after, balance_before, balance_after
        ))


