"use client";

import type { HTMLAttributes, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

import { useSpatialRealAvatarContext } from "@/components/spatialreal-avatar/spatialreal-avatar-context";
import { cn } from "@/lib/utils";

export interface SpatialRealAvatarErrorProps
  extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

export function SpatialRealAvatarError({
  className,
  children,
  ...props
}: SpatialRealAvatarErrorProps) {
  const { error, status } = useSpatialRealAvatarContext();

  if (status !== "error" || !error) {
    return null;
  }

  return (
    <div
      className={cn(
        "absolute inset-0 z-20 flex items-center justify-center bg-black/70 p-6 backdrop-blur-md",
        className,
      )}
      {...props}
    >
      {children ?? (
        <div className="max-w-sm rounded-2xl border border-rose-500/30 bg-black/55 p-5 text-white shadow-xl">
          <div className="flex items-start gap-3">
            <span className="rounded-full bg-rose-500/10 p-2 text-rose-400">
              <AlertTriangle className="size-4" />
            </span>
            <div className="space-y-1">
              <p className="text-sm font-semibold">Avatar connection failed</p>
              <p className="text-sm text-white/70">{error.message}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
