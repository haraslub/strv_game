# from scripts.helpers import get_account, deploy_proxy, upgrade, get_contract
# from brownie import MediavalSTRVGame, MediavalSTRVGameV2, Contract, exceptions, config, network
# from web3 import Web3
# import pytest


# def test_proxy_upgrades(owner):
        
#     nft_game = MediavalSTRVGame.deploy(
#         get_contract("vrf_coordinator").address,
#         get_contract("link_token").address,
#         config["networks"][network.show_active()]["keyhash"],
#         config["networks"][network.show_active()]["fee"],
#         {"from": owner},
#         publish_source=config["networks"][network.show_active()].get("publish", False),
#         )
#     proxy_admin, proxy_nft_game, proxy = deploy_proxy(owner, nft_game, "MediavalSTRVGame")
#     # set proxy address as admin
#     DEFAULT_ADMIN_ROLE = nft_game.DEFAULT_ADMIN_ROLE()
#     # ACT 1 - deploy nft game V2 and use proxy game V2 without upgrade
#     #   test will pass if VirtualMachineError
#     nft_game_V2 = MediavalSTRVGameV2.deploy(
#         get_contract("vrf_coordinator").address,
#         get_contract("link_token").address,
#         config["networks"][network.show_active()]["keyhash"],
#         config["networks"][network.show_active()]["fee"],
#         {"from": owner},
#         publish_source=config["networks"][network.show_active()].get("publish", False),
#         )
#     proxy_nft_game_V2 =Contract.from_abi(
#         "MediavalSTRVGameV2", proxy.address, MediavalSTRVGameV2.abi,
#     )
#     # ASSERT 1
#     minting_threshold = proxy_nft_game_V2.mintingThreshold()
#     gear_to_burn = proxy_nft_game_V2.gearToBurn()
#     gear_to_mint = proxy_nft_game_V2.gearToMint()

#     with pytest.raises(exceptions.VirtualMachineError):
#         proxy_nft_game_V2.setBurnGearParameters(50, 0, 1, {"from": owner})
    
#     # ACT 2 - upgrade proxy, test its functions
#     upgrade_nft_game = upgrade(
#         owner,
#         proxy,
#         nft_game_V2.address,
#         proxy_admin_contract = proxy_admin,
#         initializer=None,
#     )
#     upgrade_nft_game.wait(1)

#     proxy_nft_game_V2 = Contract.from_abi(
#         "MediavalSTRVGameV2", proxy.address, MediavalSTRVGameV2.abi,
#     )
#     nft_game.grantRole(DEFAULT_ADMIN_ROLE, proxy_nft_game_V2.address, {"from": owner})
#     proxy_nft_game_V2.setBurnGearParameters(50, 0, 1, {"from": owner})

#     minting_threshold_new = proxy_nft_game_V2.mintingThreshold()
#     gear_to_burn_new = proxy_nft_game_V2.gearToBurn()
#     gear_to_mint_new = proxy_nft_game_V2.gearToMint()

#     # ASSERT2
#     assert minting_threshold_new != minting_threshold
#     assert gear_to_burn_new != gear_to_burn
#     assert gear_to_mint_new != gear_to_mint

