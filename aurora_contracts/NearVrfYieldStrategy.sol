// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./interfaces/Strategies.sol";

/// @title NearVrfYieldStrategy
/// @notice A strategy that uses block variables for pseudo-randomness on EVM testnets.
/// @dev for testing and demonstration purposes. Not secure for production.
contract NearVrfYieldStrategy is IStrategies, ReentrancyGuard {
    using SafeERC20 for IERC20;

    address public immutable vault;
    IERC20 internal immutable _underlyingToken;
    address public immutable yieldSource;

    address[] public depositors;
    mapping(address => uint256) public depositAmounts;
    uint256 public totalDeposited;
    address public lastWinner;
    bool public paused;

    event YieldDeposited(uint256 amount);
    event WinnerAwarded(address indexed winner, uint256 amount);

    constructor(address _vault, address _underlying, address _yieldSource) {
        vault = _vault;
        _underlyingToken = IERC20(_underlying);
        yieldSource = _yieldSource;
    }

    function execute(uint256 amount, bytes calldata data) external override nonReentrant {
        require(msg.sender == vault, "Only vault can execute");
        require(!paused, "Strategy is paused");
        require(amount > 0, "Amount must be positive");

        if (depositAmounts[tx.origin] == 0) {
            depositors.push(tx.origin);
        }
        depositAmounts[tx.origin] += amount;
        totalDeposited += amount;
        
        emit Deposit(amount);
    }

    function depositYield(uint256 yieldAmount) external nonReentrant {
        require(yieldAmount > 0, "Yield must be positive");
        _underlyingToken.safeTransferFrom(msg.sender, address(this), yieldAmount);
        emit YieldDeposited(yieldAmount);
    }
    
    function harvest(bytes calldata data) external override nonReentrant {
        require(msg.sender == vault, "Only vault can call harvest");
        uint256 yieldBalance = _underlyingToken.balanceOf(address(this)) - totalDeposited;

        if (yieldBalance > 0 && depositors.length > 0) {
            address winner = _pickWinner();
            lastWinner = winner;
            
            _underlyingToken.safeTransfer(winner, yieldBalance);
            emit WinnerAwarded(winner, yieldBalance);
        }
        emit Harvested(data);
    }

    function _pickWinner() internal view returns (address) {
        // Insecure pseudo-randomness for testnet purposes. DO NOT USE IN PRODUCTION.
        uint256 randomSeed = uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, depositors.length)));
        
        uint256 winnerIndex = randomSeed % depositors.length;
        return depositors[winnerIndex];
    }
    
    function emergencyExit(bytes calldata data) external override {
        require(msg.sender == vault, "Only vault can exit");
        uint256 balance = _underlyingToken.balanceOf(address(this));
        if (balance > 0) {
            _underlyingToken.safeTransfer(vault, balance);
        }
        emit EmergencyExited(balance, data);
    }

    function getBalance() public view override returns (uint256) {
        return _underlyingToken.balanceOf(address(this));
    }

    // --- Interface Compliance ---
    function underlyingToken() external view override returns (address) { return address(_underlyingToken); }
    function knownRewardTokens(address token) external view override returns (bool) { return token == address(_underlyingToken); }
    function rewardTokensList() external view override returns (address[] memory) {
        address[] memory tokens = new address[](1);
        tokens[0] = address(_underlyingToken);
        return tokens;
    }
    function setPaused(bool _paused) external override {
        require(msg.sender == vault, "Only vault can set pause");
        paused = _paused;
    }

    // --- Unused Functions ---
    function protocol() external pure override returns (address) { return address(0); }
    function depositSelector() external pure override returns (bytes4) { return bytes4(0); }
    function withdrawSelector() external pure override returns (bytes4) { return bytes4(0); }
    function claimSelector() external pure override returns (bytes4) { return bytes4(0); }
    function getBalanceSelector() external pure override returns (bytes4) { return bytes4(0); }
    function setVault(address _vault) external override {}
    function addRewardToken(address tokenAddress) external override {}
    function claimRewards(bytes calldata data) external override {}
    function queryProtocol(bytes4 selector, bytes calldata params) external view override returns (bytes memory) { return ""; }
}
