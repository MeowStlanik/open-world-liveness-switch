import json

from tests.direct.conftest import (
    active_probe,
    deploy_switch,
    inactive_probe,
    register_mocks,
)


def test_validator_accepts_semantically_equivalent_evidence(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    register_mocks(direct_vm, active_probe())
    contract.probe("alice_liveness")

    equivalent = json.loads(active_probe())
    equivalent["sources"][0]["evidence"] = (
        "Commit abc123 is listed for alice-dev with an authored date of 20 January 2026."
    )
    direct_vm.clear_mocks()
    register_mocks(direct_vm, json.dumps(equivalent), "ACCEPT")
    assert direct_vm.run_validator(index=0) is True


def test_validator_rejects_status_disagreement(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    register_mocks(direct_vm, active_probe())
    contract.probe("alice_liveness")

    direct_vm.clear_mocks()
    register_mocks(direct_vm, inactive_probe())
    assert direct_vm.run_validator(index=0) is False


def test_validator_rejects_semantic_evidence_disagreement(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    register_mocks(direct_vm, active_probe())
    contract.probe("alice_liveness")

    direct_vm.clear_mocks()
    register_mocks(direct_vm, active_probe(), "REJECT")
    assert direct_vm.run_validator(index=0) is False


def test_validator_rejects_malformed_leader_result(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    register_mocks(direct_vm, active_probe())
    contract.probe("alice_liveness")
    malformed = json.dumps({"sources": [{"id": "github", "status": "ACTIVE"}]})
    assert direct_vm.run_validator(index=0, leader_result=malformed) is False


def test_no_activity_requires_complete_coverage(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    bad = json.loads(inactive_probe())
    bad["sources"][0]["coverage"] = "PARTIAL"
    register_mocks(direct_vm, json.dumps(bad))
    with direct_vm.expect_revert("accepted probe failed invariant checks"):
        contract.probe("alice_liveness")


def test_active_requires_matching_identity_anchor(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_switch(direct_vm, direct_deploy, direct_alice, direct_bob)
    bad = json.loads(active_probe())
    bad["sources"][0]["anchor_status"] = "MISMATCH"
    register_mocks(direct_vm, json.dumps(bad))
    with direct_vm.expect_revert("accepted probe failed invariant checks"):
        contract.probe("alice_liveness")
