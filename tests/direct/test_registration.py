import json

from tests.direct.conftest import (
    BENEFICIARY,
    CONTRACT,
    address_hex,
    beneficiaries_json,
    deploy_switch,
    guardians_json,
    sources_json,
)


def register(contract, guardian, sources=None, beneficiaries=None, **overrides):
    args = {
        "sources_json": sources or sources_json(),
        "beneficiaries_json": beneficiaries or beneficiaries_json(),
        "guardians_json": guardians_json(guardian),
        "active_quorum": 1,
        "inactive_quorum": 2,
        "inactive_family_quorum": 2,
        "consecutive_rounds_required": 2,
        "min_probe_seconds": 3600,
        "grace_seconds": 86400,
        "payload_uri": "ipfs://payload",
        "payload_sha256": "b" * 64,
    }
    args.update(overrides)
    contract.register_switch("new_switch", *args.values())


def test_registers_fail_safe_switch(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    state = contract.get_switch("alice_liveness")
    assert state["owner"].lower() == address_hex(direct_alice).lower()
    assert state["status"] == "UNARMED"
    assert state["inactive_quorum"] == 2
    assert state["inactive_family_quorum"] == 2
    assert state["consecutive_rounds_required"] == 2

    source = contract.get_source("alice_liveness", "github")
    assert source["family"] == "code"
    assert source["last_status"] == ""

    authorization = contract.authorization("alice_liveness", BENEFICIARY)
    assert authorization["authorized"] is False
    assert authorization["share_bps"] == 10_000
    assert authorization["payload_uri"] == ""


def test_rejects_correlated_source_set(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    direct_vm.sender = direct_alice
    sources = json.loads(sources_json())
    for source in sources:
        source["family"] = "social"
    with direct_vm.expect_revert("sources must span at least 2 families"):
        register(contract, direct_bob, sources=json.dumps(sources))


def test_rejects_duplicate_source_id(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    direct_vm.sender = direct_alice
    sources = json.loads(sources_json())
    sources[1]["id"] = sources[0]["id"]
    with direct_vm.expect_revert("duplicate source id"):
        register(contract, direct_bob, sources=json.dumps(sources))


def test_rejects_bad_beneficiary_total(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    direct_vm.sender = direct_alice
    beneficiaries = json.dumps([{"address": BENEFICIARY, "share_bps": 9000}])
    with direct_vm.expect_revert("beneficiary shares must total 10000 bps"):
        register(contract, direct_bob, beneficiaries=beneficiaries)


def test_rejects_weak_thresholds(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("inactive_quorum must be 2..source count"):
        register(contract, direct_bob, inactive_quorum=1)
    with direct_vm.expect_revert("consecutive rounds must be 2..10"):
        register(contract, direct_bob, consecutive_rounds_required=1)


def test_only_owner_can_cancel_and_only_before_arming(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only switch owner"):
        contract.cancel_unarmed("alice_liveness")
    direct_vm.sender = direct_alice
    contract.cancel_unarmed("alice_liveness")
    assert contract.get_switch("alice_liveness")["status"] == "CANCELLED"
