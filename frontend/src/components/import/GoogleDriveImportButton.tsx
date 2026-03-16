import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CloudDownload, Loader2 } from "lucide-react";
import { importGoogleDriveFile } from "@/api/energyApi";

const DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly";

export function GoogleDriveImportButton() {
  const [status, setStatus] = useState<"idle" | "loading" | "picking" | "importing" | "success" | "error">("idle");
  const [message, setMessage] = useState<string>("");
  const queryClient = useQueryClient();
  const clientId = typeof import.meta !== "undefined" && import.meta.env?.VITE_GOOGLE_CLIENT_ID;

  const runImport = async (accessToken: string, fileId: string) => {
    setStatus("importing");
    setMessage("Importing…");
    try {
      const result = await importGoogleDriveFile(accessToken, fileId);
      setMessage(result.message);
      setStatus("success");
      await queryClient.invalidateQueries({ queryKey: ["dateRange"] });
      await queryClient.invalidateQueries({ queryKey: ["summary"] });
      await queryClient.invalidateQueries({ queryKey: ["timeseries"] });
      await queryClient.invalidateQueries({ queryKey: ["tenants"] });
      await queryClient.invalidateQueries({ queryKey: ["sharing"] });
      await queryClient.invalidateQueries({ queryKey: ["quality"] });
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Import failed");
      setStatus("error");
    }
  };

  const openPicker = (accessToken: string) => {
    if (!window.gapi) {
      setMessage("Google Picker not loaded. Refresh the page.");
      setStatus("error");
      return;
    }
    window.gapi.load("picker", () => {
      const google = window.google;
      if (!google?.picker) {
        setMessage("Google Picker not available.");
        setStatus("error");
        return;
      }
      const picker = new google.picker.PickerBuilder()
        .setOAuthToken(accessToken)
        .addView(new google.picker.DocsView(google.picker.ViewId.SPREADSHEETS))
        .setCallback((data: { action: string; docs: { id: string }[] }) => {
          if (data.action === "picked" && data.docs?.[0]) {
            runImport(accessToken, data.docs[0].id);
          } else {
            setStatus("idle");
          }
        })
        .build();
      picker.setVisible(true);
      setStatus("picking");
    });
  };

  const handleClick = () => {
    if (!clientId?.trim()) {
      setMessage("VITE_GOOGLE_CLIENT_ID is not set.");
      setStatus("error");
      return;
    }
    const google = window.google;
    if (!google?.accounts?.oauth2) {
      setMessage("Google Sign-In not loaded. Refresh the page.");
      setStatus("error");
      return;
    }
    setStatus("loading");
    setMessage("Requesting access…");
    const tokenClient = google.accounts.oauth2.initTokenClient({
      client_id: clientId,
      scope: DRIVE_SCOPE,
      callback: (response: { access_token: string }) => {
        if (response.access_token) {
          openPicker(response.access_token);
        } else {
          setMessage("Could not get access token.");
          setStatus("error");
        }
      },
    });
    tokenClient.requestAccessToken();
  };

  const isBusy = status === "loading" || status === "picking" || status === "importing";

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={handleClick}
        disabled={isBusy}
        className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition hover:bg-primary/90 disabled:opacity-60"
      >
        {isBusy ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <CloudDownload className="h-4 w-4" />
        )}
        {status === "importing" ? "Importing…" : status === "picking" ? "Pick a file…" : "Import from Google Drive"}
      </button>
      {message && (
        <p
          className={`text-sm ${status === "error" ? "text-destructive" : status === "success" ? "text-green-600" : "text-muted-foreground"}`}
        >
          {message}
        </p>
      )}
    </div>
  );
}
