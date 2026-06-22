// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

/**
 * @title DIDRegistry
 * @author CBC-Provenance Team
 * @notice Manages DIDs, Verifiable Credentials, and their lifecycle on Arbitrum
 * @dev Smart contract for contract-bound credential management
 */

contract DIDRegistry {
    // ============================================================================
    // Type Definitions
    // ============================================================================

    /// @notice VC Status information
    struct VCStatus {
        bytes32 vcId;
        string issuerDid;
        uint256 issuanceTimestamp;
        bool isRevoked;
        bool isRecorded;
    }

    // ============================================================================
    // State Variables
    // ============================================================================

    /// @notice Maps DID identifier to IPFS CID hash of DID Document
    mapping(string => bytes32) public didToCid;

    /// @notice Maps DID identifier to owner address (for access control)
    mapping(string => address) public didToOwner;

    /// @notice Maps VC ID to issuer DID
    mapping(bytes32 => string) public vcToIssuer;

    /// @notice Maps VC ID to issuance timestamp
    mapping(bytes32 => uint256) public vcToTimestamp;

    /// @notice Maps VC ID to revocation status
    mapping(bytes32 => bool) public vcRevoked;

    /// @notice Maps VC ID to recorded status
    mapping(bytes32 => bool) public vcRecorded;

    /// @notice Contract owner
    address public owner;

    // ============================================================================
    // Events
    // ============================================================================

    /// @notice Emitted when a new DID is registered
    event DIDRegistered(string indexed did, bytes32 cidHash, address indexed owner);

    /// @notice Emitted when a VC is recorded on-chain
    event VCRecorded(bytes32 indexed vcId, string indexed issuerDid, uint256 issuanceTs);

    /// @notice Emitted when a VC is revoked
    event VCRevoked(bytes32 indexed vcId, string indexed issuerDid);

    /// @notice Emitted when a DID owner is updated
    event DIDOwnerUpdated(string indexed did, address indexed newOwner);

    // ============================================================================
    // Modifiers
    // ============================================================================

    /// @notice Ensures caller is contract owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not owner");
        _;
    }

    /// @notice Ensures caller is DID owner or contract owner
    modifier onlyDIDOwner(string calldata did) {
        require(
            msg.sender == didToOwner[did] || msg.sender == owner,
            "Not authorized for this DID"
        );
        _;
    }

    // ============================================================================
    // Constructor
    // ============================================================================

    constructor() {
        owner = msg.sender;
    }

    // ============================================================================
    // DID Registry Functions
    // ============================================================================

    /**
     * @notice Register a new DID with its IPFS CID hash
     * @param did The DID identifier (e.g., "did:key:z6Mkw...")
     * @param cidHash The bytes32 hash of the IPFS CID containing DID Document
     * @dev Only callable by DID owner or contract owner
     */
    function registerDID(string calldata did, bytes32 cidHash) external {
        require(bytes(did).length > 0, "DID cannot be empty");
        require(cidHash != bytes32(0), "CID hash cannot be zero");

        // First registration - sender becomes owner
        if (didToOwner[did] == address(0)) {
            didToOwner[did] = msg.sender;
        } else {
            // Subsequent updates - must be owner
            require(msg.sender == didToOwner[did], "Not DID owner");
        }

        didToCid[did] = cidHash;
        emit DIDRegistered(did, cidHash, didToOwner[did]);
    }

    /**
     * @notice Get the IPFS CID hash for a registered DID
     * @param did The DID identifier
     * @return The bytes32 CID hash of the DID Document
     */
    function getDIDDocument(string calldata did)
        external
        view
        returns (bytes32)
    {
        return didToCid[did];
    }

    /**
     * @notice Check if a DID is registered
     * @param did The DID identifier
     * @return True if DID is registered
     */
    function isDIDRegistered(string calldata did)
        external
        view
        returns (bool)
    {
        return didToOwner[did] != address(0);
    }

    /**
     * @notice Set the owner of a DID
     * @param did The DID identifier
     * @param newOwner The new owner address
     */
    function setDIDOwner(string calldata did, address newOwner)
        external
        onlyDIDOwner(did)
    {
        require(newOwner != address(0), "Invalid owner address");
        didToOwner[did] = newOwner;
        emit DIDOwnerUpdated(did, newOwner);
    }

    /**
     * @notice Check if an address is the owner of a DID
     * @param did The DID identifier
     * @param caller The address to check
     * @return True if caller owns the DID
     */
    function isDIDOwner(string calldata did, address caller)
        external
        view
        returns (bool)
    {
        return didToOwner[did] == caller;
    }

    // ============================================================================
    // VC State Management Functions
    // ============================================================================

    /**
     * @notice Record a VC on-chain
     * @param vcId The bytes32 hash of the VC ID
     * @param issuerDid The issuer's DID
     * @param issuanceTs The VC issuance timestamp
     * @dev Only callable by the DID owner
     */
    function recordVC(
        bytes32 vcId,
        string calldata issuerDid,
        uint256 issuanceTs
    ) external onlyDIDOwner(issuerDid) {
        require(vcId != bytes32(0), "VC ID cannot be zero");
        require(issuanceTs > 0, "Invalid issuance timestamp");
        require(
            didToOwner[issuerDid] != address(0),
            "Issuer DID not registered"
        );

        vcToIssuer[vcId] = issuerDid;
        vcToTimestamp[vcId] = issuanceTs;
        vcRecorded[vcId] = true;

        emit VCRecorded(vcId, issuerDid, issuanceTs);
    }

    /**
     * @notice Record multiple VCs in a single transaction (batch operation)
     * @param vcIds Array of VC ID hashes
     * @param issuerDid The issuer's DID
     * @param issuanceTs The VC issuance timestamp
     * @dev Gas-optimized batch operation
     */
    function batchRecordVC(
        bytes32[] calldata vcIds,
        string calldata issuerDid,
        uint256 issuanceTs
    ) external onlyDIDOwner(issuerDid) {
        require(vcIds.length > 0, "Must provide at least one VC");
        require(
            didToOwner[issuerDid] != address(0),
            "Issuer DID not registered"
        );

        for (uint256 i = 0; i < vcIds.length; i++) {
            require(vcIds[i] != bytes32(0), "VC ID cannot be zero");
            vcToIssuer[vcIds[i]] = issuerDid;
            vcToTimestamp[vcIds[i]] = issuanceTs;
            vcRecorded[vcIds[i]] = true;
            emit VCRecorded(vcIds[i], issuerDid, issuanceTs);
        }
    }

    /**
     * @notice Revoke a VC
     * @param vcId The bytes32 hash of the VC ID
     * @dev Only callable by the issuer of the VC
     */
    function revokeVC(bytes32 vcId) external {
        require(vcId != bytes32(0), "VC ID cannot be zero");
        require(vcRecorded[vcId], "VC not recorded");

        string memory issuerDid = vcToIssuer[vcId];
        require(msg.sender == didToOwner[issuerDid], "Not VC issuer");

        vcRevoked[vcId] = true;
        emit VCRevoked(vcId, issuerDid);
    }

    /**
     * @notice Get the status of a VC
     * @param vcId The bytes32 hash of the VC ID
     * @return VCStatus struct containing all VC status information
     */
    function getVCStatus(bytes32 vcId)
        external
        view
        returns (VCStatus memory)
    {
        return
            VCStatus({
                vcId: vcId,
                issuerDid: vcToIssuer[vcId],
                issuanceTimestamp: vcToTimestamp[vcId],
                isRevoked: vcRevoked[vcId],
                isRecorded: vcRecorded[vcId]
            });
    }

    /**
     * @notice Check if a VC is recorded on-chain
     * @param vcId The bytes32 hash of the VC ID
     * @return True if VC is recorded
     */
    function isVCRecorded(bytes32 vcId) external view returns (bool) {
        return vcRecorded[vcId];
    }

    /**
     * @notice Check if a VC is revoked
     * @param vcId The bytes32 hash of the VC ID
     * @return True if VC is revoked
     */
    function isVCRevoked(bytes32 vcId) external view returns (bool) {
        return vcRevoked[vcId];
    }

    /**
     * @notice Check if a VC is valid (recorded and not revoked)
     * @param vcId The bytes32 hash of the VC ID
     * @return True if VC is valid
     */
    function isVCValid(bytes32 vcId) external view returns (bool) {
        return vcRecorded[vcId] && !vcRevoked[vcId];
    }

    /**
     * @notice Get the issuer of a VC
     * @param vcId The bytes32 hash of the VC ID
     * @return The issuer's DID
     */
    function getVCIssuer(bytes32 vcId)
        external
        view
        returns (string memory)
    {
        return vcToIssuer[vcId];
    }

    /**
     * @notice Get the issuance timestamp of a VC
     * @param vcId The bytes32 hash of the VC ID
     * @return The issuance timestamp
     */
    function getVCIssuanceTimestamp(bytes32 vcId)
        external
        view
        returns (uint256)
    {
        return vcToTimestamp[vcId];
    }
}
