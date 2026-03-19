/**
 * Button to import a spreadsheet from Google Drive: OAuth, picker, then POST to backend.
 * Requires VITE_GOOGLE_CLIENT_ID. Success/error feedback uses Sonner toasts so the filter bar stays compact.
 */
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CloudDownload, Loader2 } from "lucide-react";
import { importGoogleDriveFile } from "@/api/energyApi";
import { toast } from "@/components/ui/sonner";

const DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly";

type ImportStatus = "idle" | "loading" | "picking" | "importing";

export function GoogleDriveImportButton() {
  const [status, setStatus] = useState<ImportStatus>("idle");
  const queryClient = useQueryClient();
  const clientId = typeof import.meta !== "undefined" && import.meta.env?.VITE_GOOGLE_CLIENT_ID;

  /** Call the backend to import the file, then refresh all dashboard data. */
  const runImport = async (accessToken: string, fileId: string) => {
    setStatus("importing");
    try {
      const result = await importGoogleDriveFile(accessToken, fileId);
      toast.success("Import complete", { description: result.message });
      await queryClient.invalidateQueries({ queryKey: ["dateRange"] });
      await queryClient.invalidateQueries({ queryKey: ["summary"] });
      await queryClient.invalidateQueries({ queryKey: ["timeseries"] });
      await queryClient.invalidateQueries({ queryKey: ["tenants"] });
      await queryClient.invalidateQueries({ queryKey: ["sharing"] });
      await queryClient.invalidateQueries({ queryKey: ["quality"] });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Import failed");
    } finally {
      setStatus("idle");
    }
  };

  const openPicker = (accessToken: string) => {
    if (!window.gapi) {
      toast.error("Google Picker not loaded. Refresh the page.");
      setStatus("idle");
      return;
    }
    window.gapi.load("picker", () => {
      const google = window.google;
      if (!google?.picker) {
        toast.error("Google Picker not available.");
        setStatus("idle");
        return;
      }
      const picker = new google.picker.PickerBuilder()
        .setOAuthToken(accessToken)
        .addView(new google.picker.DocsView(google.picker.ViewId.SPREADSHEETS))
        .setCallback((data: { action: string; docs: { id: string }[] }) => {
          if (data.action === "picked" && data.docs?.[0]) {
            void runImport(accessToken, data.docs[0].id);
          } else {
            setStatus("idle");
          }
        })
        .build();
      picker.setVisible(true);
      setStatus("picking");
    });
  };

  /** Start the flow: request OAuth token, then show picker and run import. */
  const handleClick = () => {
    if (!clientId?.trim()) {
      toast.error("VITE_GOOGLE_CLIENT_ID is not set.");
      return;
    }
    const google = window.google;
    if (!google?.accounts?.oauth2) {
      toast.error("Google Sign-In not loaded. Refresh the page.");
      return;
    }
    setStatus("loading");
    const tokenClient = google.accounts.oauth2.initTokenClient({
      client_id: clientId,
      scope: DRIVE_SCOPE,
      callback: (response: { access_token: string }) => {
        if (response.access_token) {
          openPicker(response.access_token);
        } else {
          toast.error("Could not get access token.");
          setStatus("idle");
        }
      },
    });
    tokenClient.requestAccessToken();
  };

  const isBusy = status === "loading" || status === "picking" || status === "importing";

  const label =
    status === "importing"
      ? "Importing…"
      : status === "picking"
        ? "Pick file…"
        : status === "loading"
          ? "Connecting…"
          : "Import";

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isBusy}
      title="Import from Google Drive"
      aria-label="Import from Google Drive"
      className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-primary/40 bg-primary/10 px-2.5 text-xs font-medium text-primary shadow-sm transition hover:bg-primary/15 disabled:opacity-60"
    >
      {isBusy ? <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin" /> : <CloudDownload className="h-3.5 w-3.5 shrink-0" />}
      <span className="max-w-[7rem] truncate sm:max-w-none">{label}</span>
    </button>
  );
}
