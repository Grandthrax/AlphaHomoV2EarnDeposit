from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

def test_opsss_lvie(currency,Strategy, chain,live_vault_usdt, whale,gov,ibUSDT, samdev,strategist, interface, accounts):

    strategist = samdev
    vault = live_vault_usdt

    strategy = strategist.deploy(Strategy, vault, ibUSDT)

    gov = samdev



    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    #whalebefore = currency.balanceOf(whale)
   # whale_deposit  = 100 *1e18
    #vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    chain.sleep(2592000)
    chain.mine(1)

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