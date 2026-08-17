import json

from tests.direct.conftest import (
    BENEFICIARY,
    CONTRACT,
    active_probe,
    arm_switch,
    beneficiaries_json,
    deploy_switch,
    guardians_json,
    inactive_probe,
    inconclusive_same_family_probe,
    register_mocks,
    source_result,
    sources_json,
    warp_after,
)


def test_positive_consensus_arms_switch(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    arm_switch(direct_vm, contract)
    state = contract.get_switch("alice_liveness")
    assert state["status"] == "MONITORING"
    assert state["last_confirmed_active"] > 0
    probe = contract.get_probe("alice_liveness", 1)
    assert probe["aggregate"] == "CONFIRMED_ACTIVE"
    assert probe["transition"] == "UNARMED->MONITORING"


def test_unarmed_switch_cannot_progress_on_absence(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    register_mocks(direct_vm, inactive_probe())
    contract.probe("alice_liveness")
    state = contract.get_switch("alice_liveness")
    assert state["status"] == "UNARMED"
    assert state["negative_streak"] == 0
    assert contract.get_probe("alice_liveness", 1)["transition"] == "UNARMED_STAYS_SAFE"


def test_unknown_sources_never_count_as_inactivity(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    arm_switch(direct_vm, contract)

    warp_after(direct_vm, "2026-02-01T01:00:01Z")
    register_mocks(direct_vm, inconclusive_same_family_probe())
    contract.probe("alice_liveness")

    state = contract.get_switch("alice_liveness")
    assert state["status"] == "MONITORING"
    assert state["negative_streak"] == 0
    probe = contract.get_probe("alice_liveness", 2)
    assert probe["aggregate"] == "INCONCLUSIVE"
    assert probe["unknown_count"] == 2


def test_negative_quorum_requires_distinct_source_families(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.warp("2026-02-01T00:00:00Z")
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    direct_vm.sender = direct_alice
    definitions = json.loads(sources_json())
    definitions[1]["family"] = "code"
    contract.register_switch(
        "alice_liveness",
        json.dumps(definitions),
        beneficiaries_json(),
        guardians_json(direct_bob),
        1,
        2,
        2,
        2,
        3600,
        86400,
        "ipfs://payload",
        "a" * 64,
    )
    arm_switch(direct_vm, contract)

    response = json.loads(inactive_probe())
    response["sources"][2] = source_result("status")
    warp_after(direct_vm, "2026-02-01T01:00:01Z")
    register_mocks(direct_vm, json.dumps(response))
    contract.probe("alice_liveness")

    probe = contract.get_probe("alice_liveness", 2)
    assert probe["inactive_count"] == 2
    assert probe["inactive_family_count"] == 1
    assert probe["aggregate"] == "INCONCLUSIVE"
    assert contract.get_switch("alice_liveness")["negative_streak"] == 0


def test_consecutive_diverse_negative_probes_start_grace(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    arm_switch(direct_vm, contract)

    warp_after(direct_vm, "2026-02-01T01:00:01Z")
    register_mocks(direct_vm, inactive_probe())
    contract.probe("alice_liveness")
    assert contract.get_switch("alice_liveness")["negative_streak"] == 1

    warp_after(direct_vm, "2026-02-01T02:00:02Z")
    register_mocks(direct_vm, inactive_probe())
    contract.probe("alice_liveness")
    state = contract.get_switch("alice_liveness")
    assert state["status"] == "GRACE"
    assert state["release_eligible_at"] == state["grace_started_at"] + 86400


def test_active_evidence_cancels_grace(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    arm_switch(direct_vm, contract)
    for instant in ("2026-02-01T01:00:01Z", "2026-02-01T02:00:02Z"):
        warp_after(direct_vm, instant)
        register_mocks(direct_vm, inactive_probe())
        contract.probe("alice_liveness")
    assert contract.get_switch("alice_liveness")["status"] == "GRACE"

    warp_after(direct_vm, "2026-02-01T03:00:03Z")
    register_mocks(direct_vm, active_probe())
    contract.probe("alice_liveness")
    state = contract.get_switch("alice_liveness")
    assert state["status"] == "MONITORING"
    assert state["negative_streak"] == 0
    assert state["release_eligible_at"] == 0


def test_release_requires_fresh_negative_probe_after_grace(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    arm_switch(direct_vm, contract)
    for instant in ("2026-02-01T01:00:01Z", "2026-02-01T02:00:02Z"):
        warp_after(direct_vm, instant)
        register_mocks(direct_vm, inactive_probe())
        contract.probe("alice_liveness")

    warp_after(direct_vm, "2026-02-02T02:00:03Z")
    assert contract.get_switch("alice_liveness")["status"] == "GRACE"
    register_mocks(direct_vm, inactive_probe())
    contract.probe("alice_liveness")

    state = contract.get_switch("alice_liveness")
    assert state["status"] == "RELEASED"
    authorization = contract.authorization("alice_liveness", BENEFICIARY)
    assert authorization["authorized"] is True
    assert authorization["share_bps"] == 10_000
    assert authorization["payload_uri"].startswith("ipfs://")


def test_guardian_can_extend_grace_only_once(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    arm_switch(direct_vm, contract)
    for instant in ("2026-02-01T01:00:01Z", "2026-02-01T02:00:02Z"):
        warp_after(direct_vm, instant)
        register_mocks(direct_vm, inactive_probe())
        contract.probe("alice_liveness")

    before = contract.get_switch("alice_liveness")["release_eligible_at"]
    direct_vm.sender = direct_bob
    contract.request_grace_extension("alice_liveness")
    after = contract.get_switch("alice_liveness")["release_eligible_at"]
    assert after == before + 86400

    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("grace extension already used"):
        contract.request_grace_extension("alice_liveness")


def test_public_probe_is_rate_limited(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    arm_switch(direct_vm, contract)
    with direct_vm.expect_revert("probe interval has not elapsed"):
        contract.probe("alice_liveness")
