"use client";

import type { ComponentPropsWithoutRef } from "react";

import { cn } from "@/lib/utils";

export type SpatialRealAvatarFrameProps = ComponentPropsWithoutRef<"div">;

export function SpatialRealAvatarFrame({
  className,
  ...props
}: SpatialRealAvatarFrameProps) {
  return (
    <div
      className={cn(
        "relative isolate overflow-hidden rounded-[28px] border border-white/10 bg-black/10 text-white shadow-[0_28px_90px_-40px_rgba(0,0,0,0.45)] backdrop-blur-sm",
        className,
      )}
      {...props}
    />
  );
}
