"use client";

import type { HTMLAttributes, ReactNode } from "react";

import { useSpatialRealAvatarContext } from "@/components/spatialreal-avatar/spatialreal-avatar-context";
import { cn } from "@/lib/utils";

export interface SpatialRealAvatarLoadingProps
  extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

export function SpatialRealAvatarLoading({
  className,
  children,
  ...props
}: SpatialRealAvatarLoadingProps) {
  const { downloadProgress, isLoading, status } = useSpatialRealAvatarContext();
  const progress =
    downloadProgress !== null
      ? Math.max(0, Math.min(100, downloadProgress * 100))
      : null;

  if (!isLoading) {
    return null;
  }

  return (
    <div
      className={cn(
        "absolute inset-0 z-10 flex items-center justify-center bg-black/45 p-6 backdrop-blur-md",
        className,
      )}
      {...props}
    >
      {children ?? (
        <div className="w-full max-w-xs rounded-2xl border border-white/10 bg-black/45 p-5 text-white shadow-xl">
          <div className="flex items-center gap-3">
            <div className="size-9 animate-spin rounded-full border-2 border-white/20 border-t-[var(--primary-fixed)]" />
            <div>
              <p className="text-sm font-semibold">Preparing SpatialReal avatar</p>
              <p className="text-xs capitalize text-white/65">{status}</p>
            </div>
          </div>

          {progress !== null ? (
            <div className="mt-4 space-y-2">
              <div
                aria-valuemax={100}
                aria-valuemin={0}
                aria-valuenow={progress}
                className="relative h-2 w-full overflow-hidden rounded-full bg-white/10"
                role="progressbar"
              >
                <div
                  className="h-full rounded-full bg-[var(--primary-fixed)] transition-[width] duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-white/60">
                {Math.round(progress)}% of avatar assets ready
              </p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
