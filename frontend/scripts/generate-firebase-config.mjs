import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const envPath = path.join(frontendRoot, ".env");
const values = {};

if (fs.existsSync(envPath)) {
    for (const line of fs.readFileSync(envPath, "utf8").split(/\r?\n/)) {
        const match = line.match(/^\s*(VITE_FIREBASE_[A-Z0-9_]+)\s*=\s*(.*)\s*$/);
        if (match) values[match[1]] = match[2].replace(/^['"]|['"]$/g, "");
    }
}

const config = {
    apiKey: values.VITE_FIREBASE_API_KEY || "",
    authDomain: values.VITE_FIREBASE_AUTH_DOMAIN || "",
    projectId: values.VITE_FIREBASE_PROJECT_ID || "",
    storageBucket: values.VITE_FIREBASE_STORAGE_BUCKET || "",
    messagingSenderId: values.VITE_FIREBASE_MESSAGING_SENDER_ID || "",
    appId: values.VITE_FIREBASE_APP_ID || "",
};

fs.writeFileSync(
    path.join(frontendRoot, "public", "firebase-public-config.js"),
    `self.FIREBASE_CONFIG = ${JSON.stringify(config)};\n`,
);