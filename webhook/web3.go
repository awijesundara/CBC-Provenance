// Ethereum/Arbitrum interaction for CBC-Provenance

package main

// Web3Client handles blockchain interactions
type Web3Client struct {
RpcURL string
}

// NewWeb3Client creates a new Web3 client
func NewWeb3Client(rpcURL string) (*Web3Client, error) {
return &Web3Client{RpcURL: rpcURL}, nil
}
