from scripts.helpers import get_account, get_contract, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from brownie import exceptions, reverts, network
from web3 import Web3
import pytest

RATE = 0.1
MINTER_ROLE = Web3.keccak(text="MINTER_ROLE")
PAUSER_ROLE = Web3.keccak(text="PAUSER_ROLE")


def test_mint_with_diff_roles(nft_game, owner):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for LOCAL testing")
    # Arrange
    admin = owner
    minter = get_account(1)
    pauser = get_account(2)
    user = get_account(3)
    AMOUNT = 10
    # Act
    nft_game.grantRole(MINTER_ROLE, minter, {"from": admin})
    nft_game.grantRole(MINTER_ROLE, admin, {"from": admin})
    nft_game.grantRole(PAUSER_ROLE, pauser, {"from": admin})
    nft_game.mint(user, 0, AMOUNT, {"from": admin})
    nft_game.mint(user, 0, AMOUNT, {"from": minter})
    user_balance_0 = nft_game.balanceOf(user, 0)
    # Assert
    assert user_balance_0 == (2 * AMOUNT)
    with reverts("BurningContract: must have minter role to mint"):
        nft_game.mint(user, 0, AMOUNT, {"from": pauser})
    with reverts("BurningContract: must have minter role to mint"):
        nft_game.mint(user, 0, AMOUNT, {"from": user})


def test_mint_roles_and_balances(nft_game, owner):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for LOCAL testing")
    # Arrange
    user = get_account(4)
    # Act
    nft_game.grantRole(MINTER_ROLE, owner, {"from": owner})
    nft_game.mint(user, 0, 10, {"from": owner})
    nft_game.mint(user, 1, 10, {"from": owner})
    nft_game.mint(user, 2, 10, {"from": owner})
    # Assert - general
    assert owner != user
    # Assert - successful mint by owner
    user_balance_id_0 = nft_game.balanceOf(user, 0)
    user_balance_id_1 = nft_game.balanceOf(user, 1)
    user_balance_id_2 = nft_game.balanceOf(user, 2)
    assert user_balance_id_0 == user_balance_id_1 == user_balance_id_2 == 10
    # Assert - unsuccessful mint by user
    with reverts("BurningContract: must have minter role to mint"):
        nft_game.mint(user, 0, 100, {"from": user})
    # Assert - unsuccessful mint of wrong id
    with reverts("Gear does not exists!"):
        nft_game.mint(user, 4, 100, {"from": owner})


def test_public_mint_and_withdrawal(nft_game, owner):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for LOCAL testing")
    # Arrange
    user = get_account(5)
    user_2 = get_account(6)
    AMOUNT_TO_MINT = 1000
    # Act
    # minting
    nft_game.publicMint(1, AMOUNT_TO_MINT, {"from": user, "value": Web3.toWei((AMOUNT_TO_MINT * RATE), "ether")})
    user_balance_id_1 = nft_game.balanceOf(user, 1)
    # withdrawal
    owner_balance_before = owner.balance()
    nft_game.withdraw({"from": owner})
    owner_balance_after = owner.balance()
    # Assert - successful mint of all NFTs
    assert user_balance_id_1 == AMOUNT_TO_MINT
    # Assert - successful withdrawal
    assert owner_balance_after == (owner_balance_before + Web3.toWei((AMOUNT_TO_MINT * RATE), "ether"))
    # Assert - unsuccessful mint once the capacity has been reached
    with pytest.raises(exceptions.VirtualMachineError):
        nft_game.publicMint(1, 1, {"from": user_2, "value": Web3.toWei(RATE * 1, "ether")})
    # Assert - the same as previous
    with reverts("Not enough supply left in public mint"):
        nft_game.publicMint(1, 1, {"from": user_2, "value": Web3.toWei(RATE * 1, "ether")})


def test_try_mint_without_enough_eth(nft_game):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for LOCAL testing")
    # Arrange
    user = get_account(7)
    AMOUNT_TO_MINT = 10
    # Act
    NEW_RATE = RATE * 0.9
    # Assert
    with reverts("Not enough ETH for transaction"):
        nft_game.publicMint(1, AMOUNT_TO_MINT, {"from": user, "value": Web3.toWei((AMOUNT_TO_MINT * NEW_RATE), "ether")})


def test_burn_function(nft_game, owner):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for LOCAL testing")
    # Arrange
    user = get_account(8)
    # mint nfts
    AMOUNT = 100
    nft_game.publicMint(0, AMOUNT, {"from": user, "value": Web3.toWei(AMOUNT*RATE, "ether")})
    nft_game.publicMint(1, AMOUNT, {"from": user, "value": Web3.toWei(AMOUNT*RATE, "ether")})
    nft_game.publicMint(2, AMOUNT, {"from": user, "value": Web3.toWei(AMOUNT*RATE, "ether")})
    
    # Act 1 - SUCCESSFUL BURN 
    user_balance_shield_before = nft_game.balanceOf(user, 1)
    user_balance_sword_before = nft_game.balanceOf(user, 2)
    print(user_balance_shield_before)
    tx = nft_game.burnToGainGear(1, 1, {"from": user})
    request_id = tx.events["RequestedRandomness"]["requestId"]
    # pretending being a chainlink node -> mock
    STATIC_RNG = 77777
    get_contract("vrf_coordinator").callBackWithRandomness(request_id, STATIC_RNG, nft_game.address, {"from": owner})
    # generatedRandomNumber should be 78, thus new sword should be minted
    user_balance_shield_after = nft_game.balanceOf(user, 1)
    user_balance_sword_after = nft_game.balanceOf(user, 2)
    # Assert 1
    assert user_balance_shield_after == (user_balance_shield_before - 1)
    assert user_balance_sword_after == (user_balance_sword_before + 1)

    # Act 2 - UNSUCCESSFUL BURN 
    user_balance_shield_before = nft_game.balanceOf(user, 1)
    user_balance_sword_before = nft_game.balanceOf(user, 2)
    tx2 = nft_game.burnToGainGear(1, 1, {"from": user})
    request_id = tx2.events["RequestedRandomness"]["requestId"]
    # pretending being a chainlink node -> mock
    STATIC_RNG = 977777
    get_contract("vrf_coordinator").callBackWithRandomness(request_id, STATIC_RNG, nft_game.address, {"from": owner})
    # generatedRandomNumber should be 98, thus new sword should NOT be minted
    user_balance_shield_after = nft_game.balanceOf(user, 1)
    user_balance_sword_after = nft_game.balanceOf(user, 2)
    # Assert 2
    assert user_balance_shield_after == (user_balance_shield_before - 1)
    assert user_balance_sword_after == (user_balance_sword_before + 1)


def test_to_break_burn_function(nft_game):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for LOCAL testing")
    # Arrange
    user = get_account(9)
    AMOUNT = 1
    # mint nfts
    nft_game.publicMint(0, AMOUNT, {"from": user, "value": Web3.toWei(AMOUNT*RATE, "ether")})
    nft_game.publicMint(1, AMOUNT, {"from": user, "value": Web3.toWei(AMOUNT*RATE, "ether")})
    nft_game.publicMint(2, AMOUNT, {"from": user, "value": Web3.toWei(AMOUNT*RATE, "ether")})
    # Act
    nft_game.burnToGainGear(1, 1, {"from": user})
    # Assert - try to burnToGainGear before chainlink node/vrf coordinators sends the randomness
    with reverts("There is nothing to burn"):
        nft_game.burnToGainGear(1, 1, {"from": user})