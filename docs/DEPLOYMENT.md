# CBC-Provenance Deployment Guide

## Prerequisites

- Arbitrum Sepolia testnet RPC access
- Node.js 16+ for smart contracts
- Python 3.11 for issuer
- Go 1.21 for webhook
- Kubernetes 1.29 with kubectl
- Docker for containerization
- IPFS node (Kubo 0.24) or gateway access

## Step 1: Deploy Smart Contract

```bash
cd smart-contracts
npm install

# Configure network in hardhat.config.js
cat > hardhat.config.js << 'HARDHAT'
require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.21",
  networks: {
    arbitrumSepolia: {
      url: "https://sepolia-rollup.arbitrum.io/rpc",
      accounts: [process.env.DEPLOYER_PRIVATE_KEY]
    }
  }
};
HARDHAT

# Deploy contract
npx hardhat run scripts/deploy.js --network arbitrumSepolia
```

**Output: Note the deployed contract address (e.g., 0x145D...)**

## Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with:
#   ARBITRUM_CONTRACT_ADDRESS=0x145D...  (from step 1)
#   ARBITRUM_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc
#   ISSUER_DID=did:key:z6Mkw...
#   VERIFIER_CONTRACT_ADDRESS=0x145D...
```

## Step 3: Deploy Issuer Node

```bash
cd issuer
pip install -r requirements.txt

# Generate issuer DID
python -c "from vc_issuer import VCIssuer; print(VCIssuer.generate_did_key())"

# Update .env with issuer DID and private key

# Run issuer
python vc_issuer.py
```

**Issuer is now listening on http://localhost:8000**

## Step 4: Deploy Admission Webhook to Kubernetes

```bash
# Create namespace
kubectl create namespace cbc-provenance

# Create TLS certificate (using cert-manager)
kubectl apply -f - << 'K8S'
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: cbc-webhook-tls
  namespace: cbc-provenance
spec:
  secretName: cbc-webhook-tls
  issuerRef:
    name: selfsigned-issuer
    kind: Issuer
K8S

# Build and push webhook image
docker build -t myregistry/cbc-webhook:latest webhook/
docker push myregistry/cbc-webhook:latest

# Deploy webhook
kubectl apply -f - << 'K8S'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cbc-webhook
  namespace: cbc-provenance
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cbc-webhook
  template:
    metadata:
      labels:
        app: cbc-webhook
    spec:
      containers:
      - name: webhook
        image: myregistry/cbc-webhook:latest
        ports:
        - containerPort: 8443
        env:
        - name: VERIFIER_CHAIN_ID
          value: "421614"
        - name: VERIFIER_CONTRACT_ADDRESS
          value: "0x145D..."
        - name: ARBITRUM_RPC_URL
          value: "https://sepolia-rollup.arbitrum.io/rpc"
        - name: IPFS_API_URL
          value: "http://ipfs-service:5001"
        volumeMounts:
        - name: webhook-certs
          mountPath: /etc/webhook/certs
          readOnly: true
      volumes:
      - name: webhook-certs
        secret:
          secretName: cbc-webhook-tls
K8S

# Verify webhook is running
kubectl get pods -n cbc-provenance
```

## Step 5: Configure Validating Webhook Rule

```bash
kubectl apply -f - << 'K8S'
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: cbc-image-validator
webhooks:
- name: validate.cbc-provenance.io
  clientConfig:
    service:
      name: cbc-webhook
      namespace: cbc-provenance
      path: "/mutate"
    caBundle: <base64-encoded-ca-cert>
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  failurePolicy: Fail
  sideEffects: None
  admissionReviewVersions: ["v1"]
  clientConfig:
    timeoutSeconds: 5
K8S
```

## Step 6: Test Image Admission

```bash
# Create a pod with a container image that has valid CBC credential
kubectl run test-pod \
  --image=docker.io/myorg/myapp@sha256:a3b2c1... \
  --namespace default

# Expected: Pod is admitted because:
# 1. Image digest resolves
# 2. VC is found in IPFS
# 3. Signature validates
# 4. CBC matches expected contract
# 5. VC is recorded on-chain and not revoked
```

## Verification

```bash
# Check issuer is running
curl http://localhost:8000/health

# Check webhook logs
kubectl logs -n cbc-provenance -l app=cbc-webhook -f

# Query smart contract
# Using web3.py or ethers.js to call getVCStatus()

# Check IPFS
ipfs cat /ipfs/QmXxxx...  # VC CID
```

## Production Considerations

1. **High Availability:** Deploy webhook with 3+ replicas
2. **caching:** Enable admission cache (TTL: 1 hour)
3. **Monitoring:** Set up Prometheus metrics for webhook latency
4. **Rate Limiting:** Implement per-issuer rate limits
5. **Key Management:** Use HSM/TPM for private keys
6. **Audit Logging:** Enable Kubernetes audit logs for admission decisions
