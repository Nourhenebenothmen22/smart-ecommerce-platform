export function parseTrustProxy(value: string): false | true | number {
  const normalized = value.trim().toLowerCase();
  if (!normalized || normalized === "false" || normalized === "0") return false;
  if (normalized === "true") return true;
  const parsed = Number(normalized);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : false;
}
