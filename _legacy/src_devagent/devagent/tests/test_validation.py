import json

from dev_agent.core.router import Router


def test_invalid_action(router: Router):
    command = json.dumps({
        "tool": "filesystem",
        "args": {
            "action": "delete_everything"
        }
    })

    result = router.execute(command)

    assert result["status"] == "error"
    assert result["error"] == "Validation failed"