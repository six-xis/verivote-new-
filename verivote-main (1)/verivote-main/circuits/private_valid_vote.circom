pragma circom 2.0.0;

include "circomlib/circuits/poseidon.circom";

// M6B ZK profile: poseidon-v1.
//
// This circuit intentionally uses Poseidon for all in-circuit hashes. It does
// not implement the Python SHA256-to-BN254 reference hash used by the current
// demo backend, and those profiles must be aligned before a production cast
// path can depend on this circuit.
template PrivateValidVote(candidateCount, depth) {
    assert(candidateCount > 0);
    assert(depth > 0);

    // Public signals. The main component must expose them in this exact M6A
    // order:
    //   0 election_id_hash
    //   1 eligibility_root
    //   2 nullifier_hash
    //   3 commitment
    //   4 rule_hash
    signal input election_id_hash;
    signal input eligibility_root;
    signal input nullifier_hash;
    signal input commitment;
    signal input rule_hash;

    // Private witness values. Do not expose these as public signals.
    signal input vote_vector[candidateCount];
    signal input randomness;
    signal input credential_secret;
    signal input merkle_path_elements[depth];
    signal input merkle_path_indices[depth];

    // (1) vote_vector is binary, and (2) it is exactly one-hot.
    signal vote_sum[candidateCount + 1];
    vote_sum[0] <== 0;
    for (var i = 0; i < candidateCount; i++) {
        vote_vector[i] * (vote_vector[i] - 1) === 0;
        vote_sum[i + 1] <== vote_sum[i] + vote_vector[i];
    }
    vote_sum[candidateCount] === 1;

    // (3) credential_commitment = Poseidon([credential_secret]).
    component credential_hasher = Poseidon(1);
    credential_hasher.inputs[0] <== credential_secret;

    // (4) nullifier_hash = Poseidon([election_id_hash, credential_secret]).
    component nullifier_hasher = Poseidon(2);
    nullifier_hasher.inputs[0] <== election_id_hash;
    nullifier_hasher.inputs[1] <== credential_secret;
    nullifier_hasher.out === nullifier_hash;

    // (6) Recompute the eligibility Merkle root from the credential
    // commitment and a private binary left/right path.
    signal merkle_node[depth + 1];
    signal merkle_left[depth];
    signal merkle_right[depth];
    component merkle_hashers[depth];

    merkle_node[0] <== credential_hasher.out;
    for (var level = 0; level < depth; level++) {
        merkle_path_indices[level] * (merkle_path_indices[level] - 1) === 0;

        // index 0: current node is left, sibling is right.
        // index 1: sibling is left, current node is right.
        merkle_left[level] <==
            merkle_node[level]
            + merkle_path_indices[level] * (merkle_path_elements[level] - merkle_node[level]);
        merkle_right[level] <==
            merkle_path_elements[level]
            + merkle_path_indices[level] * (merkle_node[level] - merkle_path_elements[level]);

        merkle_hashers[level] = Poseidon(2);
        merkle_hashers[level].inputs[0] <== merkle_left[level];
        merkle_hashers[level].inputs[1] <== merkle_right[level];
        merkle_node[level + 1] <== merkle_hashers[level].out;
    }
    merkle_node[depth] === eligibility_root;

    // (7) Commitment binding uses a layered Poseidon hash to avoid relying on
    // large-arity Poseidon instances:
    //   vote_hash = Poseidon(vote_vector...)
    //   header_hash = Poseidon(election_id_hash, eligibility_root,
    //                          nullifier_hash, rule_hash)
    //   commitment = Poseidon(header_hash, vote_hash, randomness)
    component vote_hasher = Poseidon(candidateCount);
    for (var j = 0; j < candidateCount; j++) {
        vote_hasher.inputs[j] <== vote_vector[j];
    }

    component header_hasher = Poseidon(4);
    header_hasher.inputs[0] <== election_id_hash;
    header_hasher.inputs[1] <== eligibility_root;
    header_hasher.inputs[2] <== nullifier_hash;
    header_hasher.inputs[3] <== rule_hash;

    component commitment_hasher = Poseidon(3);
    commitment_hasher.inputs[0] <== header_hasher.out;
    commitment_hasher.inputs[1] <== vote_hasher.out;
    commitment_hasher.inputs[2] <== randomness;
    commitment_hasher.out === commitment;
}
