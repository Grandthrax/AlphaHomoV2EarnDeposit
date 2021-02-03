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
    ibbefore = ibDAI.balanceOf(strategy)
    vault.migrateStrategy(strategy, strategy2, {'from': gov})
    assert ibDAI.balanceOf(strategy) == 0
    assert ibDAI.balanceOf(strategy2) == ibbefore
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

def test_live_add_both(currency,Strategy,cdai,live_strategy, usdc, Contract, strategist, ibUSDC, ibDAI, live_dai_comp_strategy, live_vault, ychad):
    vault = live_vault
    strategy = live_strategy

    vault_dai = Contract.from_explorer('0x19D3364A399d251E894aC732651be8B0E4e85001')
    strategy_dai = Contract.from_explorer('0x7D960F3313f3cB1BBB6BF67419d303597F3E2Fa8')
    live_dai_comp_strategy = Contract.from_explorer('0x4031afd3B0F71Bace9181E554A9E680Ee4AbE7dF')

    vault_usdc = Contract.from_explorer('0x5f18C75AbDAe578b483E5F43f12a39cF75b973a9')
    strategy_usdc = Contract.from_explorer('0x86Aa49bf28d03B1A4aBEb83872cFC13c89eB4beD')
    live_usdc_comp_strategy = Contract.from_explorer('0x4D7d4485fD600c61d840ccbeC328BfD76A050F87')

    vault_dai.updateStrategyDebtRatio(live_dai_comp_strategy, 8_800, {'from': ychad})
    vault_dai.addStrategy(strategy_dai, 1_000, 0, 1000, {"from": ychad})

    vault_usdc.updateStrategyDebtRatio(live_usdc_comp_strategy, 8_800, {'from': ychad})
    vault_usdc.addStrategy(strategy_usdc, 1_000, 0, 1000, {"from": ychad})


    live_dai_comp_strategy.harvest({'from': ychad})
    live_dai_comp_strategy.harvest({'from': ychad})
    live_usdc_comp_strategy.harvest({'from': ychad})
    live_usdc_comp_strategy.harvest({'from': ychad})

    strategy_usdc.harvest({'from': ychad})
    strategy_dai.harvest({'from': ychad})
    print(ibUSDC.balanceOf(strategy_usdc))
    print(usdc.balanceOf(strategy_usdc))

    print(ibDAI.balanceOf(strategy_dai))
    print(currency.balanceOf(strategy_dai))

    genericStateOfStrat(strategy_usdc, usdc, vault_usdc)
    genericStateOfStrat(strategy_dai, currency, vault_dai)

def test_live_add_usdc(currency,Strategy, live_strategy, Contract, usdc, strategist, ibUSDC, live_usdc_comp_strategy, live_vault_usdc, ychad):
    vault = live_vault_usdc
    strategy = strategist.deploy(Strategy, vault, ibUSDC)
    currency = usdc
    

    vault.updateStrategyDebtRatio(live_usdc_comp_strategy, 8_800, {'from': ychad})
    vault.addStrategy(strategy, 1_000, 0, 1000, {"from": ychad})
    live_usdc_comp_strategy.harvest({'from': ychad})
    live_usdc_comp_strategy.harvest({'from': ychad})


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
