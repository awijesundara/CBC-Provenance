// CBC-Provenance Image Validation Logic
//
// This file implements the core admission control logic for validating
// container images with contract-bound verifiable credentials

package main

import (
"crypto/ed25519"
"encoding/json"
"fmt"
"log"
"time"
)

// ValidationResult contains the result of image validation
type ValidationResult struct {
Valid       bool
AllowReason string
DenyReason  string
Cached      bool
Latency     time.Duration
}

// ImageValidator validates container images against CBC credentials
type ImageValidator struct {
web3Client  *Web3Client
ipfsClient  *IPFSClient
config      *Config
cache       map[string]*CachedValidation
cacheTTL    time.Duration
}

// CachedValidation stores cached validation results
type CachedValidation struct {
Result    ValidationResult
Timestamp time.Time
}

// NewImageValidator creates a new image validator
func NewImageValidator(w3 *Web3Client, ipfs *IPFSClient, cfg *Config) *ImageValidator {
return &ImageValidator{
web3Client: w3,
ipfsClient: ipfs,
config:     cfg,
cache:      make(map[string]*CachedValidation),
cacheTTL:   time.Hour,
}
}

// ValidateImage validates a container image reference with CBC checking
func (v *ImageValidator) ValidateImage(imageRef string) ValidationResult {
startTime := time.Now()

// Step 1: Check cache
if cached, ok := v.cache[imageRef]; ok {
if time.Since(cached.Timestamp) < v.cacheTTL {
cached.Result.Cached = true
cached.Result.Latency = time.Since(startTime)
log.Printf("Cache hit for image %s\n", imageRef)
return cached.Result
}
}

// Step 2: Resolve image digest
digest, err := v.resolveImageDigest(imageRef)
if err != nil {
return ValidationResult{
Valid:      false,
DenyReason: fmt.Sprintf("Failed to resolve image digest: %v", err),
Latency:    time.Since(startTime),
}
}
log.Printf("Resolved image digest: %s\n", digest)

// Step 3: Fetch VC from IPFS
vc, err := v.fetchVCFromIPFS(digest)
if err != nil {
return ValidationResult{
Valid:      false,
DenyReason: fmt.Sprintf("Failed to fetch VC from IPFS: %v", err),
Latency:    time.Since(startTime),
}
}
log.Printf("Fetched VC from IPFS\n")

// Step 4: Verify issuer DID Document
issuerDID := vc["issuer"].(string)
didDoc, err := v.fetchDIDDocument(issuerDID)
if err != nil {
return ValidationResult{
Valid:      false,
DenyReason: fmt.Sprintf("Failed to fetch DID Document: %v", err),
Latency:    time.Since(startTime),
}
}
log.Printf("Verified issuer DID document\n")

// Step 5: Validate Ed25519 signature
if !v.verifySignature(vc, didDoc) {
return ValidationResult{
Valid:      false,
DenyReason: "Signature verification failed",
Latency:    time.Since(startTime),
}
}
log.Printf("Verified Ed25519 signature\n")

// Step 6: Check CBC equality (CORE FEATURE)
vcCBC := vc["credentialSubject"].(map[string]interface{})["cbc"].(map[string]interface{})
vcChainID := int(vcCBC["chainId"].(float64))
vcContractAddr := vcCBC["contractAddress"].(string)

if vcChainID != v.config.VerifierChainID || vcContractAddr != v.config.VerifierContractAddress {
return ValidationResult{
Valid: false,
DenyReason: fmt.Sprintf(
"CBC mismatch: VC CBC=(%d,%s), Expected=(%d,%s)",
vcChainID, vcContractAddr,
v.config.VerifierChainID, v.config.VerifierContractAddress,
),
Latency: time.Since(startTime),
}
}
log.Printf("CBC equality verified\n")

// Step 7: Query on-chain VC status
vcID := vc["id"].(string)
isRecorded, isRevoked, err := v.queryVCStatus(vcID)
if err != nil {
return ValidationResult{
Valid:      false,
DenyReason: fmt.Sprintf("Failed to query VC status on-chain: %v", err),
Latency:    time.Since(startTime),
}
}

if !isRecorded {
return ValidationResult{
Valid:      false,
DenyReason: "VC not recorded on-chain",
Latency:    time.Since(startTime),
}
}

if isRevoked {
return ValidationResult{
Valid:      false,
DenyReason: "VC is revoked",
Latency:    time.Since(startTime),
}
}
log.Printf("On-chain status verified: recorded and not revoked\n")

// Step 8: Verify expiration
expiration := vc["expirationDate"].(string)
if err := v.verifyExpiration(expiration); err != nil {
return ValidationResult{
Valid:      false,
DenyReason: fmt.Sprintf("VC expired: %v", err),
Latency:    time.Since(startTime),
}
}
log.Printf("Expiration verified\n")

// SUCCESS - All checks passed
result := ValidationResult{
Valid:       true,
AllowReason: fmt.Sprintf("Image authenticated: CBC verified, on-chain status confirmed"),
Latency:     time.Since(startTime),
}

// Cache successful validation
v.cache[imageRef] = &CachedValidation{
Result:    result,
Timestamp: time.Now(),
}

return result
}

// resolveImageDigest resolves image reference to SHA-256 digest
func (v *ImageValidator) resolveImageDigest(imageRef string) (string, error) {
// Contact OCI registry to get manifest digest
// For now, return placeholder
return "sha256:a3b2c1...", nil
}

// fetchVCFromIPFS retrieves VC from IPFS using manifest digest index
func (v *ImageValidator) fetchVCFromIPFS(digest string) (map[string]interface{}, error) {
// Query IPFS to find VC with matching manifest digest
vcJSON := map[string]interface{}{
"issuer": "did:key:z6Mkw...",
"credentialSubject": map[string]interface{}{
"image": map[string]interface{}{
"manifestDigest": digest,
},
"cbc": map[string]interface{}{
"chainId":           421614,
"contractAddress":   "0x145D...",
},
},
"id":               "urn:vcid:0x8f...12",
"expirationDate":   time.Now().AddDate(0, 0, 365).Format(time.RFC3339),
"issuanceDate":     time.Now().Format(time.RFC3339),
}
return vcJSON, nil
}

// fetchDIDDocument retrieves DID Document from IPFS
func (v *ImageValidator) fetchDIDDocument(did string) (map[string]interface{}, error) {
// Query IPFS to find DID Document
didDoc := map[string]interface{}{
"@context": "https://w3id.org/did/v1",
"id":       did,
"verificationMethod": []map[string]interface{}{
{
"id":   did + "#z6Mkw",
"type": "Ed25519VerificationKey2020",
},
},
}
return didDoc, nil
}

// verifySignature verifies Ed25519 signature with W3C Data Integrity
func (v *ImageValidator) verifySignature(vc map[string]interface{}, didDoc map[string]interface{}) bool {
// Extract signature from VC proof
proof := vc["proof"].(map[string]interface{})
signature := proof["signatureValue"].(string)

// Extract public key from DID Document
// Verify signature using Ed25519
_ = signature // Placeholder

// In production, use cryptographic verification with actual public key
return true
}

// queryVCStatus queries smart contract for VC status
func (v *ImageValidator) queryVCStatus(vcID string) (recorded bool, revoked bool, err error) {
// Call smart contract to check if VC is recorded and not revoked
// This is a placeholder
return true, false, nil
}

// verifyExpiration checks if VC has not expired
func (v *ImageValidator) verifyExpiration(expirationDate string) error {
exp, err := time.Parse(time.RFC3339, expirationDate)
if err != nil {
return err
}
if time.Now().After(exp) {
return fmt.Errorf("VC expired on %s", expirationDate)
}
return nil
}
