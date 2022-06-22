import pytest
from brownie import config, Wei, Contract, chain, web3
import requests

# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


# change autouse to True if we want to use this fork to help debug tests
@pytest.fixture(scope="module", autouse=False)
def tenderly_fork(web3, chain):
    fork_base_url = "https://simulate.yearn.network/fork"
    payload = {"network_id": str(chain.id)}
    resp = requests.post(fork_base_url, headers={}, json=payload)
    fork_id = resp.json()["simulation_fork"]["id"]
    fork_rpc_url = f"https://rpc.tenderly.co/fork/{fork_id}"
    print(fork_rpc_url)
    tenderly_provider = web3.HTTPProvider(fork_rpc_url, {"timeout": 600})
    web3.provider = tenderly_provider
    print(f"https://dashboard.tenderly.co/yearn/yearn-web/fork/{fork_id}")


# this is the amount of funds we have our whale deposit. adjust this as needed based on their wallet balance
@pytest.fixture(scope="module")
def amount(token):
    amount = 100_000 * (10 ** token.decimals())
    yield amount


# this is the name we want to give our strategy
@pytest.fixture(scope="module")
def strategy_name():
    strategy_name = "StrategyTarotLenderWFTM"
    yield strategy_name


###### UPDATE THESE BELOW BASED ON THE WANT WE ARE TESTING ######


@pytest.fixture(scope="module")
def whale(accounts):  # WFTM
    # Totally in it for the tech
    # Update this with a large holder of your want token (the largest EOA holder of LP)
    whale = accounts.at("0x39B3bd37208CBaDE74D0fcBDBb12D606295b430a", force=True)
    yield whale


# Define relevant tokens and contracts in this section
@pytest.fixture(scope="module")
def token():  # WFTM
    # this should be the address of the ERC-20 used by the strategy/vault
    token_address = "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83"
    yield Contract(token_address)


# These are the pools we will lend to (WFTM vault)
@pytest.fixture(scope="module")
def pools():
    pools = [
        "0x93a97db4fEA1d053C31f0B658b0B87f4b38e105d",  # FTM-SPIRIT Spirit
        "0x6e11aaD63d11234024eFB6f7Be345d1d5b8a8f38",  # USDC-FTM Spirit
        "0x5B80b6e16147bc339e22296184F151262657A327",  # FTM-CRV Spooky
        "0xFf0BC3c7df0c247E5ce1eA220c7095cE1B6Dc745",  # FTM-USDC Spooky
    ]
    yield pools


# This is an extra pool we will test adding
@pytest.fixture(scope="module")
def extra():  # WFTM vault
    extra = "0x5dd76071F7b5F4599d4F2B7c08641843B746ace9"  # TAROT
    yield extra


# to test USDC, uncomment four below and comment four above. for WFTM, leave as-is


# @pytest.fixture(scope="module")
# def whale(accounts):  # USDC
#     # Totally in it for the tech
#     # Update this with a large holder of your want token (the largest EOA holder of LP)
#     whale = accounts.at("0xE45Ac34E528907d0A0239ab5Db507688070B20bf", force=True)
#     yield whale
#
#
# # Define relevant tokens and contracts in this section
# @pytest.fixture(scope="module")
# def token():  # USDC
#     # this should be the address of the ERC-20 used by the strategy/vault
#     token_address = "0x04068DA6C83AFCFA0e13ba15A6696662335D5B75"
#     yield Contract(token_address)
#
#
# # These are the pools we will lend to (USDC vault)
# @pytest.fixture(scope="module")
# def pools():
#     pools = [
#         "0x710675A9c8509D3dF254792C548555D3D0a69494",  # WFTM
#         "0xb7FA3710A69487F37ae91D74Be55578d1353f9df",  # WFTM
#         "0x7623ABCB2A3Da6bB14Bbb713B58c9B11Fc9713B1",  # FUSDT
#         "0xD8339e66Eeb1762E699b3f0eF694269658e2421f",  # miMATIC
#     ]
#     yield pools
#
#
# # This is an extra pool we will test adding
# @pytest.fixture(scope="module")
# def extra():  # USDC vault
#     extra = "0xb91e78E239ddF33DE24e32424DecfFa036E770e4"  # This is WFTM
#     yield extra


###### UPDATE THESE ABOVE BASED ON THE WANT WE ARE TESTING ######


# this is the amount of funds we are okay leaving in our strategy due to unrealized profit or conversion between bTokens
@pytest.fixture(scope="module")
def dust(token):
    dust = 0.1 * (10 ** token.decimals())
    yield dust


@pytest.fixture(scope="module")
def healthCheck():
    yield Contract("0xf13Cd6887C62B5beC145e30c38c4938c5E627fe0")


# zero address
@pytest.fixture(scope="module")
def zero_address():
    zero_address = "0x0000000000000000000000000000000000000000"
    yield zero_address


@pytest.fixture(scope="module")
def farmed():
    yield Contract("0x34D33dc8Ac6f1650D94A7E9A972B47044217600b")


# Define any accounts in this section
# for live testing, governance is the strategist MS; we will update this before we endorse
# normal gov is ychad, 0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52
@pytest.fixture(scope="module")
def gov(accounts):
    yield accounts.at("0xC0E2830724C946a6748dDFE09753613cd38f6767", force=True)


@pytest.fixture(scope="module")
def strategist_ms(accounts):
    # like governance, but better
    yield accounts.at("0x72a34AbafAB09b15E7191822A679f28E067C4a16", force=True)


@pytest.fixture(scope="module")
def keeper(accounts):
    yield accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)


@pytest.fixture(scope="module")
def rewards(accounts):
    yield accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)


@pytest.fixture(scope="module")
def guardian(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def management(accounts):
    yield accounts[3]


@pytest.fixture(scope="module")
def strategist(accounts):
    yield accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)


@pytest.fixture(scope="module")
def other_vault_strategy():
    # this is fantom curve vault strat
    other_vault_strategy = "0xcF3b91D83cD5FE15269E6461098fDa7d69138570"
    yield Contract(other_vault_strategy)


# # list any existing strategies here
# @pytest.fixture(scope="module")
# def LiveStrategy_1():
#     yield Contract("0xC1810aa7F733269C39D640f240555d0A4ebF4264")


# use this if you need to deploy the vault
@pytest.fixture(scope="function")
def vault(pm, gov, rewards, guardian, management, token, chain):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    chain.sleep(1)
    yield vault


# use this if your vault is already deployed
# @pytest.fixture(scope="function")
# def vault(pm, gov, rewards, guardian, management, token, chain):
#     vault = Contract("0x497590d2d57f05cf8B42A36062fA53eBAe283498")
#     yield vault


# replace the first value with the name of your strategy
@pytest.fixture(scope="function")
def strategy(
    StrategyImperamaxLender,
    strategist,
    keeper,
    vault,
    gov,
    guardian,
    token,
    healthCheck,
    chain,
    strategy_name,
    strategist_ms,
    pools,
):
    # make sure to include all constructor parameters needed here
    strategy = strategist.deploy(
        StrategyImperamaxLender,
        vault,
        strategy_name,
    )
    strategy.setKeeper(keeper, {"from": gov})
    # set our management fee to zero so it doesn't mess with our profit checking
    vault.setManagementFee(0, {"from": gov})
    # add our new strategy
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    strategy.setHealthCheck(healthCheck, {"from": gov})
    strategy.setDoHealthCheck(True, {"from": gov})

    # add our pools to the strategy
    for pool in pools:
        strategy.addTarotPool(pool, {"from": gov})

    # set our custom allocations (use this and comment it out to test 1 vs 4 pools allocated to)
    # realistically, here should add the deposit and harvest step beforehand, as-is we don't split up
    new_allocations = [2500, 2500, 2500, 2500]
    strategy.manuallySetAllocations(new_allocations, {"from": gov})
    yield strategy


# use this if your strategy is already deployed
# @pytest.fixture(scope="function")
# def strategy():
#     # parameters for this are: strategy, vault, max deposit, minTimePerInvest, slippage protection (10000 = 100% slippage allowed),
#     strategy = Contract("0xC1810aa7F733269C39D640f240555d0A4ebF4264")
#     yield strategy
