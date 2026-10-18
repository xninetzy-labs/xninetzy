from __future__ import annotations

from dataclasses import dataclass, field

EVENT_SIZE = (36, 36)
GATEWAY_SIZE = (50, 50)
ACTIVITY_SIZE = (100, 80)
POOL_ORIGIN = (160, 80)
LANE_HEADER = 30
COLUMN_WIDTH = 180
ROW_HEIGHT = 120
LANE_PADDING = 20
POOL_PADDING = 40
BACK_EDGE_BAND = 50
EVENT_TAGS = frozenset({"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent"})
GATEWAY_TAGS = frozenset({"exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway", "complexGateway"})


@dataclass(frozen=True, slots=True)
class Box:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2


@dataclass(slots=True)
class LayoutInput:
    node_ids: list[str]
    tags: dict[str, str]
    flows: list[tuple[str, str, str]]
    lane_of: dict[str, str] = field(default_factory=dict)
    lane_order: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LayoutResult:
    pool: Box
    lanes: dict[str, Box]
    nodes: dict[str, Box]
    edges: dict[str, list[tuple[int, int]]]
    ranks: dict[str, int]


def node_size(tag: str) -> tuple[int, int]:
    if tag in EVENT_TAGS:
        return EVENT_SIZE
    if tag in GATEWAY_TAGS:
        return GATEWAY_SIZE
    return ACTIVITY_SIZE


def _adjacency(node_ids: list[str], flows: list[tuple[str, str, str]]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    known = set(node_ids)
    outgoing: dict[str, list[str]] = {n: [] for n in node_ids}
    incoming: dict[str, list[str]] = {n: [] for n in node_ids}
    for _fid, source, target in flows:
        if source in known and target in known:
            outgoing[source].append(target)
            incoming[target].append(source)
    return outgoing, incoming


def _back_edges(node_ids: list[str], outgoing: dict[str, list[str]], incoming: dict[str, list[str]], tags: dict[str, str]) -> set[tuple[str, str]]:
    back: set[tuple[str, str]] = set()
    state: dict[str, int] = {}
    roots = [n for n in node_ids if tags.get(n) == "startEvent"] + [n for n in node_ids if not incoming[n]] + list(node_ids)
    for root in roots:
        if state.get(root):
            continue
        stack: list[tuple[str, int]] = [(root, 0)]
        state[root] = 1
        while stack:
            node, index = stack.pop()
            children = outgoing[node]
            if index < len(children):
                stack.append((node, index + 1))
                child = children[index]
                if state.get(child) == 1:
                    back.add((node, child))
                elif not state.get(child):
                    state[child] = 1
                    stack.append((child, 0))
            else:
                state[node] = 2
    return back


def _ranks(node_ids: list[str], outgoing: dict[str, list[str]], incoming: dict[str, list[str]], back: set[tuple[str, str]]) -> dict[str, int]:
    forward_in: dict[str, list[str]] = {n: [s for s in incoming[n] if (s, n) not in back] for n in node_ids}
    ranks: dict[str, int] = {}
    remaining = {n: len(forward_in[n]) for n in node_ids}
    ready = [n for n in node_ids if remaining[n] == 0]
    for node in ready:
        ranks[node] = 0
    queue = list(ready)
    while queue:
        node = queue.pop(0)
        for child in outgoing[node]:
            if (node, child) in back:
                continue
            ranks[child] = max(ranks.get(child, 0), ranks[node] + 1)
            remaining[child] -= 1
            if remaining[child] == 0:
                queue.append(child)
    for node in node_ids:
        ranks.setdefault(node, 0)
    return ranks


def _free_slot(used: set[int], preferred: int) -> int:
    for distance in range(len(used) + 2):
        for candidate in (preferred + distance, preferred - distance):
            if candidate >= 0 and candidate not in used:
                return candidate
    return max(used) + 1


def _slots(node_ids: list[str], lane_of: dict[str, str], ranks: dict[str, int], incoming: dict[str, list[str]]) -> dict[str, int]:
    slots: dict[str, int] = {}
    order = sorted(node_ids, key=lambda n: (ranks[n], node_ids.index(n)))
    taken: dict[tuple[str, int], set[int]] = {}
    for node in order:
        lane = lane_of[node]
        preds = [slots[p] for p in incoming[node] if p in slots and lane_of.get(p) == lane and ranks[p] < ranks[node]]
        preferred = round(sum(preds) / len(preds)) if preds else 0
        used = taken.setdefault((lane, ranks[node]), set())
        slot = _free_slot(used, preferred)
        used.add(slot)
        slots[node] = slot
    return slots


def compute_layout(data: LayoutInput) -> LayoutResult:
    node_ids = list(dict.fromkeys(data.node_ids))
    outgoing, incoming = _adjacency(node_ids, data.flows)
    back = _back_edges(node_ids, outgoing, incoming, data.tags)
    ranks = _ranks(node_ids, outgoing, incoming, back)

    lane_order = list(data.lane_order) or ["__pool__"]
    lane_of = {n: data.lane_of.get(n) if data.lane_of.get(n) in lane_order else lane_order[-1] for n in node_ids}
    slots = _slots(node_ids, lane_of, ranks, incoming)

    max_rank = max(ranks.values(), default=0)
    lane_rows = {lane: 1 + max((slots[n] for n in node_ids if lane_of[n] == lane), default=0) for lane in lane_order}
    band = BACK_EDGE_BAND if back else 0
    pool_x, pool_y = POOL_ORIGIN
    lane_x = pool_x + LANE_HEADER
    width = LANE_HEADER + POOL_PADDING * 2 + (max_rank + 1) * COLUMN_WIDTH
    lanes: dict[str, Box] = {}
    top = pool_y
    for lane in lane_order:
        height = lane_rows[lane] * ROW_HEIGHT + LANE_PADDING * 2 + band
        lanes[lane] = Box(lane_x, top, width - LANE_HEADER, height)
        top += height
    pool = Box(pool_x, pool_y, width, top - pool_y)

    nodes: dict[str, Box] = {}
    for node in node_ids:
        w, h = node_size(data.tags.get(node, "task"))
        lane_box = lanes[lane_of[node]]
        column_left = lane_x + POOL_PADDING + ranks[node] * COLUMN_WIDTH
        row_top = lane_box.y + LANE_PADDING + slots[node] * ROW_HEIGHT
        nodes[node] = Box(column_left + (COLUMN_WIDTH - w) // 2, row_top + (ROW_HEIGHT - h) // 2, w, h)

    edges: dict[str, list[tuple[int, int]]] = {}
    for flow_id, source, target in data.flows:
        if source not in nodes or target not in nodes:
            continue
        edges[flow_id] = _route(nodes, lanes, lane_of, ranks, data.tags, source, target, (source, target) in back)
    return LayoutResult(pool=pool, lanes=lanes, nodes=nodes, edges=edges, ranks=ranks)


def _route(
    nodes: dict[str, Box],
    lanes: dict[str, Box],
    lane_of: dict[str, str],
    ranks: dict[str, int],
    tags: dict[str, str],
    source: str,
    target: str,
    is_back: bool,
) -> list[tuple[int, int]]:
    s, t = nodes[source], nodes[target]
    if source == target:
        return [(s.right, s.center_y), (s.right + 30, s.center_y), (s.right + 30, s.bottom + 30), (s.center_x, s.bottom + 30), (s.center_x, s.bottom)]
    if is_back:
        lane = lanes[lane_of[source]]
        low = max(box.bottom for name, box in nodes.items() if lane_of[name] == lane_of[source])
        route_y = min(low + 25, lane.bottom - 10)
        return [(s.center_x, s.bottom), (s.center_x, route_y), (t.center_x, route_y), (t.center_x, t.bottom)]
    if tags.get(source) in GATEWAY_TAGS and s.center_y != t.center_y and t.x > s.right:
        exit_y = s.y if t.center_y < s.center_y else s.bottom
        return [(s.center_x, exit_y), (s.center_x, t.center_y), (t.x, t.center_y)]
    if s.center_y == t.center_y:
        blocked = [
            name for name, box in nodes.items()
            if name not in (source, target) and ranks[source] < ranks[name] < ranks[target] and box.y < s.center_y < box.bottom
        ]
        if not blocked:
            return [(s.right, s.center_y), (t.x, t.center_y)]
        lane = lanes[lane_of[source]]
        corridor = lane.y + LANE_PADDING // 2
        return [(s.right, s.center_y), (s.right + 20, s.center_y), (s.right + 20, corridor), (t.x - 20, corridor), (t.x - 20, t.center_y), (t.x, t.center_y)]
    middle = s.right + max(20, (t.x - s.right) // 2)
    return [(s.right, s.center_y), (middle, s.center_y), (middle, t.center_y), (t.x, t.center_y)]
