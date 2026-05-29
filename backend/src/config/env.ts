import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { z } from "zod";
import fs from "fs";

function getEnvDirname(): string {
  try {
    if (typeof __dirname !== "undefined") {
      return __dirname;
    }
  } catch {}

  try {
    const err = new Error();
    const stack = err.stack || "";
    const lines = stack.split("\n");
    for (const line of lines) {
      if (line.includes("env.ts") || line.includes("env.js")) {
        const match = line.match(/\(([^)]+)\)/) || line.match(/at\s+(.+)$/);
        if (match) {
          let rawPath = match[1].trim();
          // Remove trailing line/column numbers (e.g. :30:10 or :30)
          rawPath = rawPath.replace(/:\d+:\d+$/, "").replace(/:\d+$/, "");
          if (rawPath.startsWith("file://")) {
            rawPath = fileURLToPath(rawPath);
          }
          return path.dirname(rawPath);
        }
      }
    }
  } catch {}
  return "";
}

const currentDirname = getEnvDirname();

const possiblePaths = [
  path.resolve(currentDirname, "../../../.env"),
  path.resolve(currentDirname, "../../.env"),
  path.resolve(process.cwd(), "../.env"),
  path.resolve(process.cwd(), ".env"),
];

let envPath = possiblePaths[0];
for (const p of possiblePaths) {
  if (fs.existsSync(p)) {
    envPath = p;
    break;
  }
}

dotenv.config({ path: envPath });

const envSchema = z.object({
  PORT: z.preprocess((val) => (val === undefined ? undefined : Number(val)), z.number().default(5000)),
  HOST: z.string().default("0.0.0.0"),
  DATABASE_URL: z.string().min(1, "DATABASE_URL is required"),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  JWT_SECRET: z.string().min(1, "JWT_SECRET is required"),
  JWT_EXPIRES_IN: z.string().default("7d"),
  FRONTEND_URL: z.string().url().default("http://localhost:5173"),
  CORS_ALLOWED_ORIGINS: z.string().optional(),
  WEBHOOK_BASE_URL: z.string().url().optional(),
  RETELL_API_KEY: z.string().optional(),
  RETELL_AGENT_ID: z.string().optional(),
  RETELL_FROM_NUMBER: z.string().optional(),
  RETELL_WEBHOOK_SECRET: z.string().optional(),
  ML_SERVICE_TOKEN: z.string().optional(),
  ML_SERVICE_URL: z.string().url().default("http://127.0.0.1:8000"),
  ML_REQUEST_TIMEOUT_MS: z.preprocess(
    (val) => (val === undefined ? undefined : Number(val)),
    z.number().int().positive().default(5000)
  ),
  TRUST_PROXY: z.string().default("false"),
  COOKIE_SECRET: z.string().optional(), // Added for CSRF/Session if needed
}).superRefine((data, ctx) => {
  if (data.NODE_ENV === "production" && data.JWT_SECRET.length < 32) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["JWT_SECRET"],
      message: "JWT_SECRET must be at least 32 characters in production",
    });
  }

  if (data.NODE_ENV === "production" && !data.RETELL_WEBHOOK_SECRET) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["RETELL_WEBHOOK_SECRET"],
      message: "RETELL_WEBHOOK_SECRET is required in production",
    });
  }

  if (data.NODE_ENV === "production" && (!data.ML_SERVICE_TOKEN || data.ML_SERVICE_TOKEN.length < 32)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["ML_SERVICE_TOKEN"],
      message: "ML_SERVICE_TOKEN must be at least 32 characters in production",
    });
  }
});

const parsedEnv = envSchema.safeParse(process.env);

if (!parsedEnv.success) {
  console.error("❌ Invalid environment variables:", parsedEnv.error.format());
  process.exit(1);
}

export const env = parsedEnv.data;
