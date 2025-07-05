// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
// Import IERC20Metadata for the constructor
import "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./interfaces/Strategies.sol";

/// @title Vault Contract (for OZ v4.7.1)
/// @notice An ERC4626 vault that manages deposits and allocates them to various yield strategies.
contract Vault is Ownable, ERC4626, AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");
    bytes32 public constant AGENT_ROLE = keccak256("AGENT_ROLE");

    address[] public strategies;
    mapping(address => bool) public isStrategy;

    event StrategyAdded(address indexed strategy);
    event StrategyRemoved(address indexed strategy);
    event StrategyExecuted(address indexed strategy, uint256 amount, bytes data);
    event StrategyHarvested(address indexed strategy, bytes data);

    error InvalidStrategy();
    error StrategyAlreadyExists();
    error StrategyDoesNotExist();
    error ExecutionFailed();
    error InvalidAddress();
    error InsufficientBalance();

    modifier onlyManager() {
        require(hasRole(MANAGER_ROLE, msg.sender), "Vault: caller is not a manager");
        _;
    }

    modifier onlyAgent() {
        require(hasRole(AGENT_ROLE, msg.sender), "Vault: caller is not an agent");
        _;
    }

    constructor(
        // Changed type from IERC20 to IERC20Metadata to match ERC4626 constructor
        IERC20Metadata assetToken,
        string memory name,
        string memory symbol,
        address _manager,
        address _agent
    ) ERC4626(assetToken) ERC20(name, symbol) {
        _transferOwnership(msg.sender);

        require(_manager != address(0), "Manager cannot be zero address");
        require(_agent != address(0), "Agent cannot be zero address");

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setRoleAdmin(MANAGER_ROLE, DEFAULT_ADMIN_ROLE);
        _setRoleAdmin(AGENT_ROLE, DEFAULT_ADMIN_ROLE);

        _grantRole(MANAGER_ROLE, _manager);
        _grantRole(AGENT_ROLE, _agent);
    }

    function addStrategy(address _strategy) external onlyManager {
        if (_strategy == address(0)) revert InvalidAddress();
        if (isStrategy[_strategy]) revert StrategyAlreadyExists();

        isStrategy[_strategy] = true;
        strategies.push(_strategy);
        emit StrategyAdded(_strategy);
    }

    function removeStrategy(address _strategy) external onlyManager {
        if (!isStrategy[_strategy]) revert StrategyDoesNotExist();
        isStrategy[_strategy] = false;

        for (uint256 i = 0; i < strategies.length; i++) {
            if (strategies[i] == _strategy) {
                strategies[i] = strategies[strategies.length - 1];
                strategies.pop();
                break;
            }
        }
        emit StrategyRemoved(_strategy);
    }

    function depositToStrategy(
        address _strategy,
        uint256 _amount,
        bytes calldata _data
    ) external onlyAgent nonReentrant {
        if (!isStrategy[_strategy]) revert StrategyDoesNotExist();
        // Corrected: Cast the address from asset() to IERC20 before calling balanceOf
        if (IERC20(asset()).balanceOf(address(this)) < _amount) revert InsufficientBalance();

        // Corrected: Cast the address from asset() to IERC20 before calling safeApprove
        IERC20(asset()).safeApprove(_strategy, _amount);
        IStrategies(_strategy).execute(_amount, _data);
        emit StrategyExecuted(_strategy, _amount, _data);
    }
    
    function harvestStrategy(
        address _strategy,
        bytes calldata _data
    ) external onlyAgent nonReentrant {
        if (!isStrategy[_strategy]) revert StrategyDoesNotExist();

        IStrategies(_strategy).harvest(_data);
        emit StrategyHarvested(_strategy, _data);
    }

    function getStrategies() external view returns (address[] memory) {
        return strategies;
    }
}