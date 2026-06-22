# CBC-Provenance: Contract-Bound Verifiable Credentials for Replay-Resistant OCI Image Provenance in Kubernetes

**Status:** Implementation based on peer-reviewed research manuscript

## Overview

CBC-Provenance is a decentralized container image authentication framework that prevents replay attacks by binding Verifiable Credentials (VCs) to specific smart contracts. It integrates Self-Sovereign Identity (SSI) principles with blockchain-based smart contracts, IPFS storage, and Kubernetes admission control.

## Core Innovation: Contract-Binding Context (CBC)

Traditional container credentials can be replayed across different registries. CBC-Provenance solves this by binding each VC to a specific contract:

```json
{
  "credentialSubject": {
    "image": {
      "manifestDigest": "sha256:a3b2c1...",
      "reference": "docker.io/user/app@sha256:a3b2c1..."
    },
    "cbc": {
      "chainId": 421614,
      "contractAddress": "0x145D..."
    }
  }
}
```

**Result:** Credentials issued on Contract A are **invalid** on Contract B, preventing cross-registry replay attacks.

## Technology Stack

### Blockchain & Smart Contracts
- **Network:** Arbitrum Sepolia (Chain ID: 421614)
- **Language:** Solidity 0.8.21
- **Framework:** Hardhat 2.19
- **Gas Optimization:** >80% reduction via bytes32 VC IDs
- **Features:** Batch operations, event-based indexing

### Decentralized Identity & Credentials
- **Language:** Python 3.11
- **DID Method:** did:key with Ed25519 keys
- **Standards:** W3C VC Data Model v1.1
- **Signing:** Ed25519Signature2020
- **Canonicalization:** URDNA2015

### Kubernetes Admission Control
- **Language:** Go 1.21
- **Webhook Type:** Validating admission webhook
- **TLS:** cert-manager
- **Kubernetes Version:** 1.29

### Decentralized Storage
- **IPFS:** Kubo 0.24
- **Content Addressing:** CID-based integrity verification
- **Availability:** Pinning + multiple gateways

### Development Environment
- **OS:** Ubuntu 22.04 LTS
- **Container Runtime:** Docker 24.0
- **Local K8s:** kind v0.20

## Architecture

### Components

1. **Maintainer Node (Python)**
   - Generates and registers DIDs
   - Issues VCs with CBC binding
   - Publishes to IPFS
   - Records on smart contract

2. **Smart Contract (Solidity)**
   - DID registry
   - VC state management
   - Revocation tracking
   - On-chain membership verification

3. **Kubernetes Admission Webhook (Go)**
   - Image credential validation
   - CBC equality enforcement
   - Signature verification
   - On-chain status checking

4. **IPFS Network**
   - Stores DID Documents
   - Stores VCs
   - Stores metadata
   - Content-addressable retrieval

## Workflow

```
1. Maintainer generates DID and VC with CBC binding
2. VC is signed with Ed25519Signature2020
3. VC and DID Document published to IPFS
4. VC recorded on smart contract
5. At Kubernetes admission:
   a. Resolve image manifest digest
   b. Fetch VC from IPFS
   c. Verify issuer DID Document
   d. Validate Ed25519 signature
   e. Check CBC equality (CBCvc == CBCexp)
   f. Query on-chain VC status
   g. Verify non-revoked
   h. Allow/Deny pod admission
```

## Key Features

- ✅ **Replay-Resistant:** CBC binding prevents cross-registry replay
- ✅ **Decentralized:** No single certificate authority required
- ✅ **W3C Compliant:** Uses standard DID and VC formats
- ✅ **Content-Addressed:** IPFS provides integrity verification
- ✅ **Immutable Audit Trail:** Smart contract records all lifecycle events
- ✅ **Revocation:** On-chain revocation status tracking
- ✅ **Multi-Container:** Validates each image independently
- ✅ **Fail-Closed:** Denies admission on network failures

## Repository Structure

```
CBC-Provenance/
├── README.md                          # This file
├── .env.example                       # Environment template
├── smart-contracts/
│   ├── contracts/
│   │   └── DIDRegistry.sol           # Solidity 0.8.21 contract
│   ├── test/
│   │   └── DIDRegistry.test.js       # Hardhat tests
│   ├── hardhat.config.js             # Hardhat configuration
│   └── package.json
├── issuer/
│   ├── vc_issuer.py                  # Main issuer service
│   ├── did_utils.py                  # DID operations
│   ├── vc_utils.py                   # VC operations
│   ├── requirements.txt               # Python dependencies
│   └── tests/
│       ├── test_did.py
│       ├── test_vc.py
│       └── test_integration.py
├── webhook/
│   ├── main.go                       # Webhook server
│   ├── admission.go                  # Validation logic
│   ├── config.go                     # Configuration
│   ├── go.mod
│   ├── go.sum
│   └── tests/
├── examples/
│   ├── vc-example.json               # Sample VC with CBC
│   ├── did-document.json             # Sample DID Document
│   ├── config-arbitrum-sepolia.env   # Network configuration
│   └── kyverno-policy.yaml           # K8s policy example
├── docs/
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── THREAT_MODEL.md               # Threat analysis (T1-T14)
│   ├── API_REFERENCE.md              # API documentation
│   ├── ARCHITECTURE.md               # Architecture details
│   └── BENCHMARKS.md                 # Performance results
└── docker/
    ├── Dockerfile.issuer             # Issuer container
    ├── Dockerfile.webhook            # Webhook container
    └── docker-compose.yml            # Local dev environment
```

## Quick Start

### Prerequisites

- Git & GitHub account
- Docker & Kubernetes (or kind)
- Node.js 16+ (for smart contracts)
- Python 3.11 (for issuer)
- Go 1.21 (for webhook)

### 1. Clone Repository

```bash
git clone git@github.com:awijesundara/CBC-Provenance.git
cd CBC-Provenance
```

### 2. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Deploy Smart Contract

```bash
cd smart-contracts
npm install
npx hardhat run scripts/deploy.js --network arbitrumSepolia
```

### 4. Run Issuer Node

```bash
cd issuer
pip install -r requirements.txt
python vc_issuer.py
```

### 5. Deploy Webhook to Kubernetes

```bash
cd webhook
kubectl apply -f k8s-deployment.yaml
```

## Threat Model

CBC-Provenance addresses the following threats (T1-T14):

- **T1:** Image tampering → Prevented by manifest digest verification
- **T2:** Signature forgery → Ed25519 verification + W3C Data Integrity
- **T3:** Cross-registry replay → **CBC equality check** (core feature!)
- **T4:** Revocation bypass → On-chain revocation status checks
- **T5:** DID resolution attack → Content-addressed via IPFS CID verification
- **T6:** Cache poisoning → TTL-based invalidation + signature verification
- **T7:** Timeout exploitation → Fail-closed on network timeout
- **T8-T14:** See THREAT_MODEL.md for complete list

### Out of Scope

- Build system compromise (mitigated by SLSA compliance)
- Package dependency poisoning
- IPFS pin-dropping attacks
- Blockchain infrastructure unavailability

## Smart Contract Functions

### DID Registry

```solidity
function registerDID(string calldata did, bytes32 cidHash) external
function getDIDDocument(string calldata did) external view returns (bytes32)
function setDIDOwner(string calldata did, address owner) external
function isDIDOwner(string calldata did, address caller) external view returns (bool)
```

### VC State Management

```solidity
function recordVC(bytes32 vcId, string calldata issuerDid, uint256 issuanceTs) external
function revokeVC(bytes32 vcId) external
function getVCStatus(bytes32 vcId) external view returns (VCStatus)
function isVCRecorded(bytes32 vcId) external view returns (bool)
function isVCRevoked(bytes32 vcId) external view returns (bool)
```

## Performance

Expected performance metrics (from evaluation):

- **Admission latency:** <500ms (p99)
- **Cache hit rate:** >85% for repeated images
- **Gas cost per VC record:** ~50,000 gas (optimized)
- **Webhook throughput:** >1000 req/s per instance

## Security Considerations

1. **Private Key Management:** Use HSM/TPM for production
2. **API Key Rotation:** Rotate per-maintainer keys quarterly
3. **mTLS:** Enforce mutual TLS between issuer and webhook
4. **Rate Limiting:** Implement per-maintainer rate limits
5. **Fail-Closed:** Deny admission on network errors

See SECURITY.md for detailed hardening guidelines.

## Documentation

- **DEPLOYMENT.md** - Step-by-step deployment guide
- **THREAT_MODEL.md** - Complete threat analysis (T1-T14)
- **API_REFERENCE.md** - Solidity & Python API documentation
- **ARCHITECTURE.md** - Detailed architecture diagrams
- **BENCHMARKS.md** - Performance evaluation results

## Testing

```bash
# Run all tests
make test

# Test smart contract
cd smart-contracts && npm test

# Test Python issuer
cd issuer && pytest

# Test Go webhook
cd webhook && go test ./...
```

## Evaluation Results

The implementation was evaluated on:
- Arbitrum Sepolia testnet (Chain ID: 421614)
- Kubernetes 1.29 with kind
- Multiple image repositories and registries
- Concurrent admission requests

Results available in docs/BENCHMARKS.md

## Publications

This work is based on peer-reviewed research. For more information, see:
- Manuscript: "CBC-Provenance: Contract-Bound Verifiable Credentials for Replay-Resistant OCI Image Provenance in Kubernetes"
- Conference: [To be announced]
- DOI: [To be assigned]

## Authors

- W. M. A. B. Wijesundara (Institute of Science Tokyo)
- Joong-Sun Lee (Institute of Science Tokyo)
- YiNa Jeong (Catholic Kwandong University)
- Takashi Obi (Institute of Science Tokyo)

## License

[To be determined]

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: [project issues]
- Email: [contact email]

---

**Status:** Research Implementation  
**Last Updated:** 2026-06-23  
**Manuscript Status:** Under Review
