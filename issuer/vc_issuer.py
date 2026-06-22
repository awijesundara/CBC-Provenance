"""
CBC-Provenance VC Issuer Service

Main issuer service for generating and publishing Verifiable Credentials
with Contract-Binding Context (CBC) to IPFS and smart contracts.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import didkit
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, validator
import web3
import ipfshttpclient

# Configuration
logger = logging.getLogger(__name__)

# ============================================================================
# Data Models
# ============================================================================

class CBCContext(BaseModel):
    """Contract-Binding Context model"""
    chainId: int = Field(..., description="Blockchain chain ID (421614 for Arbitrum Sepolia)")
    contractAddress: str = Field(..., description="Smart contract address")


class VCRequest(BaseModel):
    """Request to issue a Verifiable Credential"""
    manifestDigest: str = Field(..., description="SHA-256 digest of OCI image manifest")
    imageReference: str = Field(..., description="Image reference (e.g., docker.io/user/image)")
    chainId: int = Field(default=421614, description="Blockchain chain ID")
    contractAddress: str = Field(..., description="Smart contract address")
    expirationDays: int = Field(default=365, description="VC validity in days")
    buildMetadata: Optional[Dict[str, Any]] = Field(None, description="Optional SLSA build metadata")

    @validator('manifestDigest')
    def validate_digest(cls, v):
        """Validate SHA-256 digest format"""
        if not v.startswith('sha256:') or len(v) != 71:
            raise ValueError('Invalid SHA-256 digest format')
        return v


class VCResponse(BaseModel):
    """Response containing issued VC"""
    vcId: str = Field(..., description="Unique VC identifier")
    vc: Dict[str, Any] = Field(..., description="Verifiable Credential JSON")
    ipfsCid: str = Field(..., description="IPFS CID of published VC")
    contractTxHash: str = Field(..., description="Transaction hash of on-chain recording")


# ============================================================================
# VC Issuer Service
# ============================================================================

class VCIssuer:
    """Service for issuing and publishing Verifiable Credentials"""

    def __init__(self, issuer_did: str, issuer_key: str, web3_provider: str, ipfs_api: str):
        """
        Initialize VC Issuer

        Args:
            issuer_did: Issuer's DID (e.g., "did:key:z6Mkw...")
            issuer_key: Ed25519 private key
            web3_provider: Ethereum RPC URL
            ipfs_api: IPFS API endpoint
        """
        self.issuer_did = issuer_did
        self.issuer_key = issuer_key
        self.w3 = web3.Web3(web3.Web3.HTTPProvider(web3_provider))
        self.ipfs = ipfshttpclient.connect(ipfs_api)

    def generate_did_key(self) -> tuple[str, str]:
        """
        Generate a new did:key with Ed25519

        Returns:
            Tuple of (did, private_key_base64)
        """
        # Generate Ed25519 key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Create DID using didkit
        did = didkit.generate_ed25519_key()
        return did, did

    def create_did_document(self, did: str) -> Dict[str, Any]:
        """
        Create a W3C-compliant DID Document

        Args:
            did: The DID identifier

        Returns:
            DID Document JSON object
        """
        return {
            "@context": "https://w3id.org/did/v1",
            "id": did,
            "verificationMethod": [
                {
                    "id": f"{did}#z6Mkw",
                    "type": "Ed25519VerificationKey2020",
                    "controller": did,
                    "publicKeyBase64": "..."  # Placeholder
                }
            ],
            "assertionMethod": [f"{did}#z6Mkw"],
            "authentication": [f"{did}#z6Mkw"]
        }

    def issue_vc(self, request: VCRequest) -> Dict[str, Any]:
        """
        Issue a Verifiable Credential with CBC binding

        Args:
            request: VC issuance request

        Returns:
            Verifiable Credential JSON object
        """
        now = datetime.now(timezone.utc)
        exp = now + timedelta(days=request.expirationDays)

        vc = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://w3id.org/security/data-integrity/v1"
            ],
            "type": ["VerifiableCredential", "ContainerImageCredential"],
            "issuer": self.issuer_did,
            "issuanceDate": now.isoformat(),
            "expirationDate": exp.isoformat(),
            "credentialSubject": {
                "image": {
                    "manifestDigest": request.manifestDigest,
                    "reference": request.imageReference
                },
                "cbc": {  # Contract-Binding Context - CORE INNOVATION
                    "chainId": request.chainId,
                    "contractAddress": request.contractAddress
                }
            }
        }

        if request.buildMetadata:
            vc["credentialSubject"]["buildMetadata"] = request.buildMetadata

        return vc

    def sign_vc(self, vc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign VC using Ed25519Signature2020

        Args:
            vc: Verifiable Credential to sign

        Returns:
            Signed VC with proof
        """
        # Use didkit to sign with W3C Data Integrity
        vc_json = json.dumps(vc)
        signed_vc = didkit.issue_credential(
            vc_json,
            {"proofFormat": "Ed25519Signature2020"},
            self.issuer_key
        )
        return json.loads(signed_vc)

    def publish_to_ipfs(self, vc: Dict[str, Any], did_doc: Dict[str, Any]) -> tuple[str, str]:
        """
        Publish VC and DID Document to IPFS

        Args:
            vc: Verifiable Credential
            did_doc: DID Document

        Returns:
            Tuple of (vc_cid, did_cid)
        """
        vc_cid = self.ipfs.add_json(vc)
        did_cid = self.ipfs.add_json(did_doc)
        return vc_cid, did_cid

    def record_on_chain(self, vc_id: str, issuer_did: str, vc_cid: str) -> str:
        """
        Record VC on smart contract

        Args:
            vc_id: VC identifier hash
            issuer_did: Issuer's DID
            vc_cid: IPFS CID of VC

        Returns:
            Transaction hash
        """
        # Convert CID to bytes32
        cid_bytes = bytes.fromhex(vc_cid.replace('Qm', ''))[:32]

        # Call smart contract recordVC function
        # This is a placeholder - actual implementation would interact with contract
        logger.info(f"Recording VC {vc_id} on-chain with issuer {issuer_did}")
        return "0x..."  # Placeholder


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="CBC-Provenance Issuer",
    description="Verifiable Credential issuer for contract-bound image authentication",
    version="1.0.0"
)

# Initialize issuer (in production, load from environment)
issuer = VCIssuer(
    issuer_did="did:key:z6Mkw...",
    issuer_key="...",
    web3_provider="https://sepolia-rollup.arbitrum.io/rpc",
    ipfs_api="http://localhost:5001"
)


@app.post("/issue-vc", response_model=VCResponse, tags=["VC Operations"])
async def issue_vc(request: VCRequest) -> VCResponse:
    """
    Issue a new Verifiable Credential with CBC binding

    This endpoint:
    1. Creates a VC with CBC binding (chainId, contractAddress)
    2. Signs it with Ed25519Signature2020
    3. Publishes to IPFS
    4. Records on smart contract
    """
    try:
        # Generate VC
        vc = issuer.issue_vc(request)
        logger.info(f"Issued VC for image {request.imageReference}")

        # Sign VC
        signed_vc = issuer.sign_vc(vc)
        vc_id = signed_vc.get("id", "urn:vcid:unknown")

        # Create DID Document
        did_doc = issuer.create_did_document(issuer.issuer_did)

        # Publish to IPFS
        vc_cid, _ = issuer.publish_to_ipfs(signed_vc, did_doc)
        logger.info(f"Published VC to IPFS: {vc_cid}")

        # Record on-chain
        tx_hash = issuer.record_on_chain(vc_id, issuer.issuer_did, vc_cid)
        logger.info(f"Recorded VC on-chain: {tx_hash}")

        return VCResponse(
            vcId=vc_id,
            vc=signed_vc,
            ipfsCid=vc_cid,
            contractTxHash=tx_hash
        )

    except Exception as e:
        logger.error(f"Error issuing VC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "service": "cbc-provenance-issuer"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
