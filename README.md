# ChangeImpact

**A GenLayer Intelligent Contract for comparing a registered commitment against two hash-pinned public document versions.**

ChangeImpact records a short commitment and a baseline document URL plus SHA-256 digest. A later review fetches the baseline and revised documents independently on the leader and validator paths, verifies the exact response bytes against the registered digests, and asks validators to assess five bounded dimensions: scope, action, conditions, time, and threshold.

The contract stores a review only after substantive validator agreement. Its outcome is derived deterministically:

- `UNCHANGED`: all five dimensions are `MATCH`.
- `MATERIAL_CHANGE`: at least one dimension is `CHANGED` and none is `UNCLEAR`.
- `UNCLEAR`: at least one dimension is `UNCLEAR`.

This is a consensus-backed comparison signal, not legal advice, proof of publisher identity, or proof that a document is authoritative.

## Contract interface

- `register_case(case_id, commitment, baseline_url, baseline_sha256)` — creates a unique case in `OPEN` status.
- `review_change(case_id, revised_url, revised_sha256)` — performs the one permitted review; successful reviews become `REVIEWED`.
- `get_case(case_id)` — returns the registered inputs and current result as JSON text.

Documents must be public, HTTPS-accessible, UTF-8 text responses, non-empty, and no more than 12,000 decoded characters. SHA-256 is checked against the exact response bytes before decoding. Login-only pages, scanned PDFs, and content that requires browser rendering are not supported by v1. A digest mismatch, inaccessible response, invalid UTF-8, or failed consensus must not produce a stored assessment.

## Local verification

Python 3.13 was used for the current local checks. Install the pinned development tools:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

On Windows, use `.venv\Scripts\python -m pip install -r requirements.txt` after creating the virtual environment.

Run Direct Mode tests and the GenVM linter:

```bash
.venv/bin/pytest -q tests/direct
.venv/bin/genvm-lint check contracts/change_impact.py
```

On Windows, replace `.venv/bin/<tool>` with `.venv\Scripts\<tool>.exe`.

### GenVM runner archive note

With `genlayer-test==0.29.2`, the first Direct Mode run may try to download `genvm-universal.tar.xz` from the GenVM `v0.3.0-rc7` release, where the published archive is named `genvm-runners-all.tar.xz`. If the runner download fails with HTTP 404, cache the published archive under the filename expected by the test SDK, then retry:

```bash
mkdir -p ~/.cache/gltest-direct
curl -fsSL -o ~/.cache/gltest-direct/genvm-universal-v0.3.0-rc7.tar.xz \
  https://github.com/genlayerlabs/genvm/releases/download/v0.3.0-rc7/genvm-runners-all.tar.xz
```

## Verification status

- GenVM lint: passed locally (3 checks).
- Direct Mode tests: 6 passed locally, including a digest-mismatch case proving failed retrieval does not write review state.
- Live Studionet deployment and one end-to-end full-consensus review: successful.
- The live example is one observed run, not an exhaustive test of network behavior or all validator/model conditions.

## Live Studionet evidence

- Network: Studionet, chain ID `61999`.
- Contract: [`0xf563C7a685cD8C7C8B8810537b442529Dc55Eac7`](https://explorer-studio.genlayer.com/address/0xf563C7a685cD8C7C8B8810537b442529Dc55Eac7).
- Deployment: [FINALIZED / Accepted](https://explorer-studio.genlayer.com/tx/0x5261f538b3fba69ed95fb401b84caa89667bedc99beb78447c3f6fbf0eadb220).
- Case registration: [FINALIZED / Accepted](https://explorer-studio.genlayer.com/tx/0x5e3592763bc569bea23fd925a322ebdad0449ce40dc90acdaff88a6bfbc057a2).
- Review: [FINALIZED / Accepted](https://explorer-studio.genlayer.com/tx/0xffba885794ddeb4074f46866163cb21548376422728f9c29beb0d2ccb381617f).
- Read-back via `get_case`: case `demo-support-terms-v1` is `REVIEWED` with outcome `MATERIAL_CHANGE`.
- The demonstration compares the two-day and five-day response terms; validators agreed `time: CHANGED` and the other four dimensions `MATCH`.

## Trust boundaries and limitations

- Registered URLs and commitments are caller-supplied; the contract does not authenticate document publishers.
- Only exact byte hashes are verified. Matching a hash does not prove the source is authoritative or truthful.
- The model output is bounded and quote-grounded, but semantic classification remains a judgment signal, not a legal interpretation.
- Cases are public on-chain and cannot be edited or reviewed a second time after a successful review.
- No funds, payment, identity verification, or continuous web monitoring are included.

## License

MIT. See [LICENSE](LICENSE).
