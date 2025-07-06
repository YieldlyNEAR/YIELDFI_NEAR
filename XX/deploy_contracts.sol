// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title Aurora Multi-Strategy Vault
 * @dev ERC4626-compatible vault with multi-protocol yield optimization
 */
contract AuroraMultiVault is ERC20, Ownable, ReentrancyGuard {
    IERC20 public immutable asset; // USDC
    
    struct Strategy {
        address strategyAddress;
        uint256 allocation; // Basis points (10000 = 100%)
        uint256 balance;
        bool active;
        string name;
    }
    
    Strategy[] public strategies;
    mapping(address => bool) public isStrategy;
    mapping(address => uint256) public strategyIndex;
    
    uint256 public totalDeployed;
    uint256 public lastRebalance;
    uint256 public constant REBALANCE_INTERVAL = 1 hours;
    
    event StrategyAdded(address indexed strategy, string name, uint256 allocation);
    event StrategyRebalanced(address indexed strategy, uint256 oldBalance, uint256 newBalance);
    event YieldHarvested(address indexed strategy, uint256 amount);
    event EmergencyExit(address indexed strategy, uint256 amount);
    
    constructor(
        address _asset,
        string memory _name,
        string memory _symbol
    ) ERC20(_name, _symbol) {
        asset = IERC20(_asset);
    }
    
    // ERC4626-like functions
    function totalAssets() public view returns (uint256) {
        return asset.balanceOf(address(this)) + totalDeployed;
    }
    
    function convertToShares(uint256 assets) public view returns (uint256) {
        uint256 supply = totalSupply();
        return supply == 0 ? assets : (assets * supply) / totalAssets();
    }
    
    function convertToAssets(uint256 shares) public view returns (uint256) {
        uint256 supply = totalSupply();
        return supply == 0 ? shares : (shares * totalAssets()) / supply;
    }
    
    // Deposit function
    function deposit(uint256 assets, address receiver) external nonReentrant returns (uint256 shares) {
        require(assets > 0, "Zero assets");
        
        shares = convertToShares(assets);
        
        asset.transferFrom(msg.sender, address(this), assets);
        _mint(receiver, shares);
        
        // Auto-deploy if vault has enough balance
        if (asset.balanceOf(address(this)) > 1000 * 1e6) { // 1000 USDC threshold
            _autoRebalance();
        }
        
        return shares;
    }
    
    // Withdrawal function
    function withdraw(uint256 assets, address receiver, address owner) external nonReentrant returns (uint256 shares) {
        shares = convertToShares(assets);
        require(shares <= balanceOf(owner), "Insufficient shares");
        
        if (msg.sender != owner) {
            uint256 allowed = allowance(owner, msg.sender);
            require(allowed >= shares, "Insufficient allowance");
            _approve(owner, msg.sender, allowed - shares);
        }
        
        // Check if we need to withdraw from strategies
        uint256 available = asset.balanceOf(address(this));
        if (available < assets) {
            _withdrawFromStrategies(assets - available);
        }
        
        _burn(owner, shares);
        asset.transfer(receiver, assets);
        
        return shares;
    }
    
    // Strategy management
    function addStrategy(
        address _strategy,
        string memory _name,
        uint256 _allocation
    ) external onlyOwner {
        require(!isStrategy[_strategy], "Strategy exists");
        require(_allocation <= 5000, "Max 50% allocation"); // Max 50%
        
        strategies.push(Strategy({
            strategyAddress: _strategy,
            allocation: _allocation,
            balance: 0,
            active: true,
            name: _name
        }));
        
        isStrategy[_strategy] = true;
        strategyIndex[_strategy] = strategies.length - 1;
        
        emit StrategyAdded(_strategy, _name, _allocation);
    }
    
    // Deploy to specific strategy
    function depositToStrategy(address strategy, uint256 amount, bytes calldata data) external onlyOwner {
        require(isStrategy[strategy], "Invalid strategy");
        require(amount <= asset.balanceOf(address(this)), "Insufficient balance");
        
        asset.transfer(strategy, amount);
        
        uint256 index = strategyIndex[strategy];
        strategies[index].balance += amount;
        totalDeployed += amount;
        
        // Call strategy-specific deposit logic if needed
        if (data.length > 0) {
            (bool success,) = strategy.call(data);
            require(success, "Strategy call failed");
        }
    }
    
    // Harvest from strategy
    function harvestStrategy(address strategy, bytes calldata data) external onlyOwner {
        require(isStrategy[strategy], "Invalid strategy");
        
        uint256 balanceBefore = asset.balanceOf(address(this));
        
        // Call strategy harvest
        (bool success,) = strategy.call(data);
        require(success, "Harvest failed");
        
        uint256 balanceAfter = asset.balanceOf(address(this));
        uint256 harvested = balanceAfter - balanceBefore;
        
        emit YieldHarvested(strategy, harvested);
    }
    
    // Rebalance portfolio
    function rebalance(address[] calldata strategyAddresses, uint256[] calldata targetAmounts) external onlyOwner {
        require(strategyAddresses.length == targetAmounts.length, "Length mismatch");
        require(block.timestamp >= lastRebalance + REBALANCE_INTERVAL, "Too frequent");
        
        uint256 totalTarget = 0;
        for (uint256 i = 0; i < targetAmounts.length; i++) {
            totalTarget += targetAmounts[i];
        }
        
        uint256 availableAssets = totalAssets();
        require(totalTarget <= availableAssets, "Insufficient assets");
        
        // Withdraw excess from strategies
        for (uint256 i = 0; i < strategies.length; i++) {
            Strategy storage strategy = strategies[i];
            if (!strategy.active) continue;
            
            // Find target for this strategy
            uint256 target = 0;
            for (uint256 j = 0; j < strategyAddresses.length; j++) {
                if (strategyAddresses[j] == strategy.strategyAddress) {
                    target = targetAmounts[j];
                    break;
                }
            }
            
            uint256 oldBalance = strategy.balance;
            
            if (strategy.balance > target) {
                // Withdraw excess
                uint256 excess = strategy.balance - target;
                _withdrawFromStrategy(strategy.strategyAddress, excess);
                strategy.balance = target;
                totalDeployed -= excess;
            } else if (strategy.balance < target) {
                // Deploy more
                uint256 needed = target - strategy.balance;
                uint256 available = asset.balanceOf(address(this));
                uint256 toDeposit = needed > available ? available : needed;
                
                if (toDeposit > 0) {
                    asset.transfer(strategy.strategyAddress, toDeposit);
                    strategy.balance += toDeposit;
                    totalDeployed += toDeposit;
                }
            }
            
            emit StrategyRebalanced(strategy.strategyAddress, oldBalance, strategy.balance);
        }
        
        lastRebalance = block.timestamp;
    }
    
    // Emergency exit from all strategies
    function emergencyExit() external onlyOwner {
        for (uint256 i = 0; i < strategies.length; i++) {
            if (strategies[i].active && strategies[i].balance > 0) {
                _withdrawFromStrategy(strategies[i].strategyAddress, strategies[i].balance);
                emit EmergencyExit(strategies[i].strategyAddress, strategies[i].balance);
                totalDeployed -= strategies[i].balance;
                strategies[i].balance = 0;
            }
        }
    }
    
    // Internal functions
    function _autoRebalance() internal {
        if (block.timestamp < lastRebalance + REBALANCE_INTERVAL) return;
        
        uint256 totalBalance = asset.balanceOf(address(this));
        
        // Deploy according to allocation percentages
        for (uint256 i = 0; i < strategies.length; i++) {
            Strategy storage strategy = strategies[i];
            if (!strategy.active) continue;
            
            uint256 targetAmount = (totalBalance * strategy.allocation) / 10000;
            
            if (targetAmount > 0) {
                asset.transfer(strategy.strategyAddress, targetAmount);
                strategy.balance += targetAmount;
                totalDeployed += targetAmount;
            }
        }
        
        lastRebalance = block.timestamp;
    }
    
    function _withdrawFromStrategies(uint256 amount) internal {
        uint256 remaining = amount;
        
        // Withdraw from strategies in reverse allocation order (highest allocation first)
        for (uint256 i = strategies.length; i > 0; i--) {
            Strategy storage strategy = strategies[i - 1];
            if (!strategy.active || strategy.balance == 0) continue;
            
            uint256 toWithdraw = remaining > strategy.balance ? strategy.balance : remaining;
            _withdrawFromStrategy(strategy.strategyAddress, toWithdraw);
            
            strategy.balance -= toWithdraw;
            totalDeployed -= toWithdraw;
            remaining -= toWithdraw;
            
            if (remaining == 0) break;
        }
    }
    
    function _withdrawFromStrategy(address strategy, uint256 amount) internal {
        // Simple transfer back (real strategies would have complex withdrawal logic)
        IERC20(asset).transferFrom(strategy, address(this), amount);
    }
    
    // View functions
    function getStrategies() external view returns (Strategy[] memory) {
        return strategies;
    }
    
    function getStrategy(address strategyAddress) external view returns (Strategy memory) {
        require(isStrategy[strategyAddress], "Invalid strategy");
        return strategies[strategyIndex[strategyAddress]];
    }
}

/**
 * @title Ref Finance Strategy (Simplified)
 */
contract RefFinanceStrategy {
    IERC20 public immutable asset;
    address public immutable vault;
    address public constant REF_ROUTER = 0x2d3162c6c6495E5C2D62BB38aFdF44a8b0Ed6c57;
    
    constructor(address _asset, address _vault) {
        asset = IERC20(_asset);
        vault = _vault;
    }
    
    modifier onlyVault() {
        require(msg.sender == vault, "Only vault");
        _;
    }
    
    function deposit(uint256 amount) external onlyVault {
        // Simplified: just hold USDC (real implementation would add liquidity to Ref)
        asset.transferFrom(vault, address(this), amount);
    }
    
    function withdraw(uint256 amount) external onlyVault {
        asset.transfer(vault, amount);
    }
    
    function harvest() external onlyVault {
        // Simplified: no actual yield generation
        // Real implementation would claim REF rewards and convert to USDC
    }
    
    function getBalance() external view returns (uint256) {
        return asset.balanceOf(address(this));
    }
}

/**
 * @title TriSolaris Strategy (Simplified)
 */
contract TriSolarisStrategy {
    IERC20 public immutable asset;
    address public immutable vault;
    address public constant TRI_ROUTER = 0x2CB45Edb4517d5947aFdE3BEAbF95A582506858B;
    
    constructor(address _asset, address _vault) {
        asset = IERC20(_asset);
        vault = _vault;
    }
    
    modifier onlyVault() {
        require(msg.sender == vault, "Only vault");
        _;
    }
    
    function deposit(uint256 amount) external onlyVault {
        asset.transferFrom(vault, address(this), amount);
    }
    
    function withdraw(uint256 amount) external onlyVault {
        asset.transfer(vault, amount);
    }
    
    function harvest() external onlyVault {
        // Simplified: no actual yield generation
    }
    
    function getBalance() external view returns (uint256) {
        return asset.balanceOf(address(this));
    }
}

/**
 * @title Bastion Strategy (Simplified)
 */
contract BastionStrategy {
    IERC20 public immutable asset;
    address public immutable vault;
    address public constant BASTION_CUSDC = 0xe5308dc623101508952948b141fD9eaBd3337D99;
    
    constructor(address _asset, address _vault) {
        asset = IERC20(_asset);
        vault = _vault;
    }
    
    modifier onlyVault() {
        require(msg.sender == vault, "Only vault");
        _;
    }
    
    function deposit(uint256 amount) external onlyVault {
        asset.transferFrom(vault, address(this), amount);
        // Real implementation would mint cUSDC tokens
    }
    
    function withdraw(uint256 amount) external onlyVault {
        asset.transfer(vault, amount);
        // Real implementation would redeem cUSDC tokens
    }
    
    function harvest() external onlyVault {
        // Real implementation would claim BASTION rewards
    }
    
    function getBalance() external view returns (uint256) {
        return asset.balanceOf(address(this));
    }
}