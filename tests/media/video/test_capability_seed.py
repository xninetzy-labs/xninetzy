from __future__ import annotations



def test_seed_media_capabilities_is_idempotent():
    from xninetzy.context.media.video import seed_media_capabilities

    r1 = seed_media_capabilities()
    r2 = seed_media_capabilities()
    assert (r1.inserted + r2.inserted) >= 1 or r1.skipped >= 1
    assert (r2.inserted + r1.inserted) >= 1 or r2.skipped >= 1
    assert r1.skipped + r2.skipped >= r1.inserted + r2.inserted
    assert all(
        c.startswith("media.video")
        for c in (
            r1.capabilities if r1.inserted > 0 else r2.capabilities
        )
    )


def test_capability_graph_resolves_video_queries():
    from xninetzy.context.media.video import seed_media_capabilities
    from xninetzy.context.capability_graph.semantic_match import match_capability

    seed_media_capabilities()

    cases = {
        "video": ("media.video",),
        "screen capture": ("media.video.capture",),
        "render": ("media.video.render",),
        "tutorial": ("media.video.tutorial",),
        "dev_video": ("media.video.development",),
    }
    for query, expected_substrings in cases.items():
        matches = match_capability(query, top_k=5)
        assert matches, f"no matches for {query!r}"
        capabilities = [m.capability for m in matches]
        assert any(
            any(sub in cap for sub in expected_substrings)
            for cap in capabilities
        ), (
            f"query={query!r} expected one of {expected_substrings}; "
            f"got {capabilities}"
        )


def test_media_nodes_listed():
    from xninetzy.context.media.video import (
        MEDIA_CAPABILITY_NODES, seed_media_capabilities,
    )
    seed_media_capabilities()
    capabilities = {n.capability for n in MEDIA_CAPABILITY_NODES}
    assert "media.video" in capabilities
    assert "media.video.render" in capabilities
    assert "media.video.motion" in capabilities
    assert "media.video.capture" in capabilities
    assert "media.video.edit" in capabilities
    assert "media.video.project_demo" in capabilities
    assert "media.video.tutorial" in capabilities
    assert "media.video.development" in capabilities
