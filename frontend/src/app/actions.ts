"use server";
import { cookies } from "next/headers";

type TokenPayload = {
  identity: string;
  room: string;
  token: string;
  url: string;
};

function getBackendTokenEndpoint() {
  return (
    process.env.BACKEND_TOKEN_ENDPOINT ??
    process.env.TOKEN_SERVER_URL ??
    process.env.VITE_TOKEN_ENDPOINT ??
    "http://localhost:8080/token"
  );
}

export async function getToken(roomName: string, participantName: string) {
  const endpoint = getBackendTokenEndpoint();
  const cookieStore = await cookies();
  const token = cookieStore.get("aarohi_token")?.value;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(endpoint, {
    method: "POST",
    headers,
    cache: "no-store",
    body: JSON.stringify({
      room: roomName,
      identity: participantName,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to get token from backend (${response.status})`);
  }

  const payload = (await response.json()) as Partial<TokenPayload>;
  if (!payload.token || !payload.url || !payload.room || !payload.identity) {
    throw new Error("Backend token response is missing required fields");
  }

  return payload as TokenPayload;
}

export async function logoutAction() {
  const cookieStore = await cookies();
  cookieStore.delete('aarohi_token');
  return { success: true };
}

export async function registerAction(username: string, password: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

  try {
    const response = await fetch(`${apiUrl}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    if (response.status === 409) {
      return { error: "A clinic with this ID already exists." };
    }

    if (!response.ok) {
      return { error: "Registration failed. Username must be at least 3 characters and password at least 6." };
    }

    return { success: true };
  } catch (e) {
    return { error: "Failed to connect to server." };
  }
}

export async function loginAction(username: string, password: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  try {
    const response = await fetch(`${apiUrl}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      return { error: "Invalid credentials." };
    }

    const data = await response.json();

    // Store token securely in an HTTP-only cookie
    const cookieStore = await cookies();
    cookieStore.set('aarohi_token', data.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 60 * 60 * 24, // 1 day
      path: '/',
    });

    return { success: true };
  } catch (e) {
    return { error: "Failed to connect to server." };
  }
}
