from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")

def test_opsss(currency,strategy, rewards,chain,vault,cdai, ibDAI,whale,gov,strategist, interface):
    rate_limit = 1_000_000_000 *1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, rate_limit, 1000, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 10_000 *1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})
    assert currency.balanceOf(strategy) ==0

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    chain.mine(100)
    cdai.mint(0, {'from': strategist})

    strategy.harvest({'from': strategist})
    

    print("ibDai = ", ibDAI.balanceOf(strategy)/1e18)
    print("dai = ", currency.balanceOf(strategy)/1e18)

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-10_000*1e18)*21024)/(10_000*1e18)))

    vault.withdraw({"from": whale})
    vault.withdraw({"from": rewards})
    vault.withdraw({"from": strategist})
    print("\nWithdraw")
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    whaleP = (currency.balanceOf(whale) - whalebefore)
    print("Whale profit: ", whaleP/1e18)
    print("Whale profit %: ", (whaleP*21024)/whale_deposit)




def test_migrate(currency,Strategy, strategy,ibDAI, chain,vault, whale,gov,strategist, interface):
    rate_limit = 1_000_000_000 *1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, rate_limit, 1000, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whale_deposit  = 10_000 *1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})
    

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    chain.mine(1)

    strategy.harvest({'from': strategist})

    strategy2 = strategist.deploy(Strategy, vault, ibDAI)
    vault.migrateStrategy(strategy, strategy2, {'from': gov})
    assert ibDAI.balanceOf(strategy) == 0
    assert ibDAI.balanceOf(strategy2) > 0
    print(ibDAI.balanceOf(strategy2))

def test_reduce_limit(currency,Strategy,cdai, strategy, chain,vault, ibDAI, whale,gov,strategist, interface):
    rate_limit = 1_000_000_000 *1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, rate_limit, 1000, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whale_deposit  = 100 *1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})
    strategy.harvest({'from': strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    vault.revokeStrategy(strategy, {'from': gov})
    cdai.mint(0, {'from': strategist}); 
    strategy.harvest({'from': strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    print(ibDAI.balanceOf(strategy))
    assert ibDAI.balanceOf(strategy) < 1_000_000
    assert currency.balanceOf(strategy) < 10

def test_live_add(currency,Strategy,cdai, strategist, ibDAI, live_dai_comp_strategy, live_vault, ychad):
    vault = live_vault
    strategy = strategist.deploy(Strategy, vault, ibDAI)

    vault.updateStrategyDebtRatio(live_dai_comp_strategy, 8_000, {'from': ychad})
    vault.addStrategy(strategy, 1_000, 0, 1000, {"from": ychad})
    live_dai_comp_strategy.harvest({'from': ychad})
    live_dai_comp_strategy.harvest({'from': ychad})


    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    strategy.harvest({'from': ychad})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)


def test_immediate_withdraw(currency,strategy, rewards,chain,vault,cdai, ibDAI,whale,gov,strategist, interface):
    rate_limit = 1_000_000_000 *1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, rate_limit, 1000, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 10_000 *1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})
    assert currency.balanceOf(strategy) ==0

    vault.withdraw({"from": whale})
    vault.withdraw({"from": rewards})
    print("\nWithdraw")
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    whaleP = (currency.balanceOf(whale) - whalebefore)
    print("Whale profit: ", whaleP/1e18)

def test_no_liquidity(currency,Strategy,cdai, strategy, chain,vault, weth, cweth, ibDAI, whale,gov,strategist, interface):
    rate_limit = 1_000_000_000 *1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, rate_limit, 1000, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    weth.approve(cweth, 2 ** 256 - 1, {"from": whale} )
    cweth.mint(1000*1e18, {"from": whale})
    cweth.borrow(1, {"from": whale})

    whale_deposit  = 1000 *1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})

    cdai.borrow(currency.balanceOf(cdai), {"from": whale})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    pre = vault.balanceOf(whale)

    vault.withdraw({"from": whale})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    assert vault.balanceOf(whale) == pre
