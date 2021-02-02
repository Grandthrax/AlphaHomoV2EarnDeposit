pragma solidity 0.6.12;
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface ISafeBox is IERC20{
  
  function cToken() external returns (address); 
  function uToken() external returns (address);

  
  function deposit(uint amount) external;

  function withdraw(uint amount) external;

  function claim(uint totalReward, bytes32[] memory proof) external;

}