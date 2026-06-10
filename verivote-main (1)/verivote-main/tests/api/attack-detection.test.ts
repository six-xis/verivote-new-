import request from "supertest";
import { beforeAll, describe, expect, it } from "vitest";
import { createTestApp } from "../../apps/api/src/test-utils/createTestApp";

let app: Awaited<ReturnType<typeof createTestApp>>;

beforeAll(async () => {
  app = await createTestApp();
});

async function createElectionWithVotes(label: string, voteCount = 1): Promise<{
  electionId: string;
  candidateId: string;
}> {
  const suffix = `${label}-${Date.now()}-${Math.random().toString(16).slice(2)}`;

  const electionResponse = await request(app)
    .post("/elections")
    .send({
      title: `Attack regression ${suffix}`,
      description: "Attack detection regression fixture"
    })
    .expect(201);
  const electionId = electionResponse.body.election.id as string;

  const candidateResponse = await request(app)
    .post(`/elections/${electionId}/candidates`)
    .send({ name: "Candidate A" })
    .expect(201);
  const candidateId = candidateResponse.body.candidate.id as string;

  for (let index = 0; index < voteCount; index += 1) {
    const userResponse = await request(app)
      .post("/users/register")
      .send({ name: `Attack voter ${suffix}-${index}` })
      .expect(201);

    await request(app)
      .post(`/elections/${electionId}/vote`)
      .send({
        userId: userResponse.body.userId,
        candidateId
      })
      .expect(201);
  }

  return { electionId, candidateId };
}

describe("API attack detection baseline", () => {
  it("passes a normal audit report", async () => {
    const { electionId } = await createElectionWithVotes("normal", 2);

    const auditResponse = await request(app)
      .post(`/aggregator/elections/${electionId}/run`)
      .expect(201);

    expect(auditResponse.body.report).toMatchObject({
      electionId,
      totalVotes: 2,
      validVotes: 2,
      invalidVotes: 0,
      duplicateVotes: 0,
      receiptChainVerified: true,
      pedersenTallyVerified: true
    });
  });

  it("detects a tampered vote commitment in the audit report", async () => {
    const { electionId } = await createElectionWithVotes("tamper-commitment", 1);

    await request(app)
      .post(`/attack/elections/${electionId}/tamper-commitment`)
      .expect(200);

    const auditResponse = await request(app)
      .post(`/aggregator/elections/${electionId}/run`)
      .expect(201);

    expect(auditResponse.body.report).toMatchObject({
      electionId,
      totalVotes: 1,
      validVotes: 1,
      invalidVotes: 0,
      duplicateVotes: 0,
      receiptChainVerified: false,
      pedersenTallyVerified: false
    });
    expect(auditResponse.body.report.receiptChainBreaks.length).toBeGreaterThan(0);
  });

  it("detects an injected duplicate vote in the audit report", async () => {
    const { electionId } = await createElectionWithVotes("duplicate", 1);

    await request(app)
      .post(`/attack/elections/${electionId}/inject-duplicate-vote`)
      .expect(200);

    const auditResponse = await request(app)
      .post(`/aggregator/elections/${electionId}/run`)
      .expect(201);

    expect(auditResponse.body.report).toMatchObject({
      electionId,
      totalVotes: 2,
      validVotes: 1,
      invalidVotes: 0,
      duplicateVotes: 1
    });
    expect(auditResponse.body.report.duplicateTokenHashes.length).toBeGreaterThan(0);
  });
});
