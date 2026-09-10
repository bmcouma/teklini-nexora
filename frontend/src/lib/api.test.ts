import { afterEach, describe, expect, it, vi } from "vitest";
import { api, setApiKey } from "./api";

afterEach(() => {
  setApiKey("");
  vi.unstubAllGlobals();
});

describe("API authentication", () => {
  it("reports unauthorized responses as a typed error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "API key required" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(api.createIncident({ use_demo_data: true })).rejects.toMatchObject({
      status: 401,
      code: "unauthorized",
    });
  });

  it("sends a user-provided session key on authenticated requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ incident: { incident_id: "INC-1" } }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    setApiKey("session-test-key");

    await api.createIncident({ use_demo_data: true });

    const requestInit = fetchMock.mock.calls[0][1] as RequestInit;
    expect(fetchMock.mock.calls[0][0]).toBe("/api/incidents");
    expect((requestInit.headers as Headers).get("X-API-Key")).toBe("session-test-key");
  });
});
