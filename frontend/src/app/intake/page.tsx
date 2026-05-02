"use client";
import { useIntakeStore } from "@/store/useIntakeStore";
import { env } from "@/env";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BarVisualizer,
  useChat,
  useLocalParticipant,
  useParticipants,
  useRoomContext,
  useTranscriptions,
  useVoiceAssistant,
} from "@livekit/components-react";
import { clsx } from "clsx";
import {
  HeartPulse,
  LoaderCircle,
  MessageSquare,
  Mic,
  MicOff,
  PhoneOff,
  Send,
  TriangleAlert,
} from "lucide-react";
import { RoomEvent, type Participant } from "livekit-client";

import { getToken } from "../actions";
import {
  SpatialRealAvatarCanvas,
  SpatialRealAvatarError,
  SpatialRealAvatarFrame,
  SpatialRealAvatarLoading,
  SpatialRealAvatarProvider,
  useSpatialRealAvatarContext,
} from "@/components/spatialreal-avatar";

type TokenConnection = {
  identity: string;
  room: string;
  token: string;
  url: string;
};

type ExtractionUpdatePayload = {
  all_data?: Record<string, string>;
  message?: string;
  type?: string;
};

type TranscriptMessage = {
  id: string;
  role: "user" | "agent";
  text: string;
  timestamp: number;
};

function formatMessageTime(timestamp: number) {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function TranscriptPanel({ messages }: { messages: TranscriptMessage[] }) {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div
        ref={scrollRef}
        className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-6 py-5"
      >
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="rounded-full border border-black/8 bg-white px-4 py-2 text-sm font-medium text-black/52 shadow-sm">
              The Clinical Assistant
            </div>
          </div>
        ) : null}

        {messages.map((message) => (
          <div
            key={message.id}
            className={clsx(
              "flex w-full",
              message.role === "user" ? "justify-end" : "justify-start",
            )}
          >
            <div
              className={clsx(
                "max-w-[85%] px-4 py-3 shadow-sm",
                message.role === "user"
                  ? "bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] text-white"
                  : "bg-white text-black/80",
              )}
              style={{
                borderRadius:
                  message.role === "user"
                    ? "1.5rem 1.5rem 0.25rem 1.5rem"
                    : "1.5rem 1.5rem 1.5rem 0.25rem",
              }}
            >
              <p
                className={clsx(
                  "mb-2 text-[11px] font-semibold uppercase tracking-[0.2em]",
                  message.role === "user" ? "text-white/75" : "text-black/40",
                )}
              >
                {message.role === "user"
                  ? "You"
                  : "Aarohi"}
              </p>
              <p className="whitespace-pre-line text-sm leading-6">
                {message.text}
              </p>
              <p
                className={clsx(
                  "mt-3 text-[11px]",
                  message.role === "user" ? "text-white/70" : "text-black/38",
                )}
              >
                {formatMessageTime(message.timestamp)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

type ActiveSessionProps = {
  onCompleted: () => void;
  onDisconnect: () => void;
  setIsRegistrationComplete: React.Dispatch<React.SetStateAction<boolean>>;
};

function ActiveSession({
  onCompleted,
  onDisconnect,
  setIsRegistrationComplete,
}: ActiveSessionProps) {
  const avatar = useSpatialRealAvatarContext();
  const room = useRoomContext();
  const { state: assistantState, audioTrack } = useVoiceAssistant();
  const transcriptSegments = useTranscriptions();
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();
  const { chatMessages, send: sendChat } = useChat();
  const participants = useParticipants();

  const [chatValue, setChatValue] = useState("");
  const [micPending, setMicPending] = useState(false);
  const finishTriggeredRef = useRef(false);
  const chatInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const handleData = (
      payload: Uint8Array,
      _participant?: Participant,
      _kind?: unknown,
      topic?: string,
    ) => {
      if (topic !== "extraction_update") {
        return;
      }

      const text = new TextDecoder().decode(payload);
      let parsed: ExtractionUpdatePayload;
      try {
        parsed = JSON.parse(text) as ExtractionUpdatePayload;
      } catch {
        return;
      }

      if (parsed.type === "intake_finished") {
        setIsRegistrationComplete(true);
        if (!finishTriggeredRef.current) {
          finishTriggeredRef.current = true;
          onCompleted();
          void avatar.disconnect();
        }
        return;
      }
    };

    room.on(RoomEvent.DataReceived, handleData);
    return () => {
      room.off(RoomEvent.DataReceived, handleData);
    };
  }, [avatar, onCompleted, room, setIsRegistrationComplete]);

  const transcript = useMemo<TranscriptMessage[]>(() => {
    const transcriptionMessages = transcriptSegments.map((segment, index) => ({
      id: `transcript-${segment.participantInfo.identity}-${index}-${segment.text}`,
      role:
        segment.participantInfo.identity === localParticipant.identity
          ? ("user" as const)
          : ("agent" as const),
      text: segment.text,
      timestamp: segment.streamInfo.timestamp + index,
    }));

    const chatTimeline = chatMessages.map((message) => ({
      id: message.id,
      role:
        message.from?.identity === localParticipant.identity
          ? ("user" as const)
          : ("agent" as const),
      text: message.message,
      timestamp: message.timestamp,
    }));

    return [...transcriptionMessages, ...chatTimeline].sort(
      (a, b) => a.timestamp - b.timestamp,
    );
  }, [chatMessages, localParticipant.identity, transcriptSegments]);

  const toggleMicrophone = useCallback(async () => {
    setMicPending(true);
    try {
      const enabled = !isMicrophoneEnabled;
      await localParticipant.setMicrophoneEnabled(enabled);
      localParticipant.audioTrackPublications.forEach((publication) => {
        if (!publication.track) {
          return;
        }

        if (enabled) {
          publication.track.unmute();
        } else {
          publication.track.mute();
        }
      });
    } finally {
      setMicPending(false);
    }
  }, [isMicrophoneEnabled, localParticipant]);

  const disconnectSession = useCallback(async () => {
    await avatar.disconnect();
    onDisconnect();
  }, [avatar, onDisconnect]);

  const sendMessage = useCallback(async () => {
    const message = chatValue.trim();
    if (!message) {
      return;
    }

    await sendChat(message);
    setChatValue("");
  }, [chatValue, sendChat]);

  return (
    <div className="relative flex h-full min-h-0 flex-1 flex-col overflow-hidden lg:flex-row">
      <section className="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-[#0a0f0f]">
        <div className="absolute left-5 top-5 z-20 inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/35 px-3 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-white/78 backdrop-blur-xl">
          <span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_18px_rgba(74,222,128,0.85)]" />
          Aarohi Active
        </div>

        <div className="min-h-0 flex-1 p-4 sm:p-6">
          <SpatialRealAvatarFrame className="h-full overflow-hidden">
            <SpatialRealAvatarCanvas className="h-full" minHeight={420} />
            <SpatialRealAvatarLoading />
            <SpatialRealAvatarError />
          </SpatialRealAvatarFrame>
        </div>

        {participants.length <= 1 ? (
          <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
            <div className="flex flex-col items-center gap-5">
              <BarVisualizer
                trackRef={audioTrack}
                barCount={9}
                className="h-20 w-56"
                style={
                  {
                    "--lk-va-bar-color": "var(--primary-fixed)",
                  } as React.CSSProperties
                }
              />
              <div className="rounded-full border border-white/10 bg-black/35 px-4 py-2 text-sm font-medium text-white/80 backdrop-blur-xl">
                {assistantState === "listening"
                  ? "Aarohi Listening"
                  : assistantState === "speaking"
                    ? "Aarohi Thinking"
                    : avatar.isLoading
                      ? "Calibrating..."
                      : "Connected"}
              </div>
            </div>
          </div>
        ) : null}

        <div className="absolute inset-x-0 bottom-0 z-20 flex items-center justify-center px-4 pb-6 sm:px-6">
          <div className="glass flex items-center gap-3 rounded-full border border-white/18 px-3 py-3 shadow-2xl shadow-black/20">
            <button
              type="button"
              onClick={() => void toggleMicrophone()}
              disabled={micPending || !avatar.isConnected}
              className={clsx(
                "inline-flex size-14 items-center justify-center rounded-full text-white transition-colors",
                isMicrophoneEnabled
                  ? "bg-white/10 hover:bg-white/15"
                  : "bg-rose-600 hover:bg-rose-500",
              )}
              aria-label={
                isMicrophoneEnabled ? "Mute microphone" : "Enable microphone"
              }
            >
              {isMicrophoneEnabled ? (
                <Mic className="size-6" />
              ) : (
                <MicOff className="size-6" />
              )}
            </button>

            <button
              type="button"
              onClick={() => void disconnectSession()}
              className="inline-flex size-14 items-center justify-center rounded-full bg-rose-600 text-white transition-colors hover:bg-rose-500"
              aria-label="Disconnect"
            >
              <PhoneOff className="size-6" />
            </button>
          </div>
        </div>
      </section>

      <aside className="z-10 flex min-h-0 w-full shrink-0 flex-col overflow-hidden border-t border-black/6 bg-[var(--surface-low)] lg:w-[420px] lg:border-l lg:border-t-0">
        <header className="flex items-center justify-between border-b border-black/6 px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] text-lg font-semibold text-white">
              A
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="font-semibold tracking-tight">Aarohi </p>
                <span className="size-2 rounded-full bg-emerald-500" />
              </div>
              <p className="text-sm text-black/52">AI Nurse</p>
            </div>
          </div>
        </header>

        <TranscriptPanel messages={transcript} />

        <div className="border-t border-black/6 px-5 py-4">
          <div className="rounded-[1.5rem] border border-black/8 bg-white p-3 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-black/42">
              <MessageSquare className="size-4" />
            </div>

            <div className="mt-3 flex items-center gap-2">
              <input
                ref={chatInputRef}
                value={chatValue}
                onChange={(event) => setChatValue(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    void sendMessage();
                  }
                }}
                placeholder="Type if you prefer text..."
                className="min-w-0 flex-1 rounded-full border border-black/8 bg-[var(--surface-low)] px-4 py-3 text-base outline-none transition-colors focus:border-[var(--primary)]"
              />
              <button
                type="button"
                disabled={!chatValue.trim()}
                onClick={() => void sendMessage()}
                className={clsx(
                  "inline-flex size-12 items-center justify-center rounded-full transition-all",
                  chatValue.trim()
                    ? "bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] text-white shadow-lg shadow-teal-900/15"
                    : "bg-[var(--surface-low)] text-black/35 opacity-80",
                )}
              >
                <Send className="size-4" />
              </button>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

export default function IntakePage() {
  const router = useRouter();
  const appId = env.appId;
  const avatarId = env.avatarId;

  const [connection, setConnection] = useState<TokenConnection | null>(null);
  const [loading, setLoading] = useState(false);
  const [roomName] = useState(() => `intake-${crypto.randomUUID()}`);
  const [isRegistrationComplete, setIsRegistrationComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const participantName = `patient-${crypto.randomUUID()}`;
      const result = await getToken(roomName, participantName);
      setConnection(result);
    } catch (connectError) {
      setError(
        connectError instanceof Error
          ? connectError.message
          : "Failed to connect to Aarohi",
      );
    } finally {
      setLoading(false);
    }
  }, [appId, avatarId, roomName]);

  const handleDisconnect = useCallback(() => {
    setConnection(null);
    if (isRegistrationComplete) {
      router.push("/success");
    } else {
      router.push("/");
    }
  }, [isRegistrationComplete, router]);

  const handleCompleted = useCallback(() => {
    setConnection(null);
    setIsRegistrationComplete(true);
    router.push("/success");
  }, [router]);

  if (!connection) {
    return (
      <main className="min-h-screen bg-background text-foreground">
        <nav className="glass sticky top-0 z-50 flex items-center justify-between px-6 py-4 sm:px-10">
          <Link
            href="/"
            className="group flex items-center gap-3 transition-opacity hover:opacity-85"
          >
            <div className="flex items-center gap-2">
              <HeartPulse className="w-7 h-7 text-[var(--primary)]" />
              <span
                className="text-xl font-bold tracking-tight"
                style={{
                  fontFamily: "'Manrope', sans-serif",
                  color: "var(--primary)",
                }}
              >
                Aarohi
              </span>
            </div>
          </Link>

          <Link
            href="/"
            className="rounded-full bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] px-4 py-2 text-sm font-semibold !text-white shadow-lg shadow-teal-900/15 [text-shadow:0_1px_1px_rgba(0,62,62,0.32)]"
          >
            Back Home
          </Link>
        </nav>

        <section className="flex min-h-[calc(100vh-80px)] items-center justify-center px-6 py-12 sm:px-10">
          <div className="w-full max-w-2xl rounded-[2rem] border border-white/70 bg-white/75 p-8 text-center shadow-2xl shadow-teal-950/8 backdrop-blur-sm sm:p-12">
            <div className="mx-auto flex size-20 items-center justify-center rounded-full bg-[var(--primary-fixed)] text-[var(--primary-container)]">
              <Mic className="size-8" />
            </div>

            <h1
              className="mt-7 text-4xl tracking-[-0.03em] sm:text-5xl"
              style={{ fontFamily: "var(--font-manrope), sans-serif" }}
            >
              Ready to Converse?
            </h1>
            <p className="mx-auto mt-4 max-w-xl text-base leading-8 text-black/60 sm:text-lg">
              Start a secure session with Aarohi. Speak naturally and view live transcriptions in the terminal.
            </p>

            {error ? (
              <div className="mx-auto mt-6 flex max-w-lg items-start gap-3 rounded-[1.25rem] border border-rose-200 bg-rose-50 px-4 py-3 text-left text-sm text-rose-700">
                <TriangleAlert className="mt-0.5 size-4 shrink-0" />
                <p>{error}</p>
              </div>
            ) : null}

            <button
              type="button"
              onClick={() => void connect()}
              disabled={loading}
              className="mt-8 inline-flex items-center gap-3 rounded-full bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] px-8 py-4 text-base font-semibold text-[#d7fffb] shadow-xl shadow-teal-900/15 transition-transform hover:-translate-y-0.5 [text-shadow:0_1px_1px_rgba(0,62,62,0.28)] disabled:cursor-not-allowed disabled:opacity-80"
            >
              {loading ? (
                <>
                  <LoaderCircle className="size-5 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Mic className="size-5" />
                  Start Conversation
                </>
              )}
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="flex h-screen overflow-hidden bg-background text-foreground">
      <SpatialRealAvatarProvider
        appId={appId!}
        avatarId={avatarId!}
        connection={{
          roomName: connection.room,
          token: connection.token,
          url: connection.url,
        }}
        onAvatarError={(avatarError) => setError(avatarError.message)}
      >
        <ActiveSession
          onCompleted={handleCompleted}
          onDisconnect={handleDisconnect}
          setIsRegistrationComplete={setIsRegistrationComplete}
        />
      </SpatialRealAvatarProvider>
    </main>
  );
}
