import "dotenv/config";

export const env = {
  PORT: Number(process.env.PORT || 5000),
  DATABASE_URL: process.env.DATABASE_URL || "",
  NODE_ENV: process.env.NODE_ENV || "development",
  JWT_SECRET: process.env.JWT_SECRET || "",
};

if (!env.DATABASE_URL) {
  throw new Error("DATABASE_URL is missing in .env");
}