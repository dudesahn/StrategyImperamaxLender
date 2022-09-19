import brownie
from brownie import Contract
from brownie import config
import math


def test_remove_from_withdrawal_queue(
    gov,
    token,
    vault,
    whale,
    strategy,
    chain,
    amount,
):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # simulate 1 day of earnings
    chain.sleep(86400)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    before = strategy.estimatedTotalAssets()

    # remove strategy from our queue
    vault.removeStrategyFromQueue(strategy, {"from": gov})
    after = strategy.estimatedTotalAssets()
    assert before == after

    # check that our strategy is no longer in the withdrawal queue's 20 addresses
    addresses = []
    for x in range(19):
        address = vault.withdrawalQueue(x)
        addresses.append(address)
    print(
        "Strategy Address: ",
        strategy.address,
        "\nWithdrawal Queue Addresses: ",
        addresses,
    )
    assert not strategy.address in addresses

    # re-add our strategy to the queue and make sure it still works
    vault.addStrategyToQueue(strategy, {"from": gov})
    after = strategy.estimatedTotalAssets()
    assert before == after

    # simulate 1 day of earnings, make sure we earn something
    chain.sleep(86400)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    after = strategy.estimatedTotalAssets()
    assert after > before

    
