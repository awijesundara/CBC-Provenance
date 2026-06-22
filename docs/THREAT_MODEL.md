# CBC-Provenance Threat Model

## Threats Addressed (T1-T14)

### T1: Image Tampering
**Threat:** Attacker modifies container layers or OCI manifest after VC issuance
**Mitigation:** Manifest digest in VC is cryptographically bound; any modification changes the digest
**Status:** MITIGATED

### T2: Signature Forgery
**Threat:** Attacker forges Ed25519 signature on VC
**Mitigation:** Ed25519Signature2020 with W3C Data Integrity, URDNA2015 canonicalization
**Status:** MITIGATED

### T3: Cross-Registry Replay
**Threat:** Attacker reuses valid VC on different registry/contract
**Mitigation:** **CBC binding** - VC includes (chainId, contractAddress); verifier checks equality
**Status:** MITIGATED (**CORE FEATURE**)

### T4: Revocation Bypass
**Threat:** Attacker uses revoked VC despite revocation
**Mitigation:** On-chain revocation status checked at admission
**Status:** MITIGATED

### T5: DID Resolution Attack
**Threat:** Attacker returns fake DID Document from IPFS
**Mitigation:** Content-addressed via IPFS CID; smart contract verifies CID matches on-chain record
**Status:** MITIGATED

### T6: Cache Poisoning
**Threat:** Attacker pollutes webhook cache with valid-seeming invalid credentials
**Mitigation:** TTL-based invalidation, signature verification on every cache hit
**Status:** MITIGATED

### T7: Timeout Exploitation
**Threat:** Attacker triggers timeouts to bypass validation (via resource exhaustion)
**Mitigation:** Fail-closed semantics - deny admission on any timeout
**Status:** MITIGATED

### T8: IPFS Gateway Compromise
**Threat:** Compromised IPFS gateway returns tampered credentials
**Mitigation:** Verify signatures; webhook can query multiple gateways
**Status:** PARTIALLY MITIGATED

### T9: Smart Contract Vulnerability
**Threat:** Exploit in DIDRegistry contract logic
**Mitigation:** Audited contract, modular design, batch operation support
**Status:** DESIGN MITIGATION

### T10: Key Rotation Failure
**Threat:** Compromised issuer key not promptly rotated
**Mitigation:** Per-issuer API key scoping, short-lived tokens, quarterly rotation policy
**Status:** OPERATIONAL MITIGATION

### T11: Admission Webhook Compromise
**Threat:** Attacker compromises webhook container/host
**Mitigation:** mTLS, least-privilege RBAC, network policies
**Status:** OPERATIONAL MITIGATION

### T12: Rate Limit Bypass
**Threat:** Attacker exhausts gas budget by rapid issuance
**Mitigation:** Per-maintainer rate limits on issuer API
**Status:** OPERATIONAL MITIGATION

### T13: Manifest Digest Resolution Failure
**Threat:** Attacker provides invalid image reference preventing digest resolution
**Mitigation:** Fail-closed - deny admission if digest cannot be resolved
**Status:** MITIGATED

### T14: URDNA2015 Canonicalization Attack
**Threat:** Attacker manipulates canonicalization to forge signature
**Mitigation:** W3C Data Integrity with URDNA2015; signatures verified with canonical form
**Status:** MITIGATED

## Out of Scope

### Not Addressed

1. **Build System Compromise**
   - Attacker compromises CI/CD pipeline to inject malicious code
   - Mitigation: SLSA compliance, HSM-backed signing

2. **Package Dependency Poisoning**
   - Attacker poisons upstream dependencies
   - Mitigation: Software composition analysis (SCA), SBOM verification

3. **IPFS Pin-Dropping**
   - Attacker unpins critical VC/DID documents from network
   - Mitigation: Redundant pinning, multiple gateways

4. **Blockchain Infrastructure Unavailability**
   - Arbitrum Sepolia network down or unreachable
   - Mitigation: Fail-closed behavior; configure fallback RPC endpoints

## Attack Scenarios

### Scenario 1: Cross-Registry Replay (MITIGATED)
```
Attacker:
  1. Obtains valid VC for Image A issued on Contract X
  2. Attempts to deploy Image A on different registry using Contract Y
  3. Webhook checks CBC: VCbc = (421614, ContractX), Expected = (421614, ContractY)
  4. CBC mismatch → Admission DENIED ✓
```

### Scenario 2: Revocation Bypass (MITIGATED)
```
Attacker:
  1. Maintains copy of valid VC
  2. Issuer revokes the VC on-chain
  3. Attacker attempts to deploy image using cached VC
  4. Webhook checks on-chain: isVCValid(vcId) → false
  5. Admission DENIED ✓
```

### Scenario 3: Signature Forgery (MITIGATED)
```
Attacker:
  1. Creates fake VC with modified manifest digest
  2. Attempts to sign with stolen issuer private key
  3. Webhook verifies signature against issuer's public key (from DID Document)
  4. Signature validation → success
  5. BUT: On-chain check fails - VC was never recorded
  6. Admission DENIED ✓
```

## Security Assumptions

1. **IPFS CID Integrity:** Content-addressing provides integrity verification
2. **Smart Contract Immutability:** Deployed contract cannot be modified
3. **Issuer Key Security:** Issuer private key is protected (HSM/TPM recommended)
4. **Kubernetes Control Plane:** Control plane is not compromised
5. **Network TLS:** mTLS between components prevents MITM attacks
6. **Atomic Consistency:** On-chain revocation is atomic and final

## Recommendations

1. Audit smart contract before mainnet deployment
2. Use HSM/TPM for production issuer key storage
3. Enable Kubernetes network policies to restrict webhook network access
4. Implement monitoring for admission webhook performance and errors
5. Set up alerting for revocation events
6. Regular key rotation (quarterly minimum)
7. Maintain multiple IPFS gateway endpoints for redundancy
8. Use Arbitrum Sepolia for testing; upgrade to mainnet after audit
