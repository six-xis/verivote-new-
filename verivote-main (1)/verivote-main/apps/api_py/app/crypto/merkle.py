from app.crypto.hash_utils import hash_object, sha256_hex


EMPTY_ROOT = sha256_hex("verivote.empty_merkle_root")


def _hash_leaf(leaf: str) -> str:
    return hash_object("verivote.merkle.leaf.v1", leaf)


def _hash_node(left: str, right: str) -> str:
    return hash_object("verivote.merkle.node.v1", [left, right])


def build_merkle_tree(leaves: list[str]) -> list[list[str]]:
    if not leaves:
        return [[EMPTY_ROOT]]

    tree = [[_hash_leaf(leaf) for leaf in leaves]]
    level = tree[0]
    while len(level) > 1:
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1] if index + 1 < len(level) else left
            next_level.append(_hash_node(left, right))
        level = next_level
        tree.append(level)
    return tree


def build_merkle_root(leaves: list[str]) -> str:
    return build_merkle_tree(leaves)[-1][0]


def create_merkle_proof(leaves: list[str], leaf: str) -> list[dict[str, str]]:
    if leaf not in leaves:
        raise ValueError("leaf is not present in the Merkle tree")
    if not leaves:
        raise ValueError("cannot create a Merkle proof for an empty tree")

    tree = build_merkle_tree(leaves)
    index = leaves.index(leaf)
    proof: list[dict[str, str]] = []

    for level in tree[:-1]:
        if index % 2 == 0:
            sibling_index = index + 1 if index + 1 < len(level) else index
            proof.append({"sibling": level[sibling_index], "position": "right"})
        else:
            sibling_index = index - 1
            proof.append({"sibling": level[sibling_index], "position": "left"})
        index //= 2

    return proof


def verify_merkle_proof(leaf: str, proof: list[dict], root: str) -> bool:
    current = _hash_leaf(leaf)

    for item in proof:
        sibling = item.get("sibling")
        position = item.get("position")
        if not isinstance(sibling, str) or position not in {"left", "right"}:
            return False

        if position == "left":
            current = _hash_node(sibling, current)
        else:
            current = _hash_node(current, sibling)

    return current == root


def merkle_root(leaves: list[str]) -> str:
    return build_merkle_root(leaves)
