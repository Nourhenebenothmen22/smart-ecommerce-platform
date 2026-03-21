import bcrypt from "bcryptjs";

/**
 * Hashes a plain text password using bcrypt.
 * @param password The plain text password to hash.
 * @param saltRounds The number of salt rounds to use (default: 12 for high security).
 * @returns A promise that resolves to the hashed password.
 */
export async function hashPassword(password: string, saltRounds: number = 12): Promise<string> {
  return bcrypt.hash(password, saltRounds);
}

/**
 * Compares a plain text password with a hashed password.
 * @param password The plain text password to check.
 * @param hash The hashed password to compare against.
 * @returns A promise that resolves to true if the passwords match, false otherwise.
 */
export async function comparePassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
