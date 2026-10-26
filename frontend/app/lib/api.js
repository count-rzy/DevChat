
const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_URL}/health/`, {
      method: "GET",
      cache: "no-store",
    });

    let data;

    try {
      data = await response.json();
    } catch {
      return {
        status: "error",
        database: "unknown",
      };
    }

    if (!response.ok) {
      return {
        status: "error",
        database: data.database || "unknown",
      };
    }

    return data;
  } catch (error) {
    console.error("DevChat API connection error:", error);

    return {
      status: "offline",
      database: "unknown",
    };
  }
}