// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";
import "./BurningContract.sol";

contract MediavalSTRVGame is BurningContract, Ownable, VRFConsumerBase {

    using SafeMath for uint256;

    uint256 public constant ARMOR = 0;
    uint256 public constant SHIELD = 1;
    uint256 public constant SWORD = 2;

    /// @notice quote "There is no limit for the total supply of equipment" -> uint256 is limited, thus
    /// decided to set max value;
    uint256[] public mintedTotal = [0, 0, 0];
    uint256 public mintedPublicly;
    uint256 public maxAvailableForPublicMint = 1000;
    uint256[] public ratesForPublicMint = [0.1 ether, 0.1 ether, 0.1 ether];

    // Mapping from token ID to Knight's balances
    mapping(uint256 => mapping(address => uint256)) private Knights;
    // Mappings from requestID to Knigt's address/randomnesses
    mapping(bytes32 => address) public RequestIdsToKnights;
    mapping(bytes32 => uint256) public RequestIdsToRandomness;
    
    // variable related to burning item in order to mint another item 
    uint256 public mintingThreshold = 80;
    uint256 public gearToBurn = SHIELD;
    uint256 public gearToMint = SWORD;

    // VRF coordinator variables
    bytes32 public keyHash;
    uint256 public fee;  

    event RequestedRandomness(bytes32 requestId, address _knight);
    event FulfilledRandomness(bytes32 requestId, uint256 randomness, uint256 randomNumber);
    event ReceivedEther(address sender, uint256 amount);

    constructor(address _vrfCoordinator, address _linkToken, bytes32 _keyHash, uint256 _fee) 
    BurningContract("https://address-of-some-strv-server.io/{id}.json") 
    VRFConsumerBase(_vrfCoordinator, _linkToken)
    {    
        _setupRole(DEFAULT_ADMIN_ROLE, _msgSender());
        keyHash = _keyHash;
        fee = _fee;
    } 

    function mint(address knight, uint256 id, uint256 amount) public {
        require(hasRole(MINTER_ROLE, _msgSender()), "BurningContract: must have minter role to mint");
        require(0 <= id && id <= mintedTotal.length, "Gear does not exists!");
        mintedTotal[id] = mintedTotal[id].add(amount);
        Knights[id][knight] = Knights[id][knight].add(amount);
        _mint(knight, id, amount, "");
    }

    // Public mint for everyone until max NFT capacity allowed is reached 
    function publicMint(uint256 id, uint256 amount) public payable { 
        require(0 <= id && id <= mintedTotal.length, "Gear does not exists!");
        require(mintedPublicly + amount <= maxAvailableForPublicMint, "Not enough supply left in public mint");
        require(msg.value >= amount * ratesForPublicMint[id], "Not enough ETH for transaction");
        mintedPublicly = mintedPublicly.add(amount);
        mintedTotal[id] = mintedTotal[id].add(amount);
        Knights[id][msg.sender] = Knights[id][msg.sender].add(amount);
        _mint(msg.sender, id, amount, "");
    }

    // get sum of all already minted gears
    function getSum(uint256[] memory _arrayToSum) public returns (uint256) {
        uint256 i;
        uint256 sum = 0;
        for (i = 0; i < _arrayToSum.length; i++) {
            sum = sum.add(_arrayToSum[i]);
        }
        return sum;
    }

    // withdraw ETH sent to the contract (during public Mint for instance)
    function withdraw() public {
        require(hasRole(DEFAULT_ADMIN_ROLE, _msgSender()), "BurningContract: must have minter role to mint");
        require(address(this).balance > 0, "Balance is zero, cannot withdraw");
        payable(owner()).transfer(address(this).balance);
    }

    // burn gear in order to try luck in getting different gear 
    function burnToGainGear(uint256 id, uint256 amount) public {
        require(0 <= id && id <= mintedTotal.length, "Gear does not exists!");
        require(id == gearToBurn, "This gear cannot be burnt!");
        address knight = msg.sender;
        for (uint i=1; i <= amount; i++) {
            require(Knights[id][knight] > 0, "There is nothing to burn");
            Knights[id][knight] = Knights[id][knight].sub(1);
            _burn(knight, id, 1);
            sword_lottery(knight);
        }
    }
    
    // Calling VRF Coordinator / Chainlink nodes in order to get a random number
    function sword_lottery(address knight) public returns (bytes32 requestId) {
        // set the burning account -> used in fullfillRandomnes to know, which account to add minted sword
        // setBurningAccount(msg.sender);
        // LINK is defined in constructor of vrfCoordinator
        require(LINK.balanceOf(address(this)) >= fee, "Not enough LINK - fill contract!");
        // call chainlink node by requestRandomness
        requestId = requestRandomness(keyHash, fee);
        RequestIdsToKnights[requestId] = knight;
        emit RequestedRandomness(requestId, knight);
    }

    // Callback function used by VRF Coordinator / Chainlink node, i.e.:
    // once chainlink node returns data to the smart contract calling function fulfillRandomness
    // calculate random number from 1 to 100:
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness) internal override {
        // check the response
        require(_randomness > 0, "Randomness not found");
        uint256 generatedRandomNumber;
        address knight = RequestIdsToKnights[_requestId];
        generatedRandomNumber = (_randomness % 100) + 1;
        RequestIdsToRandomness[_requestId] = _randomness;
        emit FulfilledRandomness(_requestId, _randomness, generatedRandomNumber);
        // if generatedRandomNumber is less or equal to mintingThreshold, then mint new gear
        if (generatedRandomNumber <= mintingThreshold) {
            _mint(knight, gearToMint, 1, "");
        }        
    }

    receive() external payable {
        emit ReceivedEther(msg.sender, msg.value);
    }
}