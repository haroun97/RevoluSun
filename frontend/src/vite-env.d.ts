/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_GOOGLE_CLIENT_ID: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient: (config: {
            client_id: string;
            scope: string;
            callback: (response: { access_token: string }) => void;
          }) => { requestAccessToken: () => void };
        };
      };
      picker?: {
        PickerBuilder: new () => {
          setOAuthToken: (token: string) => this;
          addView: (view: unknown) => this;
          setCallback: (cb: (data: { action: string; docs: { id: string }[] }) => void) => this;
          build: () => { setVisible: (visible: boolean) => void };
        };
        DocsView: new (viewId: number) => unknown;
        ViewId: { SPREADSHEETS: number };
      };
    };
    gapi?: {
      load: (name: string, callback: () => void) => void;
    };
  }
}
export {};
