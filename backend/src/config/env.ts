import "dotenv/config";

export const env = {
  PORT: Number(process.env.PORT || 5000),
  DATABASE_URL: process.env.DATABASE_URL || "",
  NODE_ENV: process.env.NODE_ENV || "development",
  JWT_SECRET: process.env.JWT_SECRET || "",
  FRONTEND_URL: process.env.FRONTEND_URL || "http://localhost:5173",
};

if (!env.DATABASE_URL) {
  throw new Error("DATABASE_URL is missing in .env");
}

if (!env.JWT_SECRET && env.NODE_ENV === "production") {
  throw new Error("JWT_SECRET is missing in .env (required in production)");
}