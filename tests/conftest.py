import pytest
from brownie import config

@pytest.fixture
def andre(accounts):
    # Andre, giver of tokens, and maker of yield
    yield accounts[0]

@pytest.fixture
def currency(interface):
    #this one is curvesteth
    #yield interface.ERC20('0x06325440D014e39736583c165C2963BA99fAf14E')
    #this is dai
    yield interface.ERC20('0x6B175474E89094C44Da98b954EedeAC495271d0F')

@pytest.fixture
def usdc(interface):
    #this one is curvesteth
    #yield interface.ERC20('0x06325440D014e39736583c165C2963BA99fAf14E')
    #this is dai
    yield interface.ERC20('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')

@pytest.fixture
def weth(interface):
    yield interface.ERC20('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')

@pytest.fixture
def alpha(interface):
    yield interface.ERC20('0xa1faa113cbE53436Df28FF0aEe54275c13B40975')

@pytest.fixture
def whale(accounts, web3, currency, chain):
    #big binance7 wallet
    #acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    #big binance8 wallet
    #acc = accounts.at('0x006d0f31a00e1f9c017ab039e9d0ba699433a28c', force=True)
    acc = accounts.at('0xC3D03e4F041Fd4cD388c549Ee2A29a9E5075882f', force=True)
    assert currency.balanceOf(acc)  > 0
    
    yield acc

@pytest.fixture
def samdev(accounts):

    acc = accounts.at('0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0', force=True)
    yield acc

@pytest.fixture
def strategistMs(accounts):
    strategistMs = accounts.at('0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7', force=True)
    yield strategistMs

@pytest.fixture
def ibDAI(interface):
    yield interface.ISafeBox('0xee8389d235E092b2945fE363e97CDBeD121A0439')

@pytest.fixture
def ibUSDC(interface):
    yield interface.ISafeBox('0x08bd64BFC832F1C2B3e07e634934453bA7Fa2db2')

@pytest.fixture
def cdai(interface):
    yield interface.CErc20I('0x8e595470Ed749b85C6F7669de83EAe304C2ec68F')

@pytest.fixture
def cusdc(interface):
    yield interface.CErc20I('0x76Eb2FE28b36B3ee97F3Adae0C69606eeDB2A37c')

@pytest.fixture
def cweth(interface):
    yield interface.CErc20I('0x41c84c0e2EE0b740Cf0d31F63f3B6F627DC6b393')

@pytest.fixture
def ychad(accounts):
    acc = accounts.at('0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52', force=True)
    yield acc

@pytest.fixture
def token(andre, Token):
    yield andre.deploy(Token)


@pytest.fixture
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts[1]


@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract


@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]


@pytest.fixture
def vault(pm, gov, rewards, guardian, currency):
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault

@pytest.fixture
def Vault(pm, gov, rewards, guardian, currency):
    Vault = pm(config["dependencies"][0]).Vault
    yield Vault

@pytest.fixture
def strategist(accounts):
    # You! Our new Strategist!
    yield accounts[3]


@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]

@pytest.fixture
def live_dai_comp_strategy(Strategy):
    strategy = Strategy.at('0x4031afd3B0F71Bace9181E554A9E680Ee4AbE7dF')

    yield strategy
@pytest.fixture
def live_usdc_comp_strategy(Strategy):
    strategy = Strategy.at('0x4D7d4485fD600c61d840ccbeC328BfD76A050F87')

    yield strategy


@pytest.fixture
def live_strategy(Strategy):
    strategy = Strategy.at('0x7D960F3313f3cB1BBB6BF67419d303597F3E2Fa8')

    yield strategy

@pytest.fixture
def live_strategy_usdc(Strategy):
    strategy = Strategy.at('0x86Aa49bf28d03B1A4aBEb83872cFC13c89eB4beD')

    yield strategy


@pytest.fixture
def live_vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at('0x19D3364A399d251E894aC732651be8B0E4e85001')
    yield vault

@pytest.fixture
def live_vault_usdt(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at('0xAf322a2eDf31490250fdEb0D712621484b09aBB6')
    yield vault

@pytest.fixture
def live_vault_usdc(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at('0x5f18C75AbDAe578b483E5F43f12a39cF75b973a9')
    yield vault

@pytest.fixture
def strategy(strategist, keeper, vault,ibDAI, Strategy):
    strategy = strategist.deploy(Strategy, vault, ibDAI)
    yield strategy

@pytest.fixture
def zapper(strategist, ZapSteth):
    zapper = strategist.deploy(ZapSteth)
    yield zapper


@pytest.fixture
def nocoiner(accounts):
    # Has no tokens (DeFi is a ponzi scheme!)
    yield accounts[5]


@pytest.fixture
def pleb(accounts, andre, token, vault):
    # Small fish in a big pond
    a = accounts[6]
    # Has 0.01% of tokens (heard about this new DeFi thing!)
    bal = token.totalSupply() // 10000
    token.transfer(a, bal, {"from": andre})
    # Unlimited Approvals
    token.approve(vault, 2 ** 256 - 1, {"from": a})
    # Deposit half their stack
    vault.deposit(bal // 2, {"from": a})
    yield a


@pytest.fixture
def chad(accounts, andre, token, vault):
    # Just here to have fun!
    a = accounts[7]
    # Has 0.1% of tokens (somehow makes money trying every new thing)
    bal = token.totalSupply() // 1000
    token.transfer(a, bal, {"from": andre})
    # Unlimited Approvals
    token.approve(vault, 2 ** 256 - 1, {"from": a})
    # Deposit half their stack
    vault.deposit(bal // 2, {"from": a})
    yield a


@pytest.fixture
def greyhat(accounts, andre, token, vault):
    # Chaotic evil, will eat you alive
    a = accounts[8]
    # Has 1% of tokens (earned them the *hard way*)
    bal = token.totalSupply() // 100
    token.transfer(a, bal, {"from": andre})
    # Unlimited Approvals
    token.approve(vault, 2 ** 256 - 1, {"from": a})
    # Deposit half their stack
    vault.deposit(bal // 2, {"from": a})
    yield a


