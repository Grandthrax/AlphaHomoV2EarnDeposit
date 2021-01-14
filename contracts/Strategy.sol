// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "./interfaces/curve/Curve.sol";
import "./interfaces/curve/Gauge.sol";
import "./interfaces/curve/IMinter.sol";
import "./interfaces/curve/ICrvV3.sol";
import "./interfaces/UniswapInterfaces/IUniswapV2Router02.sol";


// These are the core Yearn libraries
import {
    BaseStrategy,
    StrategyParams
} from "@yearnvaults/contracts/BaseStrategy.sol";
import {
    SafeERC20,
    SafeMath,
    IERC20,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";


// Import interfaces for many popular DeFi projects, or add your own!
//import "../interfaces/<protocol>/<Interface>.sol";

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    IUniswapV2Router02 public constant uniswapRouter = IUniswapV2Router02(address(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D));
    address public constantCurveContractV3 =  address(0x06325440D014e39736583c165C2963BA99fAf14E);
    Gauge public LiquidityGaugeV2 =  Gauge(address(0x182B723a58739a9c974cFDB385ceaDb237453c28));
    ICurveFi public StableSwapSTETH =  ICurveFi(address(0xDC24316b9AE028F1497c275EB9192a3Ea0f67022));
   // IMinter public CrvMinter = IMinter(address(0xd061D61a4d941c39E5453435B6345Dc261C2fcE0));

    address public constant weth = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);

    address public stETH =  address(0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84);
    IERC20 public LDO =  IERC20(address(0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32));
    ICrvV3 public CRV =  ICrvV3(address(0xD533a949740bb3306d119CC777fa900bA034cd52));


    constructor(address _vault) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        // maxReportDelay = 6300;
        // profitFactor = 100;
        // debtThreshold = 0;

        want.safeApprove(address(LiquidityGaugeV2), uint256(-1));
        LDO.safeApprove(address(uniswapRouter), uint256(-1));
        CRV.approve(address(uniswapRouter), uint256(-1));
    }

    //we get eth
    receive() external payable {}


    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external override view returns (string memory) {
        // Add your own name here, suggestion e.g. "StrategyCreamYFI"
        return "StrategystETHCurve";
    }

    function estimatedTotalAssets() public override view returns (uint256) {
        uint256 currentBal = LiquidityGaugeV2.balanceOf(address(this));

        //uint256 claimableLDO = LiquidityGaugeV2.claimable_reward(address(this), address(LDO));
        //uint256 LDOshaare = _estimateSell(address(LDO), claimableLDO);

        //uint256 claimableCRV = LiquidityGaugeV2.claimable_reward(address(this), address(CRV));
        //uint256 CRVshaare = _estimateSell(address(CRV), claimableCRV);

        //uint256 futureBal = claimableLDO.add(claimableCRV).mul(9).div(10);

        return currentBal;
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        // TODO: Do stuff here to free up any returns back into `want`
        // NOTE: Return `_profit` which is value generated by all positions, priced in `want`
        // NOTE: Should try to free up at least `_debtOutstanding` of underlying position

        uint256 guageTokens = LiquidityGaugeV2.balanceOf(address(this));
        if(guageTokens > 0){
            LiquidityGaugeV2.claim_rewards();
            IMinter(CRV.minter()).mint(address(LiquidityGaugeV2));

           uint256 ldo_balance = LDO.balanceOf(address(this));

            if(ldo_balance > 0){
                _sell(address(LDO), ldo_balance);
            }

            uint256 crv_balance = CRV.balanceOf(address(this));

            if(crv_balance > 0){
                _sell(address(CRV), crv_balance);
            }

            uint256 balance = address(this).balance;
            StableSwapSTETH.add_liquidity{value: balance}([balance, 0], 0);

            _profit = want.balanceOf(address(this));
        }

        if(_debtOutstanding > 0){
            if(_debtOutstanding > _profit){
                LiquidityGaugeV2.withdraw(_debtOutstanding - _profit);
            }
        }

        
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        // TODO: Do something to invest excess `want` tokens (from the Vault) into your positions
        // NOTE: Try to adjust positions so that `_debtOutstanding` can be freed up on *next* harvest (not immediately)

        uint256 _toInvest = want.balanceOf(address(this));

        LiquidityGaugeV2.deposit(_toInvest);
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        // TODO: Do stuff here to free up to `_amountNeeded` from all positions back into `want`
        // NOTE: Maintain invariant `want.balanceOf(this) >= _liquidatedAmount`
        // NOTE: Maintain invariant `_liquidatedAmount + _loss <= _amountNeeded`

        uint256 totalAssets = want.balanceOf(address(this));
        if (_amountNeeded > totalAssets) {
            _liquidatedAmount = totalAssets;
            _loss = _amountNeeded.sub(totalAssets);
        } else {
            _liquidatedAmount = _amountNeeded;
        }
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        prepareReturn(LiquidityGaugeV2.balanceOf(address(this)));
    }

    //sell all function
    function _sell(address currency, uint256 amount) internal {

        address[] memory path = new address[](2);
        path[0] = currency;
        path[1] = weth;

        uniswapRouter.swapExactTokensForETH(amount, uint256(0), path, address(this), now);

    }

    function _estimateSell(address currency, uint256 amount) internal view returns (uint256 outAmount){

        
        address[] memory path = new address[](2);
        path[0] = currency;
        path[1] = weth;
        uint256[] memory amounts = uniswapRouter.getAmountsOut(amount, path);
        outAmount = amounts[amounts.length - 1];

        return outAmount;

    }

    // Override this to add all tokens/tokenized positions this contract manages
    // on a *persistent* basis (e.g. not just for swapping back to want ephemerally)
    // NOTE: Do *not* include `want`, already included in `sweep` below
    //
    // Example:
    //
    //    function protectedTokens() internal override view returns (address[] memory) {
    //      address[] memory protected = new address[](3);
    //      protected[0] = tokenA;
    //      protected[1] = tokenB;
    //      protected[2] = tokenC;
    //      return protected;
    //    }
    function protectedTokens()
        internal
        override
        view
        returns (address[] memory)
    {

        address[] memory protected = new address[](1);
          protected[0] = address(LiquidityGaugeV2);
    
          return protected;
    }
}
