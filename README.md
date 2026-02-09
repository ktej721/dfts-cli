# DFTS (Decentralized File Timestamping System)

This is a tool I wrote to help timestamp files on the Bitcoin blockchain. Basically, it proves that a file existed at a certain time without needing to trust a central server.

It works on the Bitcoin Testnet right now.

## How it works

1.  **Hashing:** It takes your files and calculates their SHA-256 hashes.
2.  **Merkle Tree:** It combines all those hashes into a single "Merkle Root".
3.  **Anchoring:** You take that root and put it into a Bitcoin transaction using `OP_RETURN`.
4.  **Verification:** Later, you can prove the file hasn't changed and was there when the block was mined.

## Setup

Just install it with pip:

```bash
pip install .
```

## How to use it

There are a few steps to timestamp your files.

### 1. Hash your files
First, pick a folder with the files you want to timestamp.

```bash
dfts batch my_documents/ --output hashes.json
```

### 2. Make the proofs
This creates the Merkle tree and saves the root.

```bash
dfts merkle hashes.json
```
This will print out the **Merkle Root**. You'll need this for the next step.

### 3. Send it to Bitcoin
This is where you actually put it on the blockchain. You'll need a wallet like Electrum (Testnet).

```bash
dfts anchor <PASTE_MERKLE_ROOT_HERE>
```
Follow the instructions it prints out. Once you send the transaction, copy the **TXID**.

### 4. Finish up
Now tell the tool the TXID so it can save the final proofs.

```bash
dfts finalize proofs/ <TXID>
```

### 5. Verify
You can check a file later like this:

```bash
dfts verify my_documents/contract.pdf proofs/contract.pdf.json
```

## Future ideas (vaguely)
*   Automate the wallet part (it's manual right now).
*   Maybe support Mainnet properly.

## Technical Roadmap (iykyk)

*   **V1 (Current):** CLI, Merkle aggregation, Manual anchoring (Testnet). Done.
*   **V2:** Programmatic anchoring via PSBT.
*   **V3:** OpenTimestamps compatibility and scalable servers.
*   **V4:** Mainnet hardening & P2P proof propagation.
