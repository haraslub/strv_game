from web3 import Web3
from brownie import network
from scripts.helpers import get_contract, LOCAL_BLOCKCHAIN_ENVIRONMENTS
import pytest

AMOUNT_TO_MINT = 100
RATE = 0.1


def test_set_new_burn_gear_parameters_and_test_burning_aftwerwards(owner, nft_game, user):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for LOCAL testing")
    # Arrange
    _new_threshold = 50
    _new_gear_to_burn = 0 # armor
    _new_gear_to_mint = 1 # shield
    
    # Act
    # - setting new parameters
    nft_game.setBurnGearParameters(_new_threshold, _new_gear_to_burn, _new_gear_to_mint, {"from": owner})
    # - minting tokens
    nft_game.publicMint(0, AMOUNT_TO_MINT, {"from": user, "value": Web3.toWei(AMOUNT_TO_MINT*RATE, "ether")})
    nft_game.publicMint(1, AMOUNT_TO_MINT, {"from": user, "value": Web3.toWei(AMOUNT_TO_MINT*RATE, "ether")})
    nft_game.publicMint(2, AMOUNT_TO_MINT, {"from": user, "value": Web3.toWei(AMOUNT_TO_MINT*RATE, "ether")})
      
    STATIC_RNGS = [0, 4610, 7890, 15600]
    
    for STATIC_RNG in STATIC_RNGS:
        print("Randomness: {}".format(STATIC_RNG))
        print("Random number: {}".format((STATIC_RNG % 100) + 1))
        # get balances before burning
        user_balance_armor_before = nft_game.balanceOf(user, _new_gear_to_burn)
        user_balance_shield_before = nft_game.balanceOf(user, _new_gear_to_mint)
        # burn
        tx = nft_game.burnToGainGear(_new_gear_to_burn, 1, {"from": user})
        request_id = tx.events["RequestedRandomness"]["requestId"]
        # pretending being a chainlink node -> mock
        get_contract("vrf_coordinator").callBackWithRandomness(request_id, STATIC_RNG, nft_game.address, {"from": owner})
        user_balance_armor_after = nft_game.balanceOf(user, _new_gear_to_burn)
        user_balance_shield_after = nft_game.balanceOf(user, _new_gear_to_mint)

        # Assert
        minted_amount = 0
        if (((STATIC_RNG % 100) + 1) < _new_threshold) & (STATIC_RNG != 0):
            minted_amount = 1

        assert user_balance_armor_before == (user_balance_armor_after + 1)
        assert user_balance_shield_before == (user_balance_shield_after - minted_amount)

