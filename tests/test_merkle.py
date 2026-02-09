import pytest
from dfts.merkle import MerkleTree

def test_single_leaf():
    import hashlib
    h_a = hashlib.sha256(b"a").hexdigest()
    leaves = [h_a]
    tree = MerkleTree(leaves)
    assert tree.get_root() == h_a
    proof = tree.get_proof(h_a)
    assert proof == []
    assert MerkleTree.verify_proof(h_a, proof, h_a)

def test_two_leaves():
    # leaves are sorted in constructor
    import hashlib
    h_a = hashlib.sha256(b"a").hexdigest()
    h_b = hashlib.sha256(b"b").hexdigest()
    
    leaves = [h_b, h_a]
    tree = MerkleTree(leaves)
    
    # Dynamic verification
    sorted_leaves = sorted(leaves)
    left = sorted_leaves[0]
    right = sorted_leaves[1]
    
    combined = bytes.fromhex(left) + bytes.fromhex(right)
    expected_root = hashlib.sha256(combined).hexdigest()
    
    assert tree.get_root() == expected_root
    
    # Verify proof for h_a
    proof_a = tree.get_proof(h_a)
    assert len(proof_a) == 1
    
    # Check position based on sorted order
    if h_a == left:
        assert proof_a[0]['position'] == 'right'
        assert proof_a[0]['hash'] == h_b
    else:
        assert proof_a[0]['position'] == 'left'
        assert proof_a[0]['hash'] == h_b
        
    assert MerkleTree.verify_proof(h_a, proof_a, expected_root)

def test_three_leaves():
    import hashlib
    h_a = hashlib.sha256(b"a").hexdigest()
    h_b = hashlib.sha256(b"b").hexdigest()
    h_c = hashlib.sha256(b"c").hexdigest()
    
    leaves = [h_c, h_a, h_b]
    tree = MerkleTree(leaves)
    
    sorted_leaves = sorted(leaves)
    # L1: sorted[0], sorted[1], sorted[2]
    # L2: H(0+1), H(2+2)
    
    h_01 = hashlib.sha256(bytes.fromhex(sorted_leaves[0]) + bytes.fromhex(sorted_leaves[1])).hexdigest()
    h_22 = hashlib.sha256(bytes.fromhex(sorted_leaves[2]) + bytes.fromhex(sorted_leaves[2])).hexdigest()
    expected_root = hashlib.sha256(bytes.fromhex(h_01) + bytes.fromhex(h_22)).hexdigest()
    
    assert tree.get_root() == expected_root
    
    # Verify proof for h_c
    proof_c = tree.get_proof(h_c)
    assert MerkleTree.verify_proof(h_c, proof_c, expected_root)

def test_proof_verification_fail():
    import hashlib
    h_a = hashlib.sha256(b"a").hexdigest()
    h_b = hashlib.sha256(b"b").hexdigest()
    
    tree = MerkleTree([h_a, h_b])
    root = tree.get_root()
    proof = tree.get_proof(h_a)
    
    # Wrong target
    assert not MerkleTree.verify_proof(h_b, proof, root)
    
    # Tampered proof
    proof[0]['hash'] = h_a # replace sibling b with a
    assert not MerkleTree.verify_proof(h_a, proof, root)
