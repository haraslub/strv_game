from scripts.helpers import get_account, get_contract, fund_with_link
from brownie import config, network, MediavalSTRVGameV2
from web3 import Web3
import pytest

MINTER_ROLE = Web3.keccak(text="MINTER_ROLE")
PAUSER_ROLE = Web3.keccak(text="PAUSER_ROLE")


@pytest.fixture()
def owner():
    return get_account()

@pytest.fixture()
def minter():
    return get_account(1)

@pytest.fixture()
def pauser():
    return get_account(2)

@pytest.fixture()
def user():
    return get_account(3)


@pytest.mark.require_network("development")
@pytest.fixture(autouse=True)
def nft_game(owner, minter, pauser):
    print("Deploying NFT game..")
    nft_game = MediavalSTRVGameV2.deploy(
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["keyhash"],
        config["networks"][network.show_active()]["fee"],
        {"from": owner},
        )
    # set roles
    nft_game.grantRole(MINTER_ROLE, minter, {"from": owner})
    nft_game.grantRole(PAUSER_ROLE, pauser, {"from": owner})
    tx_funding = fund_with_link(nft_game.address, owner)
    tx_funding.wait(1)
    return nft_game


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass
