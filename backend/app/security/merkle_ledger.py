import hashlib
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("finsecure.security.merkle")

class MerkleAuditLedger:
    """
    Merkle-Tree Audit Ledger.
    Maintains a tamper-evident binary Merkle tree of all security and trust events.
    Enables detection of historical audit record modifications.
    """

    def __init__(self):
        self._leaves: List[str] = []
        self._root_hash: str = hashlib.sha256(b"FINSECURE_GENESIS_BLOCK").hexdigest()

    def add_event(self, event_data: Dict[str, Any]) -> str:
        """Hash event payload and append to Merkle tree, returning leaf hash."""
        canonical_str = json.dumps(event_data, sort_keys=True, default=str)
        leaf_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        self._leaves.append(leaf_hash)
        self._root_hash = self._recompute_root()
        logger.info(f"Merkle ledger updated. New root: {self._root_hash[:16]}... (Total leaves: {len(self._leaves)})")
        return leaf_hash

    def get_root_hash(self) -> str:
        return self._root_hash

    def _recompute_root(self) -> str:
        if not self._leaves:
            return hashlib.sha256(b"FINSECURE_GENESIS_BLOCK").hexdigest()

        current_level = list(self._leaves)
        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1]) # Duplicate last leaf if odd count

            next_level = []
            for i in range(0, len(current_level), 2):
                combined = (current_level[i] + current_level[i + 1]).encode("utf-8")
                next_level.append(hashlib.sha256(combined).hexdigest())

            current_level = next_level

        return current_level[0]

    def verify_integrity(self, expected_root: Optional[str] = None) -> bool:
        """Recompute Merkle root and check against expected root hash."""
        calc_root = self._recompute_root()
        target = expected_root or self._root_hash
        return calc_root == target

# Global Merkle ledger instance
merkle_ledger = MerkleAuditLedger()
