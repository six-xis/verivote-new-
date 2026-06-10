import type { Express } from "express";

export async function createTestApp(): Promise<Express> {
  process.env.VERIVOTE_PERSISTENCE = "memory";
  process.env.VERIVOTE_SKIP_BOOTSTRAP = "1";

  const { app } = await import("../index.js");
  return app;
}
