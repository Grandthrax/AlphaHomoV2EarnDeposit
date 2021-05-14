from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

def test_opsss_lvie(currency,Strategy, Contract,cusdt, chain,live_vault_usdt, whale,gov,ibUSDT, samdev,strategist, interface, accounts):

    strategist = samdev
    vault = live_vault_usdt

    currency = interface.ERC20(vault.token())

    strategy = strategist.deploy(Strategy, vault, ibUSDT)

    gov = accounts.at(vault.governance(), force=True)

    strat1 = Contract(vault.withdrawalQueue(0))
    vault.updateStrategyDebtRatio(strat1, 0, {'from': gov})
    vault.addStrategy(strategy, 2000, 0,2**256-1, 1000, {'from': gov})

    strat1.harvest({'from': gov})
    strategy.harvest({'from': gov})
    ibUSDT

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    chain.sleep(2592000)
    chain.mine(100)
    cusdt.mint(0, {'from': gov})


    strategy.harvest({'from': strategist})
    

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-1000*1e18)*12)/(1000*1e18)))
