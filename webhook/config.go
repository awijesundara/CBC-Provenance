// Configuration for CBC-Provenance Webhook

package main

import (
"os"
"strconv"
)

// Config contains webhook configuration
type Config struct {
WebhookPort               string
TLSCertPath              string
TLSKeyPath               string
EnableCache              bool
CacheTTL                 int
FailClosed               bool
LogLevel                 string
VerifierChainID          int
VerifierContractAddress  string
ArbitrumRPCURL           string
IPFSAPIUrl               string
}

// NewConfig loads configuration from environment
func NewConfig() *Config {
chainID, _ := strconv.Atoi(os.Getenv("VERIFIER_CHAIN_ID"))
if chainID == 0 {
chainID = 421614 // Default to Arbitrum Sepolia
}

return &Config{
WebhookPort:              os.Getenv("WEBHOOK_PORT"),
TLSCertPath:              os.Getenv("WEBHOOK_TLS_CERT_PATH"),
TLSKeyPath:               os.Getenv("WEBHOOK_TLS_KEY_PATH"),
EnableCache:              os.Getenv("WEBHOOK_ENABLE_CACHE") == "true",
CacheTTL:                 3600, // 1 hour
FailClosed:               os.Getenv("WEBHOOK_FAIL_CLOSED") != "false",
LogLevel:                 os.Getenv("WEBHOOK_LOG_LEVEL"),
VerifierChainID:          chainID,
VerifierContractAddress:  os.Getenv("VERIFIER_CONTRACT_ADDRESS"),
ArbitrumRPCURL:           os.Getenv("ARBITRUM_RPC_URL"),
IPFSAPIUrl:               os.Getenv("IPFS_API_URL"),
}
}
