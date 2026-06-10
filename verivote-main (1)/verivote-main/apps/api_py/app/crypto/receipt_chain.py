from dataclasses import dataclass

from app.crypto.hash_utils import hash_object, sha256_hex


@dataclass(frozen=True)
class ReceiptChainInput:
    election_id: str
    receipt_code: str
    previous_receipt_code_hash: str | None
    receipt_chain_index: int
    commitment: str


@dataclass(frozen=True)
class ReceiptChainBreak:
    ballot_id: str | None
    index: int
    reason: str


@dataclass(frozen=True)
class ReceiptChainVerification:
    verified: bool
    breaks: list[ReceiptChainBreak]


def hash_receipt_code(receipt_code: str) -> str:
    return sha256_hex(receipt_code)


def create_receipt_chain_hash(value: ReceiptChainInput) -> str:
    return hash_object(
        "verivote.receipt_chain.v1",
        {
            "election_id": value.election_id,
            "receipt_code": value.receipt_code,
            "previous_receipt_code_hash": value.previous_receipt_code_hash,
            "receipt_chain_index": value.receipt_chain_index,
            "commitment": value.commitment,
        },
    )


def verify_receipt_chain(ballots: list) -> ReceiptChainVerification:
    breaks: list[ReceiptChainBreak] = []
    sorted_ballots = sorted(ballots, key=lambda ballot: ballot.receipt_chain_index)

    for expected_index, ballot in enumerate(sorted_ballots):
        if ballot.receipt_chain_index != expected_index:
            breaks.append(
                ReceiptChainBreak(
                    ballot_id=ballot.id,
                    index=ballot.receipt_chain_index,
                    reason=f"receiptChainIndex sequence break: expected {expected_index}",
                )
            )

        previous_ballot = sorted_ballots[expected_index - 1] if expected_index > 0 else None
        expected_previous = (
            None if previous_ballot is None else hash_receipt_code(previous_ballot.receipt_code)
        )
        if ballot.previous_receipt_code_hash != expected_previous:
            breaks.append(
                ReceiptChainBreak(
                    ballot_id=ballot.id,
                    index=ballot.receipt_chain_index,
                    reason="previousReceiptCodeHash does not match",
                )
            )

        expected_hash = create_receipt_chain_hash(
            ReceiptChainInput(
                election_id=ballot.election_id,
                receipt_code=ballot.receipt_code,
                previous_receipt_code_hash=expected_previous,
                receipt_chain_index=ballot.receipt_chain_index,
                commitment=ballot.commitment,
            )
        )
        if ballot.receipt_chain_hash != expected_hash:
            breaks.append(
                ReceiptChainBreak(
                    ballot_id=ballot.id,
                    index=ballot.receipt_chain_index,
                    reason="receiptChainHash does not match recomputed chain hash",
                )
            )

    return ReceiptChainVerification(verified=not breaks, breaks=breaks)

