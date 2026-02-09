import hashlib
from typing import List, Dict, Optional

class MerkleTree:
    def __init__(self, leaves: List[str]):
        """
        starts the tree with a list of hashes.
        we sort them so the tree is always the same.
        """
        self.leaves = sorted(leaves)
        self.levels = self._build_tree(self.leaves)
        self.root = self.levels[-1][0] if self.levels else None

    def _hash_pair(self, left: str, right: str) -> str:
        """
        combines two hex strings and hashes them.
        """
        # Decoding hex to bytes for hashing
        left_bytes = bytes.fromhex(left)
        right_bytes = bytes.fromhex(right)
        
        # Concatenate
        combined = left_bytes + right_bytes
        
        # Hash
        return hashlib.sha256(combined).hexdigest()

    def _build_tree(self, leaves: List[str]) -> List[List[str]]:
        """
        builds the tree layer by layer.
        """
        if not leaves:
            return []

        levels = [leaves]
        current_level = leaves

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                    next_level.append(self._hash_pair(left, right))
                else:
                    # If we have an odd number, we just duplicate the last one.
                    # This is pretty standard.
                    right = left
                    next_level.append(self._hash_pair(left, right))
            
            levels.append(next_level)
            current_level = next_level

        return levels

    def get_root(self) -> Optional[str]:
        return self.root

    def get_proof(self, target_hash: str) -> List[Dict[str, str]]:
        """
        makes a proof for a specific hash so you can verify it later.
        returns a list of steps (left/right and the sibling hash).
        """
        if target_hash not in self.leaves:
            raise ValueError("Hash not found in tree leaves")

        proof = []
        index = self.leaves.index(target_hash)
        
        # Go up the tree levels (except the root)
        for level in self.levels[:-1]:
            is_right_child = (index % 2 == 1)
            sibling_index = index - 1 if is_right_child else index + 1

            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
                position = 'left' if is_right_child else 'right'
                proof.append({'position': position, 'hash': sibling_hash})
            else:
                # This happens if we are the last node and it was duplicated.
                # The sibling is actually itself in this construction.
                sibling_hash = level[index] 
                position = 'right' 
                proof.append({'position': position, 'hash': sibling_hash})

            index //= 2

        return proof

    @staticmethod
    def verify_proof(target_hash: str, proof: List[Dict[str, str]], root: str) -> bool:
        """
        checks if the proof is valid.
        """
        current_hash = target_hash
        
        for step in proof:
            sibling = step['hash']
            position = step['position']
            
            left_bytes = bytes.fromhex(sibling if position == 'left' else current_hash)
            right_bytes = bytes.fromhex(current_hash if position == 'left' else sibling)
            
            current_hash = hashlib.sha256(left_bytes + right_bytes).hexdigest()

        return current_hash == root