pragma circom 2.0.0;

include "./private_valid_vote.circom";

// Fixed demo / competition prototype instance:
//   candidateCount = 4
//   depth = 8
//
// Real deployments may compile separate instances for different candidate
// counts and Merkle depths. This file is not a universal production wrapper.
component main {
    public [
        election_id_hash,
        eligibility_root,
        nullifier_hash,
        commitment,
        rule_hash
    ]
} = PrivateValidVote(4, 8);
