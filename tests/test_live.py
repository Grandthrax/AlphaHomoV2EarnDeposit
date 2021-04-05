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

def test_opsss_lvie(currency,live_strategy, chain,live_vault, whale,gov, samdev,strategist, interface):
    strategy = live_strategy
    vault = live_vault
    strategist = samdev
    gov = samdev

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    #whalebefore = currency.balanceOf(whale)
   # whale_deposit  = 100 *1e18
    #vault.deposit(whale_deposit, {"from": whale})
    #strategy.harvest({'from': strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    #chain.sleep(2592000)
    #chain.mine(1)

    strategy.harvest({'from': strategist})
    steth = interface.ERC20('0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84')

    print("steth = ", steth.balanceOf(strategy)/1e18)
    print("eth = ", strategy.balance()/1e18)

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-1000*1e18)*12)/(1000*1e18)))

   # vault.withdraw({"from": whale})
    print("\nWithdraw")
    user = accounts.at('0x014de182c147f8663589d77eadb109bf86958f13', force=True)
    vault.withdraw({"from": user})
    print(currency.balanceOf(user)/1e18)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
  # print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e18)


def test_migrate_live(currency,Strategy, accounts, ychad, live_strategy,live_vault,ibDAI, chain, whale,samdev, interface):
    strategy = live_strategy
    vault = live_vault
    strategist = samdev
    gov = ychad

    #strategy.harvest({'from': strategist})

    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)


    strategy2 = strategist.deploy(Strategy, vault, ibDAI)
    vault.migrateStrategy(strategy, strategy2, {'from': gov})

    print("\nWithdraw")
    user = accounts.at('0x014de182c147f8663589d77eadb109bf86958f13', force=True)
    vault.withdraw({"from": user})
    print("DAI out:", currency.balanceOf(user)/1e18)
    print("Vault tokens left:",vault.balanceOf(user)/1e18)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfStrat(strategy2, currency, vault)
    genericStateOfVault(vault, currency)


def test_distributor(currency, accounts,Contract, chain, whale,gov, samdev,strategist, interface, alpha, AlphaDistributor):
    ms = accounts.at("0x16388463d60ffe0661cf7f1f31a7d658ac790ff7", force=True)
    vault = Contract("0x19D3364A399d251E894aC732651be8B0E4e85001", owner=ms)
    strategy = Contract("0x7D960F3313f3cB1BBB6BF67419d303597F3E2Fa8", owner=ms)
    currency = interface.ERC20(vault.token())
    genericStateOfStrat(strategy, currency, vault)
    print("Alpha in ms:", alpha.balanceOf(ms)/1e18)

    distributer = samdev.deploy(AlphaDistributor)
    alpha.transfer(distributer, alpha.balanceOf(ms)/2, {'from': ms})
    distributer.sellDai(alpha.balanceOf(distributer), {'from': samdev})
    genericStateOfStrat(strategy, currency, vault)


    strategy = Contract(distributer.usdcStrat())
    vault = Contract(strategy.vault())
    currency = interface.ERC20(vault.token())
    genericStateOfStrat(strategy, currency, vault)

    alpha.transfer(distributer, alpha.balanceOf(ms), {'from': ms})
    distributer.sellUsdc(alpha.balanceOf(distributer), {'from': samdev})
    genericStateOfStrat(strategy, currency, vault)




