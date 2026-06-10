import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { buildPoseidon } from "circomlibjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "../..");
const inputDir = path.join(rootDir, "circuits", "inputs");
const artifactDir = path.join(rootDir, "artifacts", "zk", "private_valid_vote");

const candidateCount = 4;
const depth = 8;
const leafCount = 1 << depth;
const credentialIndex = 37;

function asString(value) {
  return value.toString();
}

function writeJson(filePath, value) {
  return writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function tamperFieldElement(value, field) {
  return asString(field.add(field.e(value), field.e(1)));
}

function buildMerklePath(leaves, targetIndex, poseidon, field) {
  let level = leaves.slice();
  let index = targetIndex;
  const elements = [];
  const indices = [];

  for (let currentDepth = 0; currentDepth < depth; currentDepth += 1) {
    const isRight = index % 2 === 1;
    const siblingIndex = isRight ? index - 1 : index + 1;
    elements.push(level[siblingIndex]);
    indices.push(isRight ? "1" : "0");

    const nextLevel = [];
    for (let i = 0; i < level.length; i += 2) {
      nextLevel.push(field.toString(poseidon([level[i], level[i + 1]])));
    }
    level = nextLevel;
    index = Math.floor(index / 2);
  }

  return {
    root: level[0],
    merkle_path_elements: elements,
    merkle_path_indices: indices,
  };
}

function buildCommitment(poseidon, field, {
  electionIdHash,
  eligibilityRoot,
  nullifierHash,
  ruleHash,
  voteVector,
  randomness,
}) {
  const voteHash = field.toString(poseidon(voteVector));
  const headerHash = field.toString(
    poseidon([electionIdHash, eligibilityRoot, nullifierHash, ruleHash]),
  );
  return field.toString(poseidon([headerHash, voteHash, randomness]));
}

function buildInput({
  electionIdHash,
  eligibilityRoot,
  nullifierHash,
  commitment,
  ruleHash,
  voteVector,
  randomness,
  credentialSecret,
  merklePath,
}) {
  return {
    election_id_hash: electionIdHash,
    eligibility_root: eligibilityRoot,
    nullifier_hash: nullifierHash,
    commitment,
    rule_hash: ruleHash,
    vote_vector: voteVector,
    randomness,
    credential_secret: credentialSecret,
    merkle_path_elements: merklePath.merkle_path_elements,
    merkle_path_indices: merklePath.merkle_path_indices,
  };
}

const poseidon = await buildPoseidon();
const field = poseidon.F;

const electionIdHash = "123456789";
const ruleHash = "987654321";
const credentialSecret = "42424242";
const randomness = "7777777";
const voteVector = ["1", "0", "0", "0"];
const overvoteVector = ["1", "1", "0", "0"];

const credentialCommitment = field.toString(poseidon([credentialSecret]));
const nullifierHash = field.toString(poseidon([electionIdHash, credentialSecret]));

const leaves = Array.from({ length: leafCount }, (_, index) => {
  if (index === credentialIndex) {
    return credentialCommitment;
  }
  return field.toString(poseidon([BigInt(100000 + index)]));
});
const merklePath = buildMerklePath(leaves, credentialIndex, poseidon, field);
const eligibilityRoot = merklePath.root;

const commitment = buildCommitment(poseidon, field, {
  electionIdHash,
  eligibilityRoot,
  nullifierHash,
  ruleHash,
  voteVector,
  randomness,
});
const overvoteCommitment = buildCommitment(poseidon, field, {
  electionIdHash,
  eligibilityRoot,
  nullifierHash,
  ruleHash,
  voteVector: overvoteVector,
  randomness,
});

const validInput = buildInput({
  electionIdHash,
  eligibilityRoot,
  nullifierHash,
  commitment,
  ruleHash,
  voteVector,
  randomness,
  credentialSecret,
  merklePath,
});

const invalidOvervoteInput = buildInput({
  electionIdHash,
  eligibilityRoot,
  nullifierHash,
  commitment: overvoteCommitment,
  ruleHash,
  voteVector: overvoteVector,
  randomness,
  credentialSecret,
  merklePath,
});

const invalidMembershipPath = {
  merkle_path_elements: merklePath.merkle_path_elements.slice(),
  merkle_path_indices: merklePath.merkle_path_indices.slice(),
};
invalidMembershipPath.merkle_path_elements[0] = tamperFieldElement(
  invalidMembershipPath.merkle_path_elements[0],
  field,
);

const invalidMembershipInput = buildInput({
  electionIdHash,
  eligibilityRoot,
  nullifierHash,
  commitment,
  ruleHash,
  voteVector,
  randomness,
  credentialSecret,
  merklePath: invalidMembershipPath,
});

const expectedPublicSignals = [
  electionIdHash,
  eligibilityRoot,
  nullifierHash,
  commitment,
  ruleHash,
];

await mkdir(inputDir, { recursive: true });
await mkdir(artifactDir, { recursive: true });

await writeJson(path.join(inputDir, "private_valid_vote.valid.json"), validInput);
await writeJson(
  path.join(inputDir, "private_valid_vote.invalid_overvote.json"),
  invalidOvervoteInput,
);
await writeJson(
  path.join(inputDir, "private_valid_vote.invalid_membership.json"),
  invalidMembershipInput,
);
await writeJson(
  path.join(artifactDir, "public_signals_expected.json"),
  expectedPublicSignals,
);

console.log("Generated Poseidon-consistent private_valid_vote inputs:");
console.log(`- ${path.join(inputDir, "private_valid_vote.valid.json")}`);
console.log(`- ${path.join(inputDir, "private_valid_vote.invalid_overvote.json")}`);
console.log(`- ${path.join(inputDir, "private_valid_vote.invalid_membership.json")}`);
console.log(`- ${path.join(artifactDir, "public_signals_expected.json")}`);
