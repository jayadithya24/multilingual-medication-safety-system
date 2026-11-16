import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { loadEnv } from "vite";

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export function generateFirebaseConfig(mode = "development") {
    const values = loadEnv(mode, frontendRoot, "VITE_FIREBASE_");
    // Only explicitly public Firebase web-app fields are written to the browser.
    const config = Object.fromEntries(Object.entries({
        apiKey: "API_KEY", authDomain: "AUTH_DOMAIN", projectId: "PROJECT_ID",
        storageBucket: "STORAGE_BUCKET", messagingSenderId: "MESSAGING_SENDER_ID", appId: "APP_ID",
    }).map(([key, suffix]) => [key, values[`VITE_FIREBASE_${suffix}`] || ""]));
    fs.writeFileSync(path.join(frontendRoot, "public", "firebase-public-config.js"),
        `self.FIREBASE_CONFIG = ${JSON.stringify(config)};\n`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
    generateFirebaseConfig(process.argv[2] || "development");
}
