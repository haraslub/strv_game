from web3 import Web3
from brownie import reverts, network
from scripts.helpers import LOCAL_BLOCKCHAIN_ENVIRONMENTS
import pytest


def test_setParametersOfPublicMint(nft_game, owner):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for LOCAL testing")
    # Arrange
    NEW_MAX = 2000
    NEW_RATES = ["0.5 ether", "0.05 ether", "0.25 ether"]
    sum_rates = 0
    for rate in NEW_RATES:
        num, unit = rate.split(" ")
        sum_rates += Web3.toWei(num, unit)
    # Act
    nft_game.setParametersOfPublicMint(NEW_MAX, NEW_RATES, {"from": owner})
    new_max_public_mint = nft_game.maxAvailableForPublicMint()
    tot_rates = 0
    for i in range(0,3):
        tot_rates += nft_game.ratesForPublicMint(i)
    # Assert
    assert new_max_public_mint == NEW_MAX
    assert tot_rates == sum_rates


def test_setBurnGearParameters(owner, nft_game):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for LOCAL testing")
    # Arrange
    _new_threshold = 50
    _new_gear_to_burn = 0
    _new_gear_to_mint = 1
    # Act
    nft_game.setBurnGearParameters(_new_threshold, _new_gear_to_burn, _new_gear_to_mint, {"from": owner})
    new_threshold = nft_game.mintingThreshold()
    new_gear_to_burn = nft_game.gearToBurn()
    new_gear_to_mint = nft_game.gearToMint()
    # Assert
    assert new_threshold == _new_threshold
    assert new_gear_to_burn == _new_gear_to_burn
    assert new_gear_to_mint == _new_gear_to_mint