import request from "supertest";
import { beforeAll, describe, expect, it } from "vitest";
import { createTestApp } from "../../apps/api/src/test-utils/createTestApp";

let app: Awaited<ReturnType<typeof createTestApp>>;

beforeAll(async () => {
  app = await createTestApp();
});

describe("API basic voting flow", () => {
  it("creates an election, adds a candidate, registers a user, casts one vote, rejects a duplicate, and generates an audit report", async () => {
    const suffix = `basic-${Date.now()}`;

    const electionResponse = await request(app)
      .post("/elections")
      .send({
        title: `Security baseline ${suffix}`,
        description: "API regression test election"
      })
      .expect(201);

    expect(electionResponse.body.election).toMatchObject({
      title: `Security baseline ${suffix}`,
      status: "active"
    });
    const electionId = electionResponse.body.election.id as string;

    const candidateResponse = await request(app)
      .post(`/elections/${electionId}/candidates`)
      .send({ name: "Candidate A" })
      .expect(201);

    expect(candidateResponse.body.candidate).toMatchObject({
      electionId,
      name: "Candidate A"
    });
    const candidateId = candidateResponse.body.candidate.id as string;

    const userResponse = await request(app)
      .post("/users/register")
      .send({ name: `Voter ${suffix}` })
      .expect(201);

    expect(userResponse.body.user).toMatchObject({
      name: `Voter ${suffix}`
    });
    const userId = userResponse.body.userId as string;

    const voteResponse = await request(app)
      .post(`/elections/${electionId}/vote`)
      .send({ userId, candidateId })
      .expect(201);

    expect(voteResponse.body).toMatchObject({
      voteId: expect.any(String),
      receiptCode: expect.any(String),
      commitment: expect.any(String),
      receiptChainIndex: 0
    });

    const duplicateResponse = await request(app)
      .post(`/elections/${electionId}/vote`)
      .send({ userId, candidateId })
      .expect(409);

    expect(duplicateResponse.body.error).toEqual(expect.any(String));

    const auditResponse = await request(app)
      .post(`/aggregator/elections/${electionId}/run`)
      .expect(201);

    expect(auditResponse.body.report).toMatchObject({
      electionId,
      totalVotes: 1,
      validVotes: 1,
      invalidVotes: 0,
      duplicateVotes: 0,
      receiptChainVerified: true,
      auditHash: expect.any(String)
    });
  });
});
