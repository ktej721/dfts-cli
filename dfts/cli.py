import click
import json
import os
import glob
import requests
from typing import List
from dfts.hash import sha256_file
from dfts.merkle import MerkleTree
from dfts.proof import Proof

@click.group()
def cli():
    """dfts - just a simple tool to timestamp stuff on Bitcoin."""
    pass

@cli.command()
@click.argument("file_path")
def hash(file_path):
    """calculates the sha-256 hash of a file. pretty standard stuff."""
    try:
        digest = sha256_file(file_path)
        click.echo(digest)
    except Exception as e:
        click.echo(f"Oops, couldn't hash the file: {e}", err=True)

@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", default="hashes.json", help="Where to save the hashes")
def batch(directory, output):
    """hashes everything in a folder. recursively."""
    hashes = {}
    # Grab all files in the directory
    files = [f for f in glob.glob(os.path.join(directory, "**"), recursive=True) if os.path.isfile(f)]
    
    with click.progressbar(files, label="Hashing files...") as bar:
        for file_path in bar:
            try:
                digest = sha256_file(file_path)
                hashes[file_path] = digest
            except Exception as e:
                click.echo(f"Skipping {file_path} (error: {e})", err=True)
    
    with open(output, "w") as f:
        json.dump(hashes, f, indent=2)
    
    click.echo(f"Done! Saved hashes to {output}")

@cli.command()
@click.argument("hashes_file", type=click.File("r"))
@click.option("--save-proofs/--no-save-proofs", default=True, help="Save the proof files locally")
def merkle(hashes_file, save_proofs):
    """builds the merkle tree from your hashes."""
    data = json.load(hashes_file)
    if not isinstance(data, dict):
        click.echo("Error: Input needs to be a JSON object (filepath -> hash).", err=True)
        return

    # Extract just the hashes for the tree
    file_map = {v: k for k, v in data.items()} 
    leaves = list(data.values())
    
    if not leaves:
        click.echo("No hashes found in that file.", err=True)
        return

    tree = MerkleTree(leaves)
    root = tree.get_root()
    
    click.echo(f"Here is your Merkle Root: {root}")
    
    if save_proofs:
        os.makedirs("proofs", exist_ok=True)
        for file_hash in leaves:
            path = tree.get_proof(file_hash)
            
            # We save a "pending" proof because we don't have the TXID yet.
            file_path = file_map.get(file_hash, "unknown_file")
            safe_name = os.path.basename(file_path)
            
            partial_proof = {
                "file_hash": file_hash,
                "merkle_root": root,
                "merkle_path": path,
                "file_path_hint": file_path
            }
            
            with open(f"proofs/{safe_name}.pending.json", "w") as f:
                json.dump(partial_proof, f, indent=2)
                
        click.echo(f"Okay, saved pending proofs to proofs/*.pending.json")
        click.echo("Next step: Run 'dfts anchor <root>' to put this on the blockchain.")

@cli.command()
@click.argument("merkle_root")
def anchor(merkle_root):
    """a guide to help you anchor your root with electrum."""
    click.echo(f"\nMerkle Root: {merkle_root}")
    click.echo("\nInstructions:")
    click.echo("1. Open your wallet (like Electrum Testnet).")
    click.echo("2. Make a new transaction with an OP_RETURN output.")
    click.echo(f"   Use this Hex Data: {merkle_root}")
    click.echo("3. Send it!")
    
    txid = click.prompt("\n⌨️  Paste the Transaction ID (TXID) here")
    
    if not txid:
        click.echo("Cancelled.")
        return

    click.echo(f"\n Cool, anchoring recorded. TXID: {txid}")
    click.echo(f"Now run: dfts finalize proofs/ {txid}")

@cli.command()
@click.argument("proof_dir", type=click.Path(exists=True))
@click.argument("txid")
@click.option("--network", default="testnet", help="Which network? (testnet/signet)")
def finalize(proof_dir, txid, network):
    """updates the pending proofs with the final txid."""
    files = glob.glob(os.path.join(proof_dir, "*.pending.json"))
    count = 0
    for p_file in files:
        with open(p_file, "r") as f:
            data = json.load(f)
        
        proof = Proof(
            file_hash=data["file_hash"],
            merkle_root=data["merkle_root"],
            merkle_path=data["merkle_path"],
            network=network,
            transaction_id=txid
        )
        
        new_path = p_file.replace(".pending.json", ".json")
        proof.save(new_path)
        os.remove(p_file)
        count += 1
    
    click.echo(f"Updated {count} proofs in {proof_dir}")

@cli.command()
@click.argument("file_path")
@click.argument("proof_path")
def verify(file_path, proof_path):
    """checks if the file matches the proof and is actually on the blockchain."""
    # 1. Verify File Integrity
    click.echo("1️⃣  Checking file integrity...")
    file_hash = sha256_file(file_path)
    proof = Proof.load(proof_path)
    
    if file_hash != proof.file_hash:
        click.echo(f"Fail: File hash doesn't match.\nExpected: {proof.file_hash}\nActual:   {file_hash}", err=True)
        return
    click.echo("   Matches! ✔")

    # 2. Verify Merkle Proof
    click.echo("2️⃣  Checking Merkle proof...")
    if not MerkleTree.verify_proof(file_hash, proof.merkle_path, proof.merkle_root):
        click.echo(" Fail: Merkle proof is invalid. Root mismatch.", err=True)
        return
    click.echo("   Valid! ✔")

    # 3. Verify Blockchain Anchor
    click.echo(f"3️⃣  Checking blockchain (TX: {proof.transaction_id})...")
    try:
        # Use Blockstream API to check
        network_path = "testnet/" if proof.network == "testnet" else ""
        url = f"https://blockstream.info/{network_path}api/tx/{proof.transaction_id}"
        
        response = requests.get(url)
        if response.status_code != 200:
             click.echo(f" Fail: Can't find that transaction (HTTP {response.status_code}).", err=True)
             return
             
        tx_data = response.json()
        
        # Check for OP_RETURN with root
        outputs = tx_data.get("vout", [])
        found = False
        for out in outputs:
            script = out.get("scriptpubkey", "")
            if proof.merkle_root in script:
                found = True
                break
        
        if found:
            status = tx_data.get("status", {})
            confirmed = status.get("confirmed", False)
            block = status.get("block_height", -1)
            status_text = f"Confirmed at block {block}" if confirmed else "Unconfirmed (in mempool)"
            click.echo(f"   Found it! ✔ ({status_text})")
            click.echo("\n Verification Successful!")
        else:
            click.echo(" Fail: Couldn't find the Merkle root in that transaction.", err=True)

    except Exception as e:
        click.echo(f" Fail: Error checking blockchain: {e}", err=True)

def main():
    cli()

if __name__ == "__main__":
    main()