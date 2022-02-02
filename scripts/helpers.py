from brownie import (
    accounts, network, config, Contract, interface,
    LinkToken, VRFCoordinatorMock, MockV3Aggregator, MockOracle,
    TransparentUpgradeableProxy, ProxyAdmin,
)
from web3 import Web3
import eth_utils


NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["hardhat", "development", "ganache"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS + [
    "mainnet-fork",
]
OPENSEA_URL = "https://testnets.opensea.io/assets/{}/{}"
GEAR_MAPPING = {0: "ARMOR", 1: "SHIELD", 2: "SWORD"}


def get_gear(gear_number: int):
    return GEAR_MAPPING[gear_number]


def get_account(index=None, id=None):
    """
    Get account (private key) to work with

    Args:
        index (int): index of account in a local ganache
        id (string): name of the account from 'brownie accounts list'

    Returns: 
        (string): private key of the account
    """
    if index:
        return accounts[index]  # use account with defined index from local ganache
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]  # use the first ganache account
    if id:
        return accounts.load(id)    # use users's defined account in 'brownie accounts list' (id=name)
    return accounts.add(config["wallets"]["from_key"])  # use account from our environment


contract_to_mock = {"link_token": LinkToken, "vrf_coordinator": VRFCoordinatorMock}


def get_contract(contract_name):
    """
    To use this function, go to the brownie config and add a new entry for
    the contract that you want to be able to 'get'. Then add an entry in the in the variable 'contract_to_mock'.
        This script will then either:
            - Get a address from the config.
            - Or deploy a mock to use for a network that doesn't have it.
        Args:
            contract_name (string): This is the name that is refered to in the
            brownie config and 'contract_to_mock' variable.
        Returns:
            brownie.network.contract.ProjectContract: The most recently deployed
            Contract of the type specificed by the dictonary. This could be either
            a mock or the 'real' contract on a live network.
    """
    contract_type = contract_to_mock[contract_name]

    if network.show_active() in NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # if contract has not been already deployed, deploy mocks, otherwise grab the recent contract deployed
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1] # let's grab the most recent deployed contract
    else:
        try:
            contract_address = config["networks"][network.show_active()][contract_name]
            contract = Contract.from_abi(
                contract_type._name, contract_address, contract_type.abi
            )
        except KeyError:
            print(
                f"{network.show_active()} address not found, perhaps you should add it to the config or deploy mocks?"
            )
            print(
                f"brownie run scripts/deploy_mocks.py --network {network.show_active()}"
            )
    return contract


DECIMALS = 18 
INITIAL_VALUE = Web3.toWei(2000, "ether")


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    """
    Use this script if you want to deploy mocks to a testnet.
    
    Args:
        decimals (int):
        initial_value (int):
    """
    print(f"The active network is {network.show_active()}")
    print("Deploying Mocks...")
    account = get_account()
    # deploy link token contract
    print("Deploying Mock Link Token...")
    link_token = LinkToken.deploy({"from": account})
    # deploy mock price feed aggregator
    print("Deploying Mock Price Feed...")
    mock_price_feed = MockV3Aggregator.deploy(
        decimals, initial_value, {"from": account}
    )
    print(f"Deployed to {mock_price_feed.address}")
    # deploy mock VRFCoordinator
    print("Deploying Mock VRFCoordinator...")
    mock_vrf_coordinator = VRFCoordinatorMock.deploy(
        link_token.address, {"from": account}
    )
    print(f"Deployed to {mock_vrf_coordinator.address}")
    # deploy Oracle
    print("Deploying Mock Oracle...")
    mock_oracle = MockOracle.deploy(link_token.address, {"from": account})
    print(f"Deployed to {mock_oracle.address}")
    print("Mocks Deployed!")


def fund_with_link(
    contract_address, 
    account=None, 
    link_token=None, 
    amount=Web3.toWei(2, "ether")
):
    """
    Fund given contract with LINK in order to get a random number from VRF Coordinator

    Args:
        contract_address (string): the contract address to be funded
        account (string): the account to be used for fudning contract_address
        link_token (string): address of link token 
        amount (int): the amount (in WEI) to be send to fund the contract_address 
    """
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    funding_tx = link_token.transfer(contract_address, amount, {"from": account})
    # @NOTE if interface:
    # link_token_contract = interface.ILinkToken(link_token.address) 
    # funding_tx = link_token_contract.transfer(contract_address, amount, {"from": account})
    funding_tx.wait(1)
    print(f"Funded {contract_address}")
    return funding_tx


def encode_function_data(initializer=None, *args):
    """
    Encodes the function call so we can work with an initializer.
    
    Args:
        initializer ([brownie.network.contract.ContractTx], optional):
        The initializer function we want to call. Example: 'box.store'.
        Defaults to None.
        
        args (Any, optional):
        The arguments to pass to the initializer function.
        
    Returns:
        [bytes]: Return the encoded bytes.
    """
    if len(args) == 0 or not initializer:
        return eth_utils.to_bytes(hexstr="0x") # to return at least some bytes;
    return initializer.encode_input(*args)


def upgrade(
    account, 
    proxy, 
    new_implementation_address, 
    proxy_admin_contract=None, 
    initializer=None, 
    *args
    ):
    """
    Update our proxy contract:

    Args:
        account (string, address): the caller account private key
        proxy (string, contract): the proxy contract to be updated
        new_implementation_address (string, address): the address of implementation contract (the new one)
        proxy_admin_contract (string, contract, optional): if admin contract exists
        initializer (string, optional): if initializer exists (to be encoded)
        *args (Any, optional): if *args exists (parameter to be encoded with initializer)
    """
    transaction = None
    if proxy_admin_contract:
        if initializer:
            # encode initiliazer in bytes
            encoded_function_call = encode_function_data(initializer, *args)
            # upgrade the proxy admin contract with encoded initializer
            transaction = proxy_admin_contract.upgradeAndCall(
                proxy.address,  
                new_implementation_address,
                encoded_function_call,
                {"from": account},
            )
        else:
            # upgrade the proxy admin contract WITHOUT encoded initializer
            transaction = proxy_admin_contract.upgrade(
                proxy.address,
                new_implementation_address,
                {"from": account},
            )
    else:
    # if proxy admin does not exists
        if initializer:
            # encode initiliazer in bytes
            encoded_function_call = encode_function_data(initializer, *args)
            transaction = proxy.upgradeToAndCall(
                new_implementation_address,
                encoded_function_call,
                {"from": account},
            )
        else:
            transaction == proxy.upgradeTo(
                new_implementation_address,
                {"from": account},
            )
    return transaction


def deploy_proxy(account, contract_deployed, contract_name="contract", initilizer=None, *args):
    # 1.create proxy admin
    proxy_admin = ProxyAdmin.deploy(
        {"from": account}, 
        publish_source=config["networks"][network.show_active()].get("publish", False)
        )
    # 2.encode initiazer
    if initilizer:
        encoded_initiliazer = encode_function_data(initilizer, *args)
    else:
        encoded_initiliazer = encode_function_data()
    # 3.create proxy
    proxy = TransparentUpgradeableProxy.deploy(
        contract_deployed.address,
        proxy_admin.address,
        encoded_initiliazer,
        {"from": account, "gas_limit": 1000000},
        publish_source=config["networks"][network.show_active()].get("publish", False)
    )
    # 4. create proxy contract
    proxy_contract = Contract.from_abi(
        contract_name, proxy.address, contract_deployed.abi
    )
    return proxy_admin, proxy_contract, proxy