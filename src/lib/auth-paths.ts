const destinations = new Set(["/dashboard", "/account"]);

export function safeNext(value: unknown): string {
  return typeof value === "string" && destinations.has(value) ? value : "/dashboard";
}

export function isProtectedPath(path: string): boolean {
  return ["/dashboard", "/account", "/api/private"].some(
    (root) => path === root || path.startsWith(root + "/"),
  );
}

export function loginPath(next: unknown): string {
  return "/login?" + new URLSearchParams({ next: safeNext(next) }).toString();
}

export function readCredentials(form: FormData, signup = false) {
  const email = form.get("email");
  const password = form.get("password");
  if (typeof email !== "string" || typeof password !== "string") return null;
  const cleanEmail = email.trim();
  if (cleanEmail.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) return null;
  if (password.length < (signup ? 12 : 1) || password.length > 128) return null;
  if (signup && form.get("confirmPassword") !== password) return null;
  return { email: cleanEmail, password };
}
