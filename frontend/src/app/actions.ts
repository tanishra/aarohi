"use server";

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
