import collections
from typing import Tuple, Optional, Sequence, Dict, Set, List


def decode_item_maybe_with_metadata(s: str) -> Tuple[str, Optional[int]]:
    assert len(s) > 0
    if "#" in s:
        item_type, metadata_str = s.split("#")
        if len(item_type) == 0:
            raise ValueError(f"invalid item_type '{item_type}' in '{s}'")
        metadata = int(metadata_str)
        if metadata not in range(16):
            raise ValueError(f"invalid metadata {metadata} in '{s}'")
        return item_type, int(metadata_str)
    return s, None


def encode_item_with_metadata(item_type: str, metadata: Optional[int]) -> str:
    assert len(item_type) > 0
    if metadata is None:
        return item_type
    else:
        assert isinstance(metadata, int)
        return f"{item_type}#{metadata}"


def error_on_malformed_item_list(
    item_list: Sequence[str], special_items: Sequence[str]
):
    """Check that there are no duplicate item IDs, overlapping item IDs
    (e.g. "planks#2" and "planks"), that special item types don't come with metadata
    constraints (e.g. "air#0" should not be valid).
    """
    map_type_to_metadata: Dict[str, Set[Optional[int]]] = collections.defaultdict(set)
    for s in item_list:
        item_type, metadata = decode_item_maybe_with_metadata(s)
        if item_type in special_items and metadata is not None:
            raise ValueError(
                f"Non-None metadata={metadata} is not allowed for special item type '{item_type}'"
            )

        metadata_set = map_type_to_metadata[item_type]
        if metadata in metadata_set:
            raise ValueError(f"Duplicate item entry for item '{s}'")
        map_type_to_metadata[item_type].add(metadata)

    for item_type, metadata_set in map_type_to_metadata.items():
        if None in metadata_set and len(metadata_set) != 1:
            raise ValueError(
                f"Item list overlaps for item_type={item_type}. This item list includes "
                "both the wildcard metadata option and at least one specific metadata: "
                f"{[n for n in metadata_set if n is not None]}"
            )


def item_list_contains(
    item_list: Sequence[str], item_type: str, metadata: Optional[str]
):
    # log clobber not supported here. (Only used by handlers without log clobber so far).
    if metadata is None:
        return item_type in item_list
    else:
        return encode_item_with_metadata(item_type, metadata) in item_list


def get_unique_matching_item_list_id(
    item_list: Sequence[str],
    item_type: str,
    metadata: int,
    clobber_logs=True,
) -> Optional[str]:
    """
    Assuming that `item_list` doesn't have duplicate elements, returns the string
    identifier in `item_list` that corresponds to `item_type` and `metadata`.

    If there is no matching strings, returns None.

    If there are multiple matching strings, raises a ValueError, because item_lists should
    not have overlapping item identifiers.

    Args:
        item_list: A list of item identifiers. Either just the item type ("wooden_pickaxe")
            or the item type with a metadata requirement ("planks#2").
        item_type: The item type to search for.
        metadata: The metadata to search for.
        clobber_logs: If True, and the only ID in `item_list` starting with "log.*" is the
            ID "log" (no metadata suffix), then treat "log" as a match for "log2". This is
            useful for MineRLTreeChop-v0 where obtaining acacia logs ("log2") should also
            count as obtaining regular logs. Note that no clobbering will occur if any
            log item IDs include metadata, or there's any log2 item IDs in the `item_list`.

            A potentially less tricky solution than this clobbering
            behavior could be adding a special type "log*" type which matches both "log"
            and "log2".
    """
    assert metadata is not None
    if clobber_logs and item_type == "log2":
        log_start = [x for x in item_list if x.startswith("log")]
        if len(log_start) == 1 and log_start[0] == "log":
            item_type = "log"

    result = None
    matches = 0
    if item_type in item_list:
        result = item_type
        matches += 1

    key = encode_item_with_metadata(item_type, metadata)
    if key in item_list:
        result = key
        matches += 1

    if matches > 1:
        raise ValueError(
            f"Multiple item identifiers match with {(item_type, metadata)}"
        )

    return result


def inventory_start_spec_to_item_ids(inv_spec: Sequence[dict]) -> List[str]:
    """Converts the argument of SimpleInventoryAgentStart into a list of equivalent
    item ids suitable for passing into other handlers, like FlatInventoryObservation and
    EquipAction.

    [dict(type=planks, metadata=2, quantity=3),
     dict(type=wooden_pickaxe, quantity=1), ...] => ["planks#2", "wooden_pickaxe", ...]
    """
    result = []
    for d in inv_spec:
        item_type = d["type"]
        metadata = d.get("metadata")
        item_id = encode_item_with_metadata(item_type, metadata)
        result.append(item_id)
    return list(set(result))
