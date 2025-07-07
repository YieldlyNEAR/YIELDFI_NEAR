// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title Mock WETH Token
/// @notice Mock WETH token for testing.
contract MockWETH is ERC20, Ownable {
    uint8 private constant DECIMALS = 18;
    uint256 private constant INITIAL_SUPPLY = 120_000_000 * 10 ** DECIMALS; // 120M WETH

    constructor() ERC20("Wrapped Ether", "WETH") { // Removed Ownable(msg.sender)
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
            amount <= 10 * 10 ** DECIMALS,
            "MockWETH: Max 10 WETH per faucet"
        );
        _mint(msg.sender, amount);
    }

    function deposit() external payable {
        _mint(msg.sender, msg.value);
    }

    function withdraw(uint256 amount) external {
        require(
            balanceOf(msg.sender) >= amount,
            "MockWETH: Insufficient balance"
        );
        _burn(msg.sender, amount);
        payable(msg.sender).transfer(amount);
    }
    
    receive() external payable {
        _mint(msg.sender, msg.value);
    }
}
