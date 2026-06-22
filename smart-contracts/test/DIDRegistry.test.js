const { expect } = require("chai");

describe("DIDRegistry", function () {
  let registry;
  let owner;
  let issuer;
  let signer;

  beforeEach(async function () {
    [owner, issuer, signer] = await ethers.getSigners();
    const DIDRegistry = await ethers.getContractFactory("DIDRegistry");
    registry = await DIDRegistry.deploy();
    await registry.deployed();
  });

  describe("DID Registration", function () {
    it("Should register a DID", async function () {
      const didDocument = "ipfs://QmXxxx";
      await registry.connect(issuer).registerDID(issuer.address, didDocument);
      
      const doc = await registry.getDIDDocument(issuer.address);
      expect(doc).to.equal(didDocument);
    });

    it("Should update DID document", async function () {
      const doc1 = "ipfs://QmDoc1";
      const doc2 = "ipfs://QmDoc2";
      
      await registry.connect(issuer).registerDID(issuer.address, doc1);
      await registry.connect(issuer).registerDID(issuer.address, doc2);
      
      const doc = await registry.getDIDDocument(issuer.address);
      expect(doc).to.equal(doc2);
    });
  });

  describe("VC Recording", function () {
    it("Should record a VC", async function () {
      const vcId = "0x" + "1".repeat(64);
      const credentialHash = "ipfs://QmVCHash";
      
      await registry.connect(issuer).recordVC(issuer.address, vcId, credentialHash);
      
      const status = await registry.getVCStatus(vcId);
      expect(status.recorded).to.equal(true);
      expect(status.revoked).to.equal(false);
    });

    it("Should batch record VCs", async function () {
      const vcIds = [
        "0x" + "1".repeat(64),
        "0x" + "2".repeat(64)
      ];
      const hashes = ["ipfs://QmHash1", "ipfs://QmHash2"];
      
      await registry.connect(issuer).batchRecordVC(issuer.address, vcIds, hashes);
      
      for (let vcId of vcIds) {
        const status = await registry.getVCStatus(vcId);
        expect(status.recorded).to.equal(true);
      }
    });
  });

  describe("VC Revocation", function () {
    it("Should revoke a VC", async function () {
      const vcId = "0x" + "1".repeat(64);
      const credentialHash = "ipfs://QmVCHash";
      
      await registry.connect(issuer).recordVC(issuer.address, vcId, credentialHash);
      await registry.connect(issuer).revokeVC(issuer.address, vcId);
      
      const status = await registry.getVCStatus(vcId);
      expect(status.revoked).to.equal(true);
    });
  });

  describe("Events", function () {
    it("Should emit VCRecorded event", async function () {
      const vcId = "0x" + "1".repeat(64);
      const credentialHash = "ipfs://QmVCHash";
      
      await expect(
        registry.connect(issuer).recordVC(issuer.address, vcId, credentialHash)
      ).to.emit(registry, "VCRecorded");
    });
  });
});
