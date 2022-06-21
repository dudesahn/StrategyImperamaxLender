import brownie
from brownie import chain, Contract
import math
import pytest


# customize and check our allocations
def test_custom_allocations(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2000, 0, 4000, 4000]
    tx = strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # can't set for less than the pools we have or less than 10k total
    new_allocations_wrong = [2000, 2000]
    with brownie.reverts():
        strategy.manuallySetAllocations(new_allocations_wrong, {"from": gov})
    new_allocations_wrong = [2000, 2000, 5000, 500]
    with brownie.reverts():
        strategy.manuallySetAllocations(new_allocations_wrong, {"from": gov})

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our current allocations:", allocations)

    # sleep for a day and harvest
    chain.sleep(86400)
    chain.mine(1)
    strategy.harvest({"from": gov})


# add a pair
def test_add_pair(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    extra,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # add a pool
    to_add = extra
    strategy.addTarotPool(to_add, {"from": gov})

    # can't add a pool that already exists
    with brownie.reverts():
        strategy.addTarotPool(to_add, {"from": gov})

    # can't add a pool with the wrong underlying
    to_add = "0xE0d10cEfc6CDFBBde41A12C8BBe9548587568329"  # FTM-TAROT LP (TAROT side)
    with brownie.reverts():
        strategy.addTarotPool(to_add, {"from": gov})

    # set our custom allocations
    new_allocations = [2000, 2000, 4000, 1000, 1000]
    tx = strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our current allocations:", allocations)

    # sleep for a day and harvest
    chain.sleep(86400)
    chain.mine(1)
    strategy.harvest({"from": gov})


# do this to test how far we can push the strategy; will we run out of gas?
@pytest.mark.skip_coverage
def test_add_max_pairs(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    extra,
):

    # only do this test for WFTM :)
    if token.address == "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83":
        ## deposit to the vault after approving
        startingWhale = token.balanceOf(whale)
        token.approve(vault, 2**256 - 1, {"from": whale})
        vault.deposit(amount, {"from": whale})
        chain.sleep(1)
        strategy.harvest({"from": gov})
        chain.sleep(1)

        # add a pool
        to_add = [
            "0x3dA659961cFB2B3E7b167b6d0761d6Ecb5926422",
            "0x7B501aA0Ffb85171c94366db113119cdfAF7b5F5",
            "0x5dd76071F7b5F4599d4F2B7c08641843B746ace9",
            "0x8C97Dcb6a6b08E8bEECE3D75e918FbC076C094ab",
            "0x1CeE4Fd447D7Ce967FddAE4b7DA872A3a1d04F4B",
            "0x845b1619eB0C7C0F9bc7d5494a0b332f6D8Fd4f6",
            "0x7A7dd36BCca42952CC1E67BcA1Be44097fF5b644",
            "0xD05f23002f6d09Cf7b643B69F171cc2A3EAcd0b3",
            "0xbeB8c1266B6a561F2f10B2d242628D7Ed4bA458e",
            "0x604ea00f00C25747d369D9D114590a483e23ff48",
            "0x4e4a8AE836cBE9576113706e166ae1194A7113E6",
            "0xB566727F4edF30bA13939E304d828e30d4063C59",
            "0xDf79EA5d777F28cAb9fD42ACda6208a228c71B59",
            "0xf63D4894c605C246fBe238514355E3cD9680CFF0",
            "0x7D0Eb2b3EDeC482c86e0d588a0f1b3A36b99D336",
            "0xeaAb0Eb61326499a4BC79eCDbC6F3BB17B323dd6",
        ]
        for x in to_add:
            strategy.addTarotPool(x, {"from": gov})

        # set our custom allocations
        new_allocations = [
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
            500,
        ]
        tx_1 = strategy.manuallySetAllocations(new_allocations, {"from": gov})

        # check allocations
        allocations = strategy.getCurrentPoolAllocations({"from": whale})
        print("These are our current allocations:", allocations)

        # sleep for a day and harvest
        chain.sleep(86400)
        chain.mine(1)
        tx_2 = strategy.harvest({"from": gov})
        chain.sleep(86400)
        chain.mine(1)

        tx_3 = vault.withdraw({"from": whale})
        assert token.balanceOf(whale) > startingWhale
        profits = (token.balanceOf(whale) - startingWhale) / 1e18
        print("Profits for our whale in 24 hours:", profits)
        print(
            "Gas used:",
            "Manual Allocation:",
            tx_1.gas_used,
            "Harvest:",
            tx_2.gas_used,
            "Withdrawal from all:",
            tx_3.gas_used,
        )
    else:
        print("We only run this test with WFTM")


# remove a pair whenever it doesn't have any locked debt
def test_remove_pair_free(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2000, 2000, 3000, 3000]
    tx = strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # record our positions
    pos_0 = strategy.pools(0)

    # remove a pair!
    to_remove = pos_0
    strategy.attemptToRemovePool(to_remove, {"from": gov})

    # sleep for a day and harvest
    chain.sleep(86400)
    chain.mine(1)
    strategy.harvest({"from": gov})


# deposit to pools, manually send out free liquidity from these pools to lock our funds up to simulate high utilization, then try to remove the pairs.
def test_remove_pair_locked(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations before we do anything stupid:", allocations)

    # check our free want
    new_want = token.balanceOf(strategy)
    print("Want before exploit:", new_want / (10 ** token.decimals()))
    print(
        "Total estimated assets before exploit:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)
    exchange_rates = []
    balances = []
    poolBalances = []
    totalBalances = []
    for x in order:
        pool = Contract(x)
        rate = pool.exchangeRateLast() / 1e18
        exchange_rates.append(rate)
        amount = pool.balanceOf(strategy.address) / 1e18
        balances.append(amount)
        poolBalance = token.balanceOf(pool) / 1e18
        poolBalances.append(poolBalance)
        totalBalance = pool.totalBalance() / 1e18
        totalBalances.append(totalBalance)

    print("Pool exchange rate:", exchange_rates)
    print("Pool WFTM Balance:", poolBalances)
    print("Pool TotalBalance:", totalBalances)
    print("Strategy bToken Balances:", balances)

    # have two of the bTokens send away almost all of the free liquidity
    sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
    to_send = token.balanceOf(sentient_pool_1) * 0.9999
    before = token.balanceOf(sentient_pool_1)
    token.transfer(gov, to_send, {"from": sentient_pool_1})
    after = token.balanceOf(sentient_pool_1)
    assert after < before
    print("\nNew balance of pool 1:", after / (10 ** token.decimals()))

    # send all of this one
    sentient_pool_2 = accounts.at(strategy.pools(2), force=True)
    to_send = token.balanceOf(sentient_pool_2) * 0.99999
    before = token.balanceOf(sentient_pool_2)
    token.transfer(gov, to_send, {"from": sentient_pool_2})
    after = token.balanceOf(sentient_pool_2)
    assert after < before
    print("New balance of pool 2:", after / (10 ** token.decimals()))

    # update the pools
    pool_1 = Contract(strategy.pools(0))
    pool_2 = Contract(strategy.pools(2))
    pool_1.sync({"from": whale})
    pool_2.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining these pools:", pool_1.address, pool_2.address)

    ######## POOLS REKT #########

    # check our new balances
    new_balance = pool_1.totalBalance() / (10 ** token.decimals())
    print(
        "New Pool 1 balance",
    )

    # check pool utilizations, assert that 0 and 2 have gone up
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[2] > old_utes[2]
    assert utes[0] > old_utes[0]
    print("Pool utilizations after force increase:", utes)

    ######## TRY TO REMOVE REKT POOL #1 #########

    # remove a pair! this one has low liquidity!
    to_remove = strategy.pools(2)
    strategy.attemptToRemovePool(to_remove, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the first -failed- removal:", allocations)

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)
    exchange_rates = []
    balances = []
    poolBalances = []
    totalBalances = []
    for x in order:
        pool = Contract(x)
        rate = pool.exchangeRateLast() / 1e18
        exchange_rates.append(rate)
        amount = pool.balanceOf(strategy.address) / 1e18
        balances.append(amount)
        poolBalance = token.balanceOf(pool) / 1e18
        poolBalances.append(poolBalance)
        totalBalance = pool.totalBalance() / 1e18
        totalBalances.append(totalBalance)

    print("Pool exchange rate:", exchange_rates)
    print("Pool WFTM Balance:", poolBalances)
    print("Pool TotalBalance:", totalBalances)
    print("Strategy bToken Balances:", balances)

    # the pool shouldn't actually be removed
    assert len(strategy.getPools()) == 4

    # check our free want
    new_want = token.balanceOf(strategy)
    print("\nLoose want after first removal:", new_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )
    print(
        "Strategy Debt:",
        vault.strategies(strategy.address)["totalDebt"] / (10 ** token.decimals()),
    )

    # sleep for a day and harvest, turn off health checks since low liq = high yield
    chain.sleep(86400)
    chain.mine(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    first = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the first harvest:", allocations)
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )
    print(
        "Strategy Debt:",
        vault.strategies(strategy.address)["totalDebt"] / (10 ** token.decimals()),
    )

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)
    exchange_rates = []
    balances = []
    poolBalances = []
    totalBalances = []
    for x in order:
        pool = Contract(x)
        rate = pool.exchangeRateLast() / 1e18
        exchange_rates.append(rate)
        amount = pool.balanceOf(strategy.address) / 1e18
        balances.append(amount)
        poolBalance = token.balanceOf(pool) / 1e18
        poolBalances.append(poolBalance)
        totalBalance = pool.totalBalance() / 1e18
        totalBalances.append(totalBalance)

    print("Pool exchange rate:", exchange_rates)
    print("Pool WFTM Balance:", poolBalances)
    print("Pool TotalBalance:", totalBalances)
    print("Strategy bToken Balances:", balances)

    ######## TRY TO REMOVE REKT POOL #2 #########
    # something goes wrong here because we re-allocate our WFTM to a rekt pool before we remove it

    # remove a pair! this is our pair with 0 assets free, the final position.
    to_remove = strategy.pools(2)
    strategy.attemptToRemovePool(to_remove, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print(
        "\nThese are our allocations after the second removal, shouldn't work:",
        allocations,
    )

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)
    exchange_rates = []
    balances = []
    poolBalances = []
    totalBalances = []
    for x in order:
        pool = Contract(x)
        rate = pool.exchangeRateLast() / 1e18
        exchange_rates.append(rate)
        amount = pool.balanceOf(strategy.address) / 1e18
        balances.append(amount)
        poolBalance = token.balanceOf(pool) / 1e18
        poolBalances.append(poolBalance)
        totalBalance = pool.totalBalance() / 1e18
        totalBalances.append(totalBalance)

    print("Pool exchange rate:", exchange_rates)
    print("Pool WFTM Balance:", poolBalances)
    print("Pool TotalBalance:", totalBalances)
    print("Strategy bToken Balances:", balances)

    # the pool shouldn't actually be removed
    assert len(strategy.getPools()) == 4

    # check our free want
    newest_want = token.balanceOf(strategy)
    print("\nLoose want after second removal:", newest_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )
    print(
        "Strategy Debt:",
        vault.strategies(strategy.address)["totalDebt"] / (10 ** token.decimals()),
    )

    # sleep for a day and harvest
    chain.sleep(86400)
    chain.mine(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the second harvest:", allocations)

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)
    exchange_rates = []
    balances = []
    poolBalances = []
    totalBalances = []
    for x in order:
        pool = Contract(x)
        rate = pool.exchangeRateLast() / 1e18
        exchange_rates.append(rate)
        amount = pool.balanceOf(strategy.address) / 1e18
        balances.append(amount)
        poolBalance = token.balanceOf(pool) / 1e18
        poolBalances.append(poolBalance)
        totalBalance = pool.totalBalance() / 1e18
        totalBalances.append(totalBalance)

    print("Pool exchange rate:", exchange_rates)
    print("Pool WFTM Balance:", poolBalances)
    print("Pool TotalBalance:", totalBalances)
    print("Strategy bToken Balances:", balances)

    pool_1.exchangeRate({"from": whale})
    pool_2.exchangeRate({"from": whale})
    chain.sleep(1)
    chain.mine(1)

    print("\nNew exchange rate:", pool_2.exchangeRateLast() / (10 ** token.decimals()))
    print("Vault share price:", vault.pricePerShare() / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    ######## REMOVE A NON-REKT POOL #########

    # remove a pair! this one should remove just fine. positions 2 and 3 will be our high util pairs
    to_remove = strategy.pools(1)
    strategy.attemptToRemovePool(to_remove, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print(
        "\nThese are our allocations after the final removal (that should work):",
        allocations,
    )

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)
    exchange_rates = []
    balances = []
    poolBalances = []
    totalBalances = []
    for x in order:
        pool = Contract(x)
        rate = pool.exchangeRateLast() / 1e18
        exchange_rates.append(rate)
        amount = pool.balanceOf(strategy.address) / 1e18
        balances.append(amount)
        poolBalance = token.balanceOf(pool) / 1e18
        poolBalances.append(poolBalance)
        totalBalance = pool.totalBalance() / 1e18
        totalBalances.append(totalBalance)

    print("Pool exchange rate:", exchange_rates)
    print("Pool WFTM Balance:", poolBalances)
    print("Pool TotalBalance:", totalBalances)
    print("Strategy bToken Balances:", balances)

    # the pool should be removed
    assert len(strategy.getPools()) == 3

    # check our free want
    newer_want = token.balanceOf(strategy)
    print("\nLoose want after third removal:", newer_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )
    print("Staked Balance:", strategy.stakedBalance() / (10 ** token.decimals()))
    print(
        "Strategy Debt:",
        vault.strategies(strategy.address)["totalDebt"] / (10 ** token.decimals()),
    )

    # sleep for a day and harvest, high util pools will automatically move to the back
    chain.sleep(86400)
    chain.mine(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    second = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the third harvest:", allocations)
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )
    print("Staked Balance:", strategy.stakedBalance() / (10 ** token.decimals()))
    print(
        "Strategy Debt:",
        vault.strategies(strategy.address)["totalDebt"] / (10 ** token.decimals()),
    )

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)
    exchange_rates = []
    balances = []
    poolBalances = []
    totalBalances = []
    for x in order:
        pool = Contract(x)
        rate = pool.exchangeRateLast() / 1e18
        exchange_rates.append(rate)
        amount = pool.balanceOf(strategy.address) / 1e18
        balances.append(amount)
        poolBalance = token.balanceOf(pool) / 1e18
        poolBalances.append(poolBalance)
        totalBalance = pool.totalBalance() / 1e18
        totalBalances.append(totalBalance)

    print("Pool exchange rate:", exchange_rates)
    print("Pool WFTM Balance:", poolBalances)
    print("Pool TotalBalance:", totalBalances)
    print("Strategy bToken Balances:", balances)


# test that when we have locked pairs and need to reorder, they are tracked properly
def test_remove_pair_locked_reorder(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    tx = strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print(
        "These are our allocations before we do anything stupid (we already manually updated them):",
        allocations,
    )

    # send away almost all of one pool's liquidity
    sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
    to_send = token.balanceOf(sentient_pool_1) * 0.9999
    before = token.balanceOf(sentient_pool_1)
    token.transfer(gov, to_send, {"from": sentient_pool_1})
    after = token.balanceOf(sentient_pool_1)
    assert after < before
    print("New balance of pool 1:", after / (10 ** token.decimals()))

    # update the pools
    pool_1 = Contract(strategy.pools(0))
    pool_1.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining this pool 99%:", pool_1.address)

    # check our new balances
    new_balance = pool_1.totalBalance() / (10 ** token.decimals())
    print(
        "New Pool 1 balance",
    )

    # check pool utilizations, assert that 0 has gone up
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[0] > old_utes[0]
    print("Pool utilizations after force increase:", utes)

    # remove a pair! this one has low liquidity!
    to_remove = strategy.pools(0)
    strategy.attemptToRemovePool(to_remove, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check that we are blocking deposits to our pool we attempted to remove
    assert strategy.preventDeposits(0) == True
    assert strategy.getPools()[0] == sentient_pool_1.address

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the first -failed- removal:", allocations)

    # check pool order, make sure we didn't change things yet
    order = strategy.getPools({"from": whale})
    assert order[0] == sentient_pool_1.address
    print("Pool order:", order)

    # the pool shouldn't actually be removed
    assert len(strategy.getPools()) == 4

    # check our free want
    new_want = token.balanceOf(strategy)
    print("\nWant after 1 removal:", new_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # reorder our pools
    strategy.reorderPools({"from": gov})

    # check that our low util pool is now in last place, and that our preventDeposits went with it
    order = strategy.getPools({"from": whale})
    assert order[3] == sentient_pool_1.address
    assert strategy.preventDeposits(3) == True
    assert strategy.preventDeposits(0) == False
    print("Pool order:", order)

    # send all of this pool's assets so it's 100% utilized
    sentient_pool_2 = accounts.at(strategy.pools(1), force=True)
    to_send = token.balanceOf(sentient_pool_2)
    before = token.balanceOf(sentient_pool_2)
    token.transfer(gov, to_send, {"from": sentient_pool_2})
    after = token.balanceOf(sentient_pool_2)
    assert after < before
    print("New balance of pool 2:", after / (10 ** token.decimals()))

    # update the pools
    pool_2 = Contract(strategy.pools(1))
    pool_2.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining this pool 100%:", pool_2.address)

    # remove a pair! this one has no liquidity
    to_remove = strategy.pools(1)
    strategy.attemptToRemovePool(to_remove, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check that our pool hasn't moved
    order = strategy.getPools({"from": whale})
    assert order[1] == sentient_pool_2.address
    assert strategy.preventDeposits(3) == True
    assert strategy.preventDeposits(1) == True
    print("Pool order:", order)

    # sleep for a day and harvest, turn off health checks since low liq = high yield
    chain.sleep(86400)
    chain.mine(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the first harvest:", allocations)

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)

    # check that our highest util pools are now at the end
    # the second pool should be in last place since we removed 100% of its liq
    order = strategy.getPools({"from": whale})
    assert order[3] == sentient_pool_2.address
    assert order[2] == sentient_pool_1.address
    assert strategy.preventDeposits(3) == True
    assert strategy.preventDeposits(2) == True
    assert strategy.preventDeposits(1) == False
    assert strategy.preventDeposits(0) == False
    print("Pool order:", order)

    # remove a pair! this one should remove just fine. positions 2 and 3 will be our high util pairs
    to_remove = strategy.pools(1)
    strategy.attemptToRemovePool(to_remove, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print(
        "\nThese are our allocations after the second removal (that should work):",
        allocations,
    )

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)

    # the pool should be removed
    assert len(strategy.getPools()) == 3

    # check our free want
    newer_want = token.balanceOf(strategy)
    print("\nWant after 2 removals:", newer_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # sleep for a day and harvest, high util pools will automatically move to the back
    chain.sleep(86400)
    chain.mine(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the second harvest:", allocations)

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)

    # remove a pair! this is our pair with 0 assets free, the final position.
    to_remove = strategy.pools(2)
    strategy.attemptToRemovePool(to_remove, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print(
        "\nThese are our allocations after the third removal, shouldn't work:",
        allocations,
    )

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)

    # the pool shouldn't actually be removed
    assert len(strategy.getPools()) == 3

    # check our free want
    newest_want = token.balanceOf(strategy)
    print("\nWant after 3 removals:", newest_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # sleep for a day and harvest
    chain.sleep(86400)
    chain.mine(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the harvest:", allocations)

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)

    pool_1.exchangeRate({"from": whale})
    pool_2.exchangeRate({"from": whale})
    chain.sleep(1)
    chain.mine(1)

    print("\nNew exchange rate:", pool_2.exchangeRateLast() / (10 ** token.decimals()))

    print("Vault share price:", vault.pricePerShare() / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )


# manually reorder our pools
def test_reorder_pairs(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    tx = strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # record our positions
    pos_0 = strategy.pools(0)
    pos_1 = strategy.pools(1)
    pos_2 = strategy.pools(2)
    pos_3 = strategy.pools(3)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our current allocations:", allocations)

    # check pool order
    first = strategy.getPools({"from": whale})
    print("\nPools before any reorder:", first)

    # first, reorder by utilization automatically based on utilization
    strategy.reorderPools({"from": gov})

    # check pool order, and our utilizations
    second = strategy.getPools({"from": whale})
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[2] > utes[1]
    assert utes[1] > utes[0]
    print("\nPools after auto reorder:", second)
    print("Pool utilizations:", utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our current allocations:", allocations)

    # sleep for a day and harvest
    chain.sleep(86400)
    chain.mine(1)
    strategy.harvest({"from": gov})

    # check pool order
    third = strategy.getPools({"from": whale})
    print("\nPools after manual reorder:", third)

    # sleep for a day and harvest
    chain.sleep(86400)
    chain.mine(1)
    strategy.harvest({"from": gov})

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our current allocations:", allocations)
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # check that we don't have any free want
    starting_want = token.balanceOf(strategy)
    assert starting_want == 0

    # remove a pair!
    to_remove = strategy.pools(2)
    strategy.attemptToRemovePool(to_remove, {"from": gov})

    # check our free want
    new_want = token.balanceOf(strategy)
    print("\nWant after 1 removal:", new_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our current allocations:", allocations)

    # remove another pair!
    to_remove = strategy.pools(1)
    strategy.attemptToRemovePool(to_remove, {"from": gov})

    # check our free want
    newer_want = token.balanceOf(strategy)
    print("\nWant after 2 removals:", newer_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our current allocations:", allocations)

    # remove another pair!
    to_remove = strategy.pools(1)
    strategy.attemptToRemovePool(to_remove, {"from": gov})

    # check our free want
    newer_want = token.balanceOf(strategy)
    print("\nWant after 3 removals:", newer_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our current allocations:", allocations)

    # reorder pools with only 1 pool
    strategy.reorderPools({"from": gov})

    # turn off reorder
    strategy.setReorder(False, {"from": gov})

    # sleep for a day and harvest
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})

    # check our free want
    new_want = token.balanceOf(strategy)
    print("\nWant after 2 removals and harvest:", new_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our current allocations:", allocations)


# operate the strategy like normal, but with some of the assets locked in a pool
def test_high_utilization(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    print("Starting Whale:", startingWhale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    tx = strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations before we do anything stupid:", allocations)

    # have two of the bTokens send away almost all of the free liquidity
    sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
    to_send = token.balanceOf(sentient_pool_1) * 0.9999
    before = token.balanceOf(sentient_pool_1)
    token.transfer(gov, to_send, {"from": sentient_pool_1})
    after = token.balanceOf(sentient_pool_1)
    assert after < before
    print("New balance of pool 1:", after / (10 ** token.decimals()))

    # send all of this one
    sentient_pool_2 = accounts.at(strategy.pools(2), force=True)
    to_send = token.balanceOf(sentient_pool_2)
    before = token.balanceOf(sentient_pool_2)
    token.transfer(gov, to_send, {"from": sentient_pool_2})
    after = token.balanceOf(sentient_pool_2)
    assert after < before
    print("New balance of pool 2:", after / (10 ** token.decimals()))

    # update the pools
    pool_1 = Contract(strategy.pools(0))
    pool_2 = Contract(strategy.pools(2))
    pool_1.sync({"from": whale})
    pool_2.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining these pools:", pool_1.address, pool_2.address)

    # check our new balances
    new_balance = pool_1.totalBalance() / (10 ** token.decimals())
    print(
        "New Pool 1 balance",
    )

    # check pool utilizations, assert that 0 and 2 have gone up
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[2] > old_utes[2]
    assert utes[0] > old_utes[0]
    print("Pool utilizations after force increase:", utes)

    # try out a full withdrawal, we should have to take a loss
    loss_okay = 10000
    max_uint = 2**256 - 1

    # this should revert since the whale would take a loss from the withdrawal
    with brownie.reverts():
        tx = vault.withdraw(max_uint, whale, loss_okay, {"from": whale})


# ensure that we can't remove all funds from our pools, and try to manually allocate them
def test_high_utilization_manual_allocation(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    print("Starting Whale:", startingWhale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    tx = strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations before we do anything stupid:", allocations)

    # have two of the bTokens send away almost all of the free liquidity
    sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
    to_send = token.balanceOf(sentient_pool_1) * 0.99
    before = token.balanceOf(sentient_pool_1)
    token.transfer(gov, to_send, {"from": sentient_pool_1})
    after = token.balanceOf(sentient_pool_1)
    assert after < before
    print("New balance of pool 1:", after / (10 ** token.decimals()))

    # send all of this one
    sentient_pool_2 = accounts.at(strategy.pools(2), force=True)
    to_send = token.balanceOf(sentient_pool_2) * 0.98
    before = token.balanceOf(sentient_pool_2)
    token.transfer(gov, to_send, {"from": sentient_pool_2})
    after = token.balanceOf(sentient_pool_2)
    assert after < before
    print("New balance of pool 2:", after / (10 ** token.decimals()))

    # update the pools
    pool_1 = Contract(strategy.pools(0))
    pool_2 = Contract(strategy.pools(2))
    pool_1.sync({"from": whale})
    pool_2.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining these pools:", pool_1.address, pool_2.address)

    # check our new balances
    new_balance = pool_1.totalBalance() / (10 ** token.decimals())
    print(
        "New Pool 1 balance",
    )

    # check pool utilizations, assert that 0 and 2 have gone up
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[2] > old_utes[2]
    assert utes[0] > old_utes[0]
    print("Pool utilizations after force increase:", utes)

    # set our custom allocations
    new_allocations = [5000, 50, 4900, 50]
    tx = strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print(
        "These are our allocations after draining and trying to reallocate:",
        allocations,
    )


# moved these two to a new test file since in the old one the last test was randomly failing for seemingly no good reasons, hypothesizing that the file was too long?
# test out withdrawing directly from strategy via gov
def test_emergency_withdraw(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations before we do anything stupid:", allocations)

    # use our emergency withdraw to kill all of our bTokens
    max_uint = 2**256 - 1
    tx = strategy.emergencyWithdraw(max_uint, {"from": gov})

    # check pool utilizations
    new_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations after emergency withdraw:", new_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations after withdrawal:", allocations)


# test if we get small losses from rapidly converting in and out of bTokens
def test_deposit_harvest_withdraw(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    print("Starting Whale:", startingWhale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    harvest = strategy.harvest({"from": gov})
    chain.sleep(1)

    print(
        "Strategy estimated total assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )
    tx = vault.withdraw({"from": whale})

    # Seems that sometimes whale loses 1-2 gwei, sometimes doesn't lose anything
    # these losses occur whenever we don't actually update our exchange rates -> no events fire for them, specifically AccrueInterest event
    # additionally, in these cases, the strategy only thinks it has 99,999.999999... WFTM due to conversion,
    # so when it gets this back, it's not a true loss in the strategy's withdrawal call's eyes
    # this appears to only occur when we don't include any chain.sleep or chain.mine around the harvest call
    net = token.balanceOf(whale) - startingWhale
    if net >= 0:
        print("\nThese are our gains, great than or equal to 0:", net, "wei")
    if net < 0:
        print("\nWe lost a few wei, this many:", net * -1, "wei")

    assert net >= 0  # do this to force a revert so we can debug why we reverted


# do emergency shutdown from vault with a harvest, but with some of the assets locked in a pool
def test_high_utilization_emergency_shutdown_from_vault_harvest(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    print("Starting Whale:", startingWhale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # simulate one day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations before we do anything stupid:", allocations)

    # have two of the bTokens send away almost all of the free liquidity
    sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
    to_send = token.balanceOf(sentient_pool_1) * 0.9999
    before = token.balanceOf(sentient_pool_1)
    token.transfer(gov, to_send, {"from": sentient_pool_1})
    after = token.balanceOf(sentient_pool_1)
    assert after < before
    print("New balance of pool 1:", after / (10 ** token.decimals()))

    # send all of this one
    sentient_pool_2 = accounts.at(strategy.pools(2), force=True)
    to_send = token.balanceOf(sentient_pool_2)
    before = token.balanceOf(sentient_pool_2)
    token.transfer(gov, to_send, {"from": sentient_pool_2})
    after = token.balanceOf(sentient_pool_2)
    assert after < before
    print("New balance of pool 2:", after / (10 ** token.decimals()))

    # update the pools
    pool_1 = Contract(strategy.pools(0))
    pool_2 = Contract(strategy.pools(2))
    pool_1.sync({"from": whale})
    pool_2.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining these pools:", pool_1.address, pool_2.address)

    # check our new balances
    new_balance = pool_1.totalBalance() / (10 ** token.decimals())
    print(
        "New Pool 1 balance",
    )

    # check pool utilizations, assert that 0 and 2 have gone up
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[2] > old_utes[2]
    assert utes[0] > old_utes[0]
    print("Pool utilizations after force increase:", utes)

    # set emergency and exit, then confirm that the strategy has no funds
    vault.setEmergencyShutdown(True, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the first harvest:", allocations)
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )
    print(
        "Strategy Debt:",
        vault.strategies(strategy.address)["totalDebt"] / (10 ** token.decimals()),
    )

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)
    exchange_rates = []
    balances = []
    poolBalances = []
    totalBalances = []
    for x in order:
        pool = Contract(x)
        rate = pool.exchangeRateLast() / 1e18
        exchange_rates.append(rate)
        amount = pool.balanceOf(strategy.address) / 1e18
        balances.append(amount)
        poolBalance = token.balanceOf(pool) / 1e18
        poolBalances.append(poolBalance)
        totalBalance = pool.totalBalance() / 1e18
        totalBalances.append(totalBalance)

    print("Pool exchange rate:", exchange_rates)
    print("Pool WFTM Balance:", poolBalances)
    print("Pool TotalBalance:", totalBalances)
    print("Strategy bToken Balances:", balances)

    # in emergency shutdown, debtOutstanding is set to the full debt balance of the strategy, so this harvest will be removing all funds
    strategy.setDoHealthCheck(False, {"from": gov})
    tx = strategy.harvest({"from": gov})
    print("These is our harvest:", tx.events["Harvested"])
    chain.sleep(1)

    # check our vault share price, it should have gone down to like 0.5
    share_price = vault.pricePerShare()
    print("Share price:", share_price / (10 ** token.decimals()))

    max_uint = 2**256 - 1
    loss_okay = 10000
    tx_2 = vault.withdraw(max_uint, whale, loss_okay, {"from": whale})
    losses = token.balanceOf(whale) - startingWhale
    print("These are our losses:", losses / (10 ** token.decimals()))


# do emergency shutdown from vault without a harvest, but with some of the assets locked in a pool
def test_high_utilization_emergency_shutdown_from_vault_no_harvest(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    print("Starting Whale:", startingWhale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # simulate one day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations before we do anything stupid:", allocations)

    # have two of the bTokens send away almost all of the free liquidity
    sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
    to_send = token.balanceOf(sentient_pool_1) * 0.9999
    before = token.balanceOf(sentient_pool_1)
    token.transfer(gov, to_send, {"from": sentient_pool_1})
    after = token.balanceOf(sentient_pool_1)
    assert after < before
    print("New balance of pool 1:", after / (10 ** token.decimals()))

    # send all of this one
    sentient_pool_2 = accounts.at(strategy.pools(2), force=True)
    to_send = token.balanceOf(sentient_pool_2)
    before = token.balanceOf(sentient_pool_2)
    token.transfer(gov, to_send, {"from": sentient_pool_2})
    after = token.balanceOf(sentient_pool_2)
    assert after < before
    print("New balance of pool 2:", after / (10 ** token.decimals()))

    # update the pools
    pool_1 = Contract(strategy.pools(0))
    pool_2 = Contract(strategy.pools(2))
    pool_1.sync({"from": whale})
    pool_2.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining these pools:", pool_1.address, pool_2.address)

    # check our new balances
    new_balance = pool_1.totalBalance() / (10 ** token.decimals())
    print(
        "New Pool 1 balance",
    )

    # check pool utilizations, assert that 0 and 2 have gone up
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[2] > old_utes[2]
    assert utes[0] > old_utes[0]
    print("Pool utilizations after force increase:", utes)

    # set emergency and exit, then confirm that the strategy has no funds
    vault.setEmergencyShutdown(True, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    max_uint = 2**256 - 1
    loss_okay = 10000
    tx_2 = vault.withdraw(max_uint, whale, loss_okay, {"from": whale})
    losses = token.balanceOf(whale) - startingWhale
    print("These are our whale's losses:", losses / (10 ** token.decimals()))


# do emergency exit from strategy with a harvest, but with some of the assets locked in a pool
def test_high_utilization_emergency_exit_harvest(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    print("Starting Whale:", startingWhale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # simulate one day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations before we do anything stupid:", allocations)

    # have two of the bTokens send away almost all of the free liquidity
    sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
    to_send = token.balanceOf(sentient_pool_1) * 0.9999
    before = token.balanceOf(sentient_pool_1)
    token.transfer(gov, to_send, {"from": sentient_pool_1})
    after = token.balanceOf(sentient_pool_1)
    assert after < before
    print("New balance of pool 1:", after / (10 ** token.decimals()))

    # send all of this one
    sentient_pool_2 = accounts.at(strategy.pools(2), force=True)
    to_send = token.balanceOf(sentient_pool_2)
    before = token.balanceOf(sentient_pool_2)
    token.transfer(gov, to_send, {"from": sentient_pool_2})
    after = token.balanceOf(sentient_pool_2)
    assert after < before
    print("New balance of pool 2:", after / (10 ** token.decimals()))

    # update the pools
    pool_1 = Contract(strategy.pools(0))
    pool_2 = Contract(strategy.pools(2))
    pool_1.sync({"from": whale})
    pool_2.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining these pools:", pool_1.address, pool_2.address)

    # check our new balances
    new_balance = pool_1.totalBalance() / (10 ** token.decimals())
    print(
        "New Pool 1 balance",
    )

    # check pool utilizations, assert that 0 and 2 have gone up
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[2] > old_utes[2]
    assert utes[0] > old_utes[0]
    print("Pool utilizations after force increase:", utes)

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # in emergency shutdown, debtOutstanding is set to the full debt balance of the strategy, so this harvest will be removing all funds
    strategy.setDoHealthCheck(False, {"from": gov})
    tx = strategy.harvest({"from": gov})
    print("These is our harvest:", tx.events["Harvested"])
    chain.sleep(1)

    # check our vault share price, it should have gone down to like 0.5
    share_price = vault.pricePerShare()
    print("Share price:", share_price / (10 ** token.decimals()))

    max_uint = 2**256 - 1
    loss_okay = 10000
    tx_2 = vault.withdraw(max_uint, whale, loss_okay, {"from": whale})
    losses = token.balanceOf(whale) - startingWhale
    print("These are our losses:", losses / (10 ** token.decimals()))


# do emergency exit from strategy without a harvest, but with some of the assets locked in a pool
def test_high_utilization_emergency_exit_no_harvest(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    print("Starting Whale:", startingWhale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # simulate one day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations before we do anything stupid:", allocations)

    # have two of the bTokens send away almost all of the free liquidity
    sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
    to_send = token.balanceOf(sentient_pool_1) * 0.9999
    before = token.balanceOf(sentient_pool_1)
    token.transfer(gov, to_send, {"from": sentient_pool_1})
    after = token.balanceOf(sentient_pool_1)
    assert after < before
    print("New balance of pool 1:", after / (10 ** token.decimals()))

    # send all of this one
    sentient_pool_2 = accounts.at(strategy.pools(2), force=True)
    to_send = token.balanceOf(sentient_pool_2)
    before = token.balanceOf(sentient_pool_2)
    token.transfer(gov, to_send, {"from": sentient_pool_2})
    after = token.balanceOf(sentient_pool_2)
    assert after < before
    print("New balance of pool 2:", after / (10 ** token.decimals()))

    # update the pools
    pool_1 = Contract(strategy.pools(0))
    pool_2 = Contract(strategy.pools(2))
    pool_1.sync({"from": whale})
    pool_2.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining these pools:", pool_1.address, pool_2.address)

    # check our new balances
    new_balance = pool_1.totalBalance() / (10 ** token.decimals())
    print(
        "New Pool 1 balance",
    )

    # check pool utilizations, assert that 0 and 2 have gone up
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[2] > old_utes[2]
    assert utes[0] > old_utes[0]
    print("Pool utilizations after force increase:", utes)

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    max_uint = 2**256 - 1
    loss_okay = 10000
    tx_2 = vault.withdraw(max_uint, whale, loss_okay, {"from": whale})
    losses = token.balanceOf(whale) - startingWhale
    print("These are our whale's losses:", losses / (10 ** token.decimals()))


# deposit to pools, manually send out free liquidity from these pools to lock our funds up to simulate high utilization, then send it back
def test_remove_pair_locked_and_unlock(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    accounts,
):

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set our custom allocations
    new_allocations = [2500, 2500, 2500, 2500]
    tx = strategy.manuallySetAllocations(new_allocations, {"from": gov})

    # check pool utilizations
    old_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations at baseline:", old_utes)

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("These are our allocations before we do anything stupid:", allocations)

    # have two of the bTokens send away almost all of the free liquidity
    sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
    to_send = token.balanceOf(sentient_pool_1) * 0.9999
    before = token.balanceOf(sentient_pool_1)
    token.transfer(gov, to_send, {"from": sentient_pool_1})
    after = token.balanceOf(sentient_pool_1)
    assert after < before
    print("\nNew balance of pool 1:", after / (10 ** token.decimals()))

    # update the pools
    pool_1 = Contract(strategy.pools(0))
    pool_1.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)
    print("We are draining this pool:", pool_1.address)

    # check pool utilizations, assert that 0 and 2 have gone up
    utes = strategy.getEachPoolUtilization({"from": whale})
    assert utes[0] > old_utes[0]
    print("Pool utilizations after force increase:", utes)

    # remove a pair! this one has low liquidity!
    to_remove = strategy.pools(0)
    strategy.attemptToRemovePool(to_remove, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the first -failed- removal:", allocations)

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)

    # the pool shouldn't actually be removed
    assert len(strategy.getPools()) == 4

    # check our free want
    new_want = token.balanceOf(strategy)
    print("\nWant after 1 removal:", new_want / (10 ** token.decimals()))
    print(
        "Total estimated assets:",
        strategy.estimatedTotalAssets() / (10 ** token.decimals()),
    )

    # sleep for a day and harvest, high util pools will automatically move to the back
    chain.sleep(86400)
    chain.mine(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the first harvest:", allocations)

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)

    # send our funds back
    before = token.balanceOf(sentient_pool_1)
    token.transfer(sentient_pool_1, to_send, {"from": gov})
    after = token.balanceOf(sentient_pool_1)
    assert after > before
    print(
        "\nNew balance of pool 1 after returning lost funds:",
        after / (10 ** token.decimals()),
    )

    # update the pool, it should now be in the 4th spot
    pool_4 = Contract(strategy.pools(3))
    pool_4.sync({"from": whale})
    chain.sleep(1)
    chain.mine(1)

    # check pool utilizations
    newest_utes = strategy.getEachPoolUtilization({"from": whale})
    print("Pool utilizations after sending funds back:", newest_utes)

    # try to remove our same pair again, should be in the last position
    to_remove = strategy.pools(3)
    tx = strategy.attemptToRemovePool(to_remove, {"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # the pool should now be removed
    assert len(strategy.getPools()) == 3

    # check allocations
    allocations = strategy.getCurrentPoolAllocations({"from": whale})
    print("\nThese are our allocations after the first -failed- removal:", allocations)

    # check pool order
    order = strategy.getPools({"from": whale})
    print("Pool order:", order)

    # sleep for a day and harvest, see if we lost anything or not
    chain.sleep(86400)
    chain.mine(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    max_uint = 2**256 - 1
    loss_okay = 10000
    tx_2 = vault.withdraw(max_uint, whale, loss_okay, {"from": whale})
    losses = token.balanceOf(whale) - startingWhale
    print(
        "These are our whale's losses, if positive it's gains:",
        losses / (10 ** token.decimals()),
    )


# test how our exchange rate calc compares to tarot's
# def test_exchange_rates(
#     gov,
#     token,
#     vault,
#     strategist,
#     whale,
#     strategy,
#     chain,
#     amount,
#     accounts,
# ):
#
#     ## deposit to the vault after approving
#     startingWhale = token.balanceOf(whale)
#     token.approve(vault, 2**256 - 1, {"from": whale})
#     vault.deposit(amount, {"from": whale})
#     chain.sleep(1)
#     strategy.harvest({"from": gov})
#     chain.sleep(1)
#     old_utes = strategy.getEachPoolUtilization({"from": whale})
#
#     for pool_index in range(4):
#         pool_address = strategy.pools(pool_index)
#         pool_contract = Contract(pool_address)
#         pool_contract.skim(whale, {"from": whale})
#         chain.sleep(1)
#         chain.mine(1)
#
#         tarot_rate = pool_contract.exchangeRateLast({"from": whale})
#         internal_rate = strategy.trueExchangeRate(pool_address)
#
#         print("\nThis is our pool:", pool_address)
#         print("Tarot exchange rate:", tarot_rate / 1e18)
#         print("True exchange rate:", internal_rate / 1e18)
#
#         if tarot_rate == internal_rate:
#             print("\nThe rates are exactly the same 🚀")
#         else:  # for USDC, it seems to lose a bit of precision
#             assert math.isclose(tarot_rate, internal_rate, abs_tol=1e6)
#
#     # sleep for a day and harvest, high util pools will automatically move to the back
#     chain.sleep(86400)
#     tx = strategy.harvest({"from": gov})
#     chain.sleep(1)
#     chain.mine(1)
#
#     for pool_index in range(4):
#         pool_address = strategy.pools(pool_index)
#         pool_contract = Contract(pool_address)
#         pool_contract.skim(whale, {"from": whale})
#         chain.sleep(1)
#         chain.mine(1)
#
#         tarot_rate = pool_contract.exchangeRateLast({"from": whale})
#         internal_rate = strategy.trueExchangeRate(pool_address)
#
#         print("\nThis is our pool:", pool_address)
#         print("Tarot exchange rate:", tarot_rate / 1e18)
#         print("True exchange rate:", internal_rate / 1e18)
#
#         if tarot_rate == internal_rate:
#             print("\nThe rates are exactly the same 🚀")
#         else:  # for USDC, it seems to lose a bit of precision
#             assert math.isclose(tarot_rate, internal_rate, abs_tol=1e6)
#
#     # have one of the bTokens send away almost all of the free liquidity
#     sentient_pool_1 = accounts.at(strategy.pools(0), force=True)
#     to_send = token.balanceOf(sentient_pool_1) * 0.9999
#     before = token.balanceOf(sentient_pool_1)
#     token.transfer(gov, to_send, {"from": sentient_pool_1})
#     after = token.balanceOf(sentient_pool_1)
#     assert after < before
#     print("\nNew balance of pool 1:", after / (10 ** token.decimals()))
#
#     # update the pools
#     pool_1 = Contract(strategy.pools(0))
#     pool_1.sync({"from": whale})
#     chain.sleep(1)
#     chain.mine(1)
#     print("We are draining this pool:", pool_1.address)
#
#     # check pool utilizations, assert that 0 and 2 have gone up
#     utes = strategy.getEachPoolUtilization({"from": whale})
#     assert utes[0] > old_utes[0]
#     print("Pool utilizations after force increase:", utes)
#
#     # sleep for a day and harvest, this will take losses
#     chain.sleep(86400)
#     chain.mine(1)
#     strategy.setDoHealthCheck(False, {"from": gov})
#     tx = strategy.harvest({"from": gov})
#     chain.sleep(1)
#     chain.mine(1)
#
#     for pool_index in range(4):
#         pool_address = strategy.pools(pool_index)
#         pool_contract = Contract(pool_address)
#         pool_contract.skim(whale, {"from": whale})
#         chain.sleep(1)
#         chain.mine(1)
#
#         tarot_rate = pool_contract.exchangeRateLast({"from": whale})
#         internal_rate = strategy.trueExchangeRate(pool_address)
#
#         print("\nThis is our pool:", pool_address)
#         print("Tarot exchange rate:", tarot_rate / 1e18)
#         print("True exchange rate:", internal_rate / 1e18)
#
#         # our rekt pool should be at the back
#         if pool_index == 3:
#             # for the rekt pool, the tarot rate will be the same as if it didn't lose assets, so will be greater than ours
#             assert tarot_rate > internal_rate
#         else:
#             if tarot_rate == internal_rate:
#                 print("\nThe rates are exactly the same 🚀")
#             else:  # for USDC, it seems to lose a bit of precision
#                 assert math.isclose(tarot_rate, internal_rate, abs_tol=1e6)
