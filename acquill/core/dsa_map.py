"""Placement-focused DSA topic graph: topic -> its direct prerequisites.

Order follows college-placement preparation:
Tier 1 (must know) -> Tier 2 (important) -> Tier 3 (top product companies).
"""

import difflib
import re

DSA_PREREQUISITES = {
    # Tier 1 - foundations
    "programming basics": (),
    "time and space complexity": ("programming basics",),
    "recursion": ("programming basics",),
    # Tier 1 - arrays and strings
    "arrays": ("programming basics",),
    "strings": ("arrays",),
    "two pointers": ("arrays",),
    "sliding window": ("two pointers",),
    "prefix sum": ("arrays",),
    "sorting": ("arrays", "time and space complexity", "recursion"),
    "binary search": ("arrays", "sorting"),
    # Tier 1 - hashing
    "hash maps and sets": ("arrays", "time and space complexity"),
    # Tier 1 - linked list, stack, queue
    "linked list": ("arrays", "programming basics"),
    "fast and slow pointers": ("linked list", "two pointers"),
    "stack": ("arrays",),
    "queue": ("arrays",),
    # Tier 1 - trees
    "binary tree": ("recursion", "stack", "linked list"),
    "level-order traversal": ("binary tree", "queue"),
    "binary search tree": ("binary tree", "binary search"),
    # Tier 2
    "backtracking": ("recursion", "arrays"),
    "heap": ("binary tree", "arrays"),
    "top-k problems": ("heap",),
    "greedy basics": ("sorting", "arrays"),
    "graph basics": ("arrays", "linked list", "binary tree"),
    "graph bfs and dfs": ("graph basics", "queue", "recursion"),
    "cycle detection and connected components": ("graph bfs and dfs",),
    "topological sort": ("graph bfs and dfs",),
    "dynamic programming basics": ("recursion", "hash maps and sets"),
    "1d dp": ("dynamic programming basics",),
    "2d dp": ("1d dp",),
    # Tier 3
    "trie": ("binary tree", "strings", "hash maps and sets"),
    "monotonic stack": ("stack", "arrays"),
    "union-find": ("arrays", "binary tree"),
    "dijkstra": ("graph basics", "heap"),
    "longest increasing subsequence": ("1d dp", "binary search"),
    "bit manipulation": ("programming basics",),
}

TOPIC_ALIASES = {
    "big o": "time and space complexity",
    "big-o": "time and space complexity",
    "big o notation": "time and space complexity",
    "complexity": "time and space complexity",
    "time complexity": "time and space complexity",
    "space complexity": "time and space complexity",
    "sorting algorithms": "sorting",
    "hash map": "hash maps and sets",
    "hash maps": "hash maps and sets",
    "hash set": "hash maps and sets",
    "hashmap": "hash maps and sets",
    "hashing": "hash maps and sets",
    "linked lists": "linked list",
    "two-pointer": "two pointers",
    "two pointers technique": "two pointers",
    "sliding window technique": "sliding window",
    "prefix sums": "prefix sum",
    "tree": "binary tree",
    "trees": "binary tree",
    "binary trees": "binary tree",
    "binary tree and traversals": "binary tree",
    "dfs": "binary tree",
    "bfs": "level-order traversal",
    "level order traversal": "level-order traversal",
    "bst": "binary search tree",
    "priority queue": "heap",
    "heap / priority queue": "heap",
    "top k problems": "top-k problems",
    "top-k": "top-k problems",
    "greedy": "greedy basics",
    "greedy algorithms": "greedy basics",
    "graph": "graph basics",
    "graphs": "graph basics",
    "graph representation": "graph basics",
    "bfs and dfs": "graph bfs and dfs",
    "graph traversal": "graph bfs and dfs",
    "cycle detection": "cycle detection and connected components",
    "connected components": "cycle detection and connected components",
    "topo sort": "topological sort",
    "dp": "dynamic programming basics",
    "dynamic programming": "dynamic programming basics",
    "memoization": "dynamic programming basics",
    "1-d dp": "1d dp",
    "2-d dp": "2d dp",
    "union find": "union-find",
    "disjoint set": "union-find",
    "disjoint set union": "union-find",
    "dijkstra's algorithm": "dijkstra",
    "shortest path": "dijkstra",
    "lis": "longest increasing subsequence",
}


def _normalize(name):
    """Lowercase, collapse whitespace, drop parentheticals."""
    key = " ".join((name or "").lower().split())
    key = re.sub(r"\(.*?\)", " ", key)
    return " ".join(key.split())


def canonical(name):
    """Map free text to a topic in the graph, or None if it is not DSA."""
    key = _normalize(name)
    if not key:
        return None
    key = TOPIC_ALIASES.get(key, key)
    if key in DSA_PREREQUISITES:
        return key
    close = difflib.get_close_matches(key, DSA_PREREQUISITES, n=1, cutoff=0.85)
    return close[0] if close else None


def prerequisites(name, depth=1):
    """Direct prerequisites (depth=1) or the full chain (depth=None)."""
    root = canonical(name)
    if not root:
        return []

    seen = set()
    frontier = [root]
    for _ in range(depth or len(DSA_PREREQUISITES)):
        nxt = []
        for topic in frontier:
            for dep in DSA_PREREQUISITES.get(topic, ()):
                if dep not in seen and dep != root:
                    seen.add(dep)
                    nxt.append(dep)
        frontier = nxt
        if not frontier:
            break
    return list(seen)
