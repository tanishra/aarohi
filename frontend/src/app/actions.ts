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

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
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
