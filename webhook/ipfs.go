// IPFS interaction for CBC-Provenance

package main

// IPFSClient handles IPFS interactions
type IPFSClient struct {
ApiURL string
}

// NewIPFSClient creates a new IPFS client
func NewIPFSClient(apiURL string) (*IPFSClient, error) {
return &IPFSClient{ApiURL: apiURL}, nil
}
