/**
 * Merge class names: combines clsx and tailwind-merge so Tailwind classes
 * override correctly (e.g. "p-4 p-2" becomes "p-2").
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
