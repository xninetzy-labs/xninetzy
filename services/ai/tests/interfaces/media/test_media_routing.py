import pytest

from app.xninetzy.agent.orchestrator import orchestrator_node


@pytest.mark.asyncio
@pytest.mark.parametrize("metadata_key", ["media", "quotedMedia"])
async def test_attachment_forces_agent_route_without_llm(metadata_key):
    state = {
        "message": "[document uploaded]",
        "sender_name": "User",
        "chat_type": "private",
        "metadata": {
            metadata_key: {
                "hasMedia": True,
                "mediaType": "document",
                "messageId": "m1",
            }
        },
        "messages": [],
    }
    result = await orchestrator_node(state)
    assert result["route"] == "agent"
    assert result["clarification_question"] is None
