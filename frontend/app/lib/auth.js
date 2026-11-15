import { getApiBaseUrl } from "./api";

export class ApiError extends Error {
  constructor(message, { status, fields } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields || {};
  }
}

async function readResponse(response) {
  let data = {};
  try {
    data = await response.json();
  } catch {
    // Keep a useful generic error for non-JSON server and proxy responses.
  }

  if (!response.ok) {
    const message =
      data.detail ||
      Object.values(data).flat().find((value) => typeof value === "string") ||
      "Request failed. Please try again.";
    throw new ApiError(message, { status: response.status, fields: data });
  }
  return data;
}

export async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...options,
      credentials: "include",
      cache: "no-store",
      headers: {
        ...(options.body && !(typeof FormData !== "undefined" && options.body instanceof FormData)
          ? { "Content-Type": "application/json" }
          : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError("The server could not be reached.");
  }
  return readResponse(response);
}

export async function getCsrfToken() {
  const data = await request("/accounts/csrf/");
  return data.csrfToken;
}

export async function postWithCsrf(path, payload) {
  const csrfToken = await getCsrfToken();
  return request(path, {
    method: "POST",
    headers: { "X-CSRFToken": csrfToken },
    ...(payload ? { body: JSON.stringify(payload) } : {}),
  });
}

export async function logIn(credentials) {
  const result = await postWithCsrf("/accounts/login/", credentials);
  // Django rotates the CSRF secret on login. Bootstrap the new token before
  // another state-changing request is attempted.
  await getCsrfToken();
  return result.user;
}

export async function registerAccount(details) {
  return postWithCsrf("/accounts/register/", details);
}

export async function logOut() {
  return postWithCsrf("/accounts/logout/");
}

export async function getCurrentUser() {
  const result = await request("/accounts/me/");
  return result.user;
}
