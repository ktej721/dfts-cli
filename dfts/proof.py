import json
from typing import Dict, List, Optional

class Proof:
    """
    this class holds everything you need to prove a file was anchored.
    it's basically a bundle of hashes and a bitcoin txid.
    """
    def __init__(self, 
                 file_hash: str, 
                 merkle_root: str, 
                 merkle_path: List[Dict[str, str]], 
                 network: str, 
                 transaction_id: str,
                 block_height: Optional[int] = None):
        
        self.file_hash = file_hash
        self.merkle_root = merkle_root
        self.merkle_path = merkle_path
        self.network = network
        self.transaction_id = transaction_id
        self.block_height = block_height
        self.version = "1.0"

    def to_dict(self) -> Dict:
        """
        turns the proof object into a dict so we can save it as json.
        """
        return {
            "version": self.version,
            "file_hash": self.file_hash,
            "merkle_root": self.merkle_root,
            "merkle_path": self.merkle_path,
            "bitcoin_network": self.network,
            "transaction_id": self.transaction_id,
            "block_height": self.block_height
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Proof':
        """
        creates a proof object from a dict. helpful when loading from a file.
        """
        # Validate version if necessary in the future
        return cls(
            file_hash=data["file_hash"],
            merkle_root=data["merkle_root"],
            merkle_path=data["merkle_path"],
            network=data["bitcoin_network"],
            transaction_id=data["transaction_id"],
            block_height=data.get("block_height")
        )

    def save(self, path: str):
        """
        saves the proof as a json file at the given path.
        """
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'Proof':
        """
        loads a proof from a json file. pretty straightforward.
        """
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)