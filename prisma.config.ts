// Prisma 7 config — loads env vars before using them
import { config } from "dotenv";
config({ path: ".env.local" });
config({ path: ".env" }); // fallback

import { defineConfig } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
    seed: "npx tsx prisma/seed.ts",
  },
  datasource: {
    url: process.env["DATABASE_URL"],
  },
});
