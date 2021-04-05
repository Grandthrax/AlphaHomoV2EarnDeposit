// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";

import "./interfaces/UniswapInterfaces/IUniswapV2Router02.sol";

contract AlphaDistributor {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address public governance = 0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7;
    address public strategist = 0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0;

    address public uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address public sushiswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address public router = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;

    address public daiStrat = 0x7D960F3313f3cB1BBB6BF67419d303597F3E2Fa8;
    address public usdcStrat = 0x86Aa49bf28d03B1A4aBEb83872cFC13c89eB4beD;

    address[] public usdcPath;
    address[] public daiPath;

    address public alpha = 0xa1faa113cbE53436Df28FF0aEe54275c13B40975;
    address public weth = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public dai = 0x6B175474E89094C44Da98b954EedeAC495271d0F;
    address public usdc = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;

    constructor() public{
        usdcPath = new address[](3);
        usdcPath[0] = alpha;
        usdcPath[1] = weth;
        usdcPath[2] = usdc;

        daiPath = new address[](3);
        daiPath[0] = alpha;
        daiPath[1] = weth;
        daiPath[2] = dai;

        IERC20(alpha).safeApprove(uniswapRouter, type(uint256).max);
        IERC20(alpha).safeApprove(sushiswapRouter, type(uint256).max);
    }
    modifier onlyAuthorized() {
        require(msg.sender == strategist || msg.sender == governance, "!authorized");
        _;
    }

    modifier onlyGovernance() {
        require(msg.sender == governance, "!authorized");
        _;
    }


    function setUseSushi(bool _useSushi) public onlyAuthorized {
        if(_useSushi){
            router = sushiswapRouter;
        }else{
            router = uniswapRouter;
        }
    }

    function setUseSushi(bool _usdc,  address[] memory path) public onlyGovernance {
       if(_usdc){
           usdcPath = path;
       }else{
           daiPath = path;
       }
    }
    function setStrat(bool _usdc,  address _strat) public onlyGovernance {
       if(_usdc){
           usdcStrat = _strat;
       }else{
           daiStrat = _strat;
       }
    }

    function sellUsdc(uint256 amount) public onlyAuthorized{
        IUniswapV2Router02(router).swapExactTokensForTokens(amount, 0, usdcPath, usdcStrat, now);
    }

    function sellDai(uint256 amount) public onlyAuthorized{
        IUniswapV2Router02(router).swapExactTokensForTokens(amount, 0, daiPath, daiStrat, now);
    }

}