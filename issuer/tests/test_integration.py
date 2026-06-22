import pytest
from vc_issuer import VCIssuer
import json

@pytest.fixture
def issuer():
    return VCIssuer()

def test_did_generation(issuer):
    """Test DID key generation"""
    did = issuer.generate_did_key()
    assert did.startswith("did:key:z")

def test_vc_structure(issuer):
    """Test VC includes all required fields"""
    manifest_digest = "sha256:abc123"
    vc = issuer.issue_vc(manifest_digest)
    
    assert "id" in vc
    assert "credentialSubject" in vc
    assert "proof" in vc
    assert vc["credentialSubject"]["cbc"]["chainId"] == 421614

def test_signature_verification(issuer):
    """Test Ed25519 signature verification"""
    manifest_digest = "sha256:abc123"
    vc = issuer.issue_vc(manifest_digest)
    
    # Signature should be present
    assert "signatureValue" in vc["proof"]
    assert len(vc["proof"]["signatureValue"]) > 0

def test_cbc_binding(issuer):
    """Test CBC binding is correct"""
    manifest_digest = "sha256:abc123"
    vc = issuer.issue_vc(manifest_digest)
    
    cbc = vc["credentialSubject"]["cbc"]
    assert cbc["chainId"] == 421614
    assert cbc["contractAddress"].startswith("0x")
