// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title Mock USDC Token
/// @notice Mock USDC token for testing.
contract MockUSDC is ERC20, Ownable {
    uint8 private constant DECIMALS = 6;
    uint256 private constant INITIAL_SUPPLY = 1_000_000_000 * 10 ** DECIMALS; // 1B USDC

    constructor() ERC20("USD Coin", "USDC") { // Removed Ownable(msg.sender)
        _transferOwnership(msg.sender); // Added for OZ v4 compatibility
        _mint(msg.sender, INITIAL_SUPPLY);
    }

    function decimals() public pure override returns (uint8) {
        return DECIMALS;
    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }

    function faucet(uint256 amount) external {
        require(
            amount <= 10_000 * 10 ** DECIMALS,
            "MockUSDC: Max 10,000 USDC per faucet"
        );
        _mint(msg.sender, amount);
    }
}
