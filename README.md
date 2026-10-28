# SOVEREIGNLEDGER
### Air-Gapped Personal Accounting & Tax Compliance Agent

[![NVIDIA OpenShell](https://img.shields.io/badge/Sandbox-NVIDIA%20OpenShell%20v0.1.2-76b900.svg)](https://developer.nvidia.com)
[![Model](https://img.shields.io/badge/Model-nvidia%2FMistral--NeMo--12B--Instruct-blue.svg)](https://huggingface.co/nvidia/Mistral-NeMo-12B-Instruct)
[![Network Egress](https://img.shields.io/badge/Network.Egress-DENY__ALL-crimson.svg)](#security--sandbox-architecture)
[![Ledger Engine](https://img.shields.io/badge/Store-DuckDB%20Double--Entry-yellow.svg)](https://duckdb.org)

SovereignLedger is an autonomous personal accounting and tax compliance daemon running inside a kernel-enforced `NVIDIA OpenShell` network-denied sandbox (`egress: deny_all`). It synthesizes reusable, deterministic Python parsing skills for arbitrary receipts and bank CSVs, compiling financial records into an IRS Schedule C expense ledger without sending a single packet over the public internet.

---

## SYSTEM ARCHITECTURE

```
                      +-------------------------------------------------------------+
                      |                      LOCAL WORKSTATION                      |
                      |                                                             |
                      |   [ Monitored Drop Folder ] (/data/incoming)                |
                      |              |                                              |
                      |              v (inotify filesystem trigger)                 |
                      |   +-----------------------------------------------------+   |
                      |   |              NVIDIA OPENSHELL SANDBOX               |   |
                      |   |   Kernel Enforcement: network.egress = DENY_ALL     |   |
                      |   |   Filesystem: /data/incoming (ro), /db (rw)         |   |
                      |   |                                                     |   |
                      |   |   +---------------------------------------------+   |   |
                      |   |   |         SovereignLedger Core Daemon         |   |   |
                      |   |   |   - Unstructured Ingestion (PDF / CSV)      |   |   |
                      |   |   |   - Dynamic Parser & Skill Synthesis        |   |   |
                      |   |   |   - Double-Entry Verification               |   |   |
                      |   +---|------------------|--------------------------|---+   |
                      |       |                  v                          |       |
                      |       |   [ DuckDB / SQLite Encrypted Ledger ]      |       |
                      |       |   [ Reusable Extraction Skills: /skills/*.py ]      |
                      |       +------------------|--------------------------+       |
                      |                          | (Local IPC only:                 |
                      |                          |  127.0.0.1:11434 loopback)       |
                      |                          v                                  |
                      |   [ Local Inference: Ollama / llama.cpp ]                   |
                      |   nvidia/Mistral-NeMo-12B-Instruct (Q4_K_M)                 |
                      |   *Zero outbound internet packets. Pure local compute.*     |
                      +-------------------------------------------------------------+
```

---

## KEY DIFFERENTIATORS

1. **Kernel-Level Zero-Egress Boundary**: Intercepts network activity using Linux Landlock and socket-level monitors. Prohibits any connection outside of `127.0.0.1:11434`.
2. **Deterministic Code Synthesis**: When an unknown invoice is encountered, `Mistral-NeMo-12B` writes a Python extraction class. Once AST-validated, future invoices from that vendor run in milliseconds with 0 LLM tokens.
3. **Strict Arithmetic Guardrails**: LLMs are mathematically fallible. SovereignLedger enforces that all additions, subtractions, and double-entry reconciliations occur purely in DuckDB via deterministic SQL.
4. **Episodic Preference Memory**: Retains merchant tax assignments across sessions using SQLite FTS5.

---

## JUDGES' 60-SECOND RAPID EVALUATION GUIDE

You can launch and test the entire system in two minutes using the web cockpit:

```bash
# 1. Clone repository & install dependencies
git clone https://github.com/your-org/sovereignledger.git
cd sovereignledger
make install

# 2. Launch the interactive web cockpit
make run-web
```
Now open **http://localhost:8080** in your web browser.

### Verification Steps inside Web Dashboard:
1. Observe the **Security & Sandbox Telemetry** panel confirming `network.egress = DENY_ALL` and `0 external packets sent`.
2. Click the green **1-CLICK DEMO SIMULATION** button:
   - It deposits 4 test documents into the dropzone (Bank CSV, AWS Bill, Stripe Payout, GitHub Bill).
   - In milliseconds, the autonomous synthesizer checks AST safety and compiles new skills.
   - The double-entry ledger is balanced and reconciled.
3. Toggle to the **IRS Schedule C Report** tab to review the tax category aggregations.
4. Click **Export Schedule C (CSV)** to retrieve the balanced filing summary.

---

## CLI COMMAND REFERENCE

| Command | Description |
| :--- | :--- |
| `make install` | Installs system and test dependencies |
| `make seed` | Generates sample bank CSVs and digital invoices |
| `make run-web` | Launches web cockpit at `http://localhost:8080` |
| `make run-tui` | Launches Textual interactive terminal dashboard |
| `make run-watcher` | Runs standalone inotify dropzone daemon |
| `make test` | Executes full automated unit and e2e test suite |
| `make verify-isolation`| Audits network sandbox and zero-egress kernel rules |

---

## SECURITY & THREAT MODEL

```
THREAT: Malicious invoice prompt injection exfiltrating financial data.
MITIGATION:
  1. OpenShell kernel blocks all outbound sockets (Egress = DENY_ALL).
  2. AST validator kills any dynamic skill containing 'socket', 'urllib', or 'os'.
  3. LLM is isolated from the host via Landlock read-only filesystem limits.
```
```

---

## 7. VERIFICATION AND DEPLOYMENT INSTRUCTIONS

To verify the setup:

```bash
# 1. Run all unit & integration tests
pytest tests/ -v

# 2. Verify network isolation
bash scripts/verify_network_isolation.sh

# 3. Launch the dashboard for interactive verification
python3 -m src.cli serve-web --host 0.0.0.0 --port 8080
