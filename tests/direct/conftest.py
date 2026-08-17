import json


CONTRACT = "contracts/open_world_liveness_switch.py"
BENEFICIARY = "0x000000000000000000000000000000000000bEEF"


def sources_json():
    return json.dumps(
        [
            {
                "id": "github",
                "family": "code",
                "url": "https://example.com/github/alice",
                "criteria": "A commit authored by Alice is visible within the previous 60 days.",
                "identity_anchor": "alice-dev",
            },
            {
                "id": "blog",
                "family": "publishing",
                "url": "https://example.com/blog/alice",
                "criteria": "A blog post attributed to Alice is dated within the previous 90 days.",
                "identity_anchor": "Alice Example Blog",
            },
            {
                "id": "status",
                "family": "owned_domain",
                "url": "https://example.com/alive/alice",
                "criteria": "The owner liveness date on this page is no older than 45 days.",
                "identity_anchor": "alice.example.com",
            },
        ],
        sort_keys=True,
    )


def beneficiaries_json():
    return json.dumps([{"address": BENEFICIARY, "share_bps": 10_000}])


def address_hex(value):
    if hasattr(value, "as_hex"):
        return value.as_hex
    if isinstance(value, bytes):
        return "0x" + value.hex()
    return str(value)


def guardians_json(guardian):
    return json.dumps([address_hex(guardian)])


def source_result(
    source_id,
    status="UNKNOWN",
    coverage="UNAVAILABLE",
    anchor="UNKNOWN",
    observed_at="",
    confidence=0,
    evidence="Source unavailable.",
):
    return {
        "id": source_id,
        "status": status,
        "coverage": coverage,
        "anchor_status": anchor,
        "observed_activity_at": observed_at,
        "evidence": evidence,
        "confidence": confidence,
    }


def active_probe():
    return json.dumps(
        {
            "sources": [
                source_result(
                    "github",
                    "ACTIVE",
                    "COMPLETE",
                    "MATCH",
                    "2026-01-20T12:00:00Z",
                    96,
                    "alice-dev authored commit abc123 on 2026-01-20.",
                ),
                source_result("blog"),
                source_result("status"),
            ]
        },
        sort_keys=True,
    )


def inactive_probe(status_unknown=False):
    blog_status = "UNKNOWN" if status_unknown else "NO_ACTIVITY"
    blog_coverage = "UNAVAILABLE" if status_unknown else "COMPLETE"
    blog_anchor = "UNKNOWN" if status_unknown else "MATCH"
    blog_confidence = 0 if status_unknown else 92
    return json.dumps(
        {
            "sources": [
                source_result(
                    "github",
                    "NO_ACTIVITY",
                    "COMPLETE",
                    "MATCH",
                    "",
                    94,
                    "Complete activity list has no qualifying commit in 60 days.",
                ),
                source_result(
                    "blog",
                    blog_status,
                    blog_coverage,
                    blog_anchor,
                    "",
                    blog_confidence,
                    "Blog unavailable." if status_unknown else "Complete feed has no post in 90 days.",
                ),
                source_result(
                    "status",
                    "NO_ACTIVITY",
                    "COMPLETE",
                    "MATCH",
                    "",
                    95,
                    "The signed liveness date is older than 45 days.",
                ),
            ]
        },
        sort_keys=True,
    )


def inconclusive_same_family_probe():
    data = json.loads(inactive_probe())
    data["sources"][1] = source_result("blog")
    data["sources"][2] = source_result("status")
    return json.dumps(data, sort_keys=True)


def register_mocks(vm, response, comparison="ACCEPT"):
    vm.mock_web(r"example\.com/github/alice", {"status": 200, "body": "alice-dev activity"})
    vm.mock_web(r"example\.com/blog/alice", {"status": 200, "body": "Alice Example Blog feed"})
    vm.mock_web(r"example\.com/alive/alice", {"status": 200, "body": "alice.example.com status"})
    vm.mock_llm(r"OPEN-WORLD LIVENESS PROBE", response)
    vm.mock_llm(r"LIVENESS EVIDENCE CONSENSUS CHECK", comparison)


def deploy_switch(vm, direct_deploy, owner, guardian):
    vm.warp("2026-02-01T00:00:00Z")
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    vm.sender = owner
    contract.register_switch(
        "alice_liveness",
        sources_json(),
        beneficiaries_json(),
        guardians_json(guardian),
        1,
        2,
        2,
        2,
        3600,
        86400,
        "ipfs://bafy-example-encrypted-payload",
        "a" * 64,
    )
    return contract


def arm_switch(vm, contract):
    register_mocks(vm, active_probe())
    contract.probe("alice_liveness")


def warp_after(vm, iso_time):
    vm.clear_mocks()
    vm.warp(iso_time)
