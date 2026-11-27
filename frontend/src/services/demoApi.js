import { AxiosError } from "axios";
import { handleDemoRequest } from "./demoData.js";

export async function staticDemoAdapter(config) {
  try {
    const data = await handleDemoRequest(config);
    return {
      data,
      status: 200,
      statusText: "OK",
      headers: {},
      config,
      request: null,
    };
  } catch (error) {
    const status = error.status || 500;
    const response = {
      data: { detail: error.message || "Static demo data is unavailable." },
      status,
      statusText: status === 405 ? "Method Not Allowed" : "Static Demo Error",
      headers: {},
      config,
      request: null,
    };
    throw new AxiosError(
      response.data.detail,
      AxiosError.ERR_BAD_REQUEST,
      config,
      null,
      response,
    );
  }
}
