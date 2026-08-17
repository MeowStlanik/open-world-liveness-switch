"""Network smoke test. Run explicitly with: gltest tests/integration -v -s."""

import json

import pytest
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


@pytest.mark.integration
def test_deploy_register_and_read(default_account):
    factory = get_contract_factory("OpenWorldLivenessSwitch")
    contract = factory.deploy()
    sources = json.dumps(
        [
            {
                "id": "code",
                "family": "code",
                "url": "https://example.com/code",
                "criteria": "A dated contribution exists within the previous sixty days.",
                "identity_anchor": "example-user",
            },
            {
                "id": "blog",
                "family": "publishing",
                "url": "https://example.com/blog",
                "criteria": "A dated article exists within the previous ninety days.",
                "identity_anchor": "Example Blog",
            },
            {
                "id": "status",
                "family": "domain",
                "url": "https://example.com/status",
                "criteria": "The public status date is no older than forty-five days.",
                "identity_anchor": "example.com",
            },
        ]
    )
    beneficiaries = json.dumps(
        [{"address": "0x000000000000000000000000000000000000bEEF", "share_bps": 10000}]
    )
    guardians = json.dumps(["0x000000000000000000000000000000000000cAFE"])
    tx = contract.register_switch(
        args=[
            "integration_switch",
            sources,
            beneficiaries,
            guardians,
            1,
            2,
            2,
            2,
            86400,
            604800,
            "ipfs://payload",
            "a" * 64,
        ]
    ).transact()
    assert tx_execution_succeeded(tx)
    state = contract.get_switch(args=["integration_switch"]).call()
    assert state["status"] == "UNARMED"
