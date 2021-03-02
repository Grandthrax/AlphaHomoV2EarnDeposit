// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "./interfaces/AH2/ISafeBox.sol";
import "./interfaces/UniswapInterfaces/IUniswapV2Router02.sol";
import "./Interfaces/Compound/CErc20I.sol";


// These are the core Yearn libraries
import {
    BaseStrategy
} from "@yearnvaults/contracts/BaseStrategy.sol";

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";


// Import interfaces for many popular DeFi projects, or add your own!
//import "../interfaces/<protocol>/<Interface>.sol";

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address private uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;

    ISafeBox public safeBox;
    CErc20I public crToken;
   
    address public constant weth = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);


    constructor(address _vault, address _safeBox) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        // maxReportDelay = 6300;
        profitFactor = 1000;
        debtThreshold = 1_000_000 *1e18;
        safeBox = ISafeBox(_safeBox);
        require(address(want) == safeBox.uToken(), "Wrong safebox");
        crToken = CErc20I(safeBox.cToken());

        want.safeApprove(_safeBox, uint256(-1));
    }


    function name() external override view returns (string memory) {
        // Add your own name here, suggestion e.g. "StrategyCreamYFI"
        return string(abi.encodePacked("StrategyAH2Earn", crToken.symbol()));
    }

    function claim(uint totalReward, bytes32[] memory proof) public onlyAuthorized {
        safeBox.claim(totalReward, proof);
    }

    function estimatedTotalAssets() public override view returns (uint256) {
        return want.balanceOf(address(this)).add(convertToUnderlying(safeBox.balanceOf(address(this))));
    }

    function convertToUnderlying(uint256 amountOfTokens) public view returns (uint256 balance){
        if (amountOfTokens == 0) {
            balance = 0;
        } else {
            balance = amountOfTokens.mul(crToken.exchangeRateStored()).div(1e18);
        }
    }

    function convertFromUnderlying(uint256 amountOfUnderlying) public view returns (uint256 balance){
        if (amountOfUnderlying == 0) {
            balance = 0;
        } else {
            balance = amountOfUnderlying.mul(1e18).div(crToken.exchangeRateStored());
        }
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

        _debtPayment = _debtOutstanding;
        uint256 lentAssets = convertToUnderlying(safeBox.balanceOf(address(this)));
        
        uint256 looseAssets = want.balanceOf(address(this));

        uint256 total = looseAssets.add(lentAssets);


        //future sam. this is from gen lender hence the logic of why we would have loose assets and no lent assets
        if (lentAssets == 0) {
            //no position to harvest or profit to report
            if (_debtPayment > looseAssets) {
                //we can only return looseAssets
                _debtPayment = looseAssets;
            }

            return (_profit, _loss, _debtPayment);
        }

        uint256 debt = vault.strategies(address(this)).totalDebt;

        if (total > debt) {
            _profit = total - debt;
            uint256 amountToFree = _profit.add(_debtPayment);
            if (amountToFree > 0 && looseAssets < amountToFree) {

                //withdraw what we can withdraw
                _withdrawSome(amountToFree.sub(looseAssets));
                uint256 newLoose = want.balanceOf(address(this));

                //if we dont have enough money adjust _debtOutstanding and only change profit if needed
                if (newLoose < amountToFree) {
                    if (_profit > newLoose) {
                        _profit = newLoose;
                        _debtPayment = 0;
                    } else {
                        _debtPayment = Math.min(newLoose - _profit, _debtPayment);
                    }
                }
            }
        } else {
            //serious. loss should never happen but if it does lets record it accurately
            _loss = debt - total;
            uint256 amountToFree = _debtPayment;

            if (amountToFree > 0 && looseAssets < amountToFree) {
                //withdraw what we can withdraw

                _withdrawSome(amountToFree.sub(looseAssets));
                uint256 newLoose = want.balanceOf(address(this));

                if (newLoose < amountToFree) {
                    _debtPayment = newLoose;
                }
            }
        }
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {

        uint256 _toInvest = want.balanceOf(address(this));

        safeBox.deposit(_toInvest);
    }

    //withdraw amount from safebox
    //safe to enter more than we have
    function _withdrawSome(uint256 _amount) internal returns (uint256) {
        

        uint256 amountInCtokens = convertFromUnderlying(_amount);
        uint256 balanceOfSafebox = safeBox.balanceOf(address(this));

        uint256 balanceBefore = want.balanceOf(address(this));

        if(balanceOfSafebox < 2){
            return 0;
        }
        balanceOfSafebox = balanceOfSafebox-1;
       

        if (amountInCtokens > balanceOfSafebox) {
            //cant withdraw more than we own
            amountInCtokens = balanceOfSafebox;
        }

        //not state changing but OK because of previous call
        uint256 liquidity = want.balanceOf(address(crToken));
        uint256 liquidityInCTokens = convertFromUnderlying(liquidity);

        if (liquidityInCTokens > 2) {
            liquidityInCTokens = liquidityInCTokens-1;
           
            if (amountInCtokens <= liquidityInCTokens) {
                //we can take all
                safeBox.withdraw(amountInCtokens);
            } else {
                //redo or else price changes
                crToken.mint(0);
                liquidityInCTokens = convertFromUnderlying(want.balanceOf(address(crToken)));
                //take all we can
                safeBox.withdraw(liquidityInCTokens);
            }
        }
        uint256 newBalance = want.balanceOf(address(this));
 
        return newBalance.sub(balanceBefore);
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        _loss; //should not be able to lose here

        uint256 looseAssets = want.balanceOf(address(this));

        if(looseAssets < _amountNeeded){
            _withdrawSome(_amountNeeded - looseAssets);
        }
       

        _liquidatedAmount = Math.min(_amountNeeded, want.balanceOf(address(this)));

    }

    function harvestTrigger(uint256 callCost) public override view returns (bool) {
        uint256 wantCallCost = ethToWant(callCost);

        return super.harvestTrigger(wantCallCost);
    }

    function ethToWant(uint256 _amount) internal view returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = weth;
        path[1] = address(want);

        uint256[] memory amounts = IUniswapV2Router02(uniswapRouter).getAmountsOut(_amount, path);

        return amounts[amounts.length - 1];
    }

    function prepareMigration(address _newStrategy) internal override {
        safeBox.transfer(_newStrategy, safeBox.balanceOf(address(this)));
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
          protected[0] = address(safeBox);
    
          return protected;
    }
}
