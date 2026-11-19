// Load test for the Orders API (Phase 7). Run it against a LOCAL stack, never
// against production: it creates real orders. See infra/loadtest/README.md.
//
//   BASE_URL=http://127.0.0.1:8000 SCALE=1 k6 run orders.js
//
// A customer day in miniature: most visitors only read the menu, a few order.
import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://127.0.0.1:8000";
const SCALE = Number(__ENV.SCALE || 1); // 1 = "normal Friday", 10 = "the R$20 promo"
const PAUSE = Number(__ENV.PAUSE ?? 1); // seconds between actions; 0 = stress mode, find the limit

export const options = {
  stages: [
    { duration: "30s", target: 10 * SCALE },
    { duration: "1m", target: 10 * SCALE },
    { duration: "10s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"], // under 1% errors
    http_req_duration: ["p(95)<500"], // 95% of requests under 500 ms
  },
};

export function setup() {
  const menu = http.get(`${BASE}/menu`);
  check(menu, { "menu loads": (r) => r.status === 200 });
  return { ids: menu.json().map((p) => p.id) };
}

export default function (data) {
  const menu = http.get(`${BASE}/menu`);
  check(menu, { "menu 200": (r) => r.status === 200 });

  if (Math.random() < 0.1) {
    const order = http.post(
      `${BASE}/orders`,
      JSON.stringify({
        customer: { name: "Load test", phone: "000000000", address: "k6 street 1" },
        items: [{ pizza_id: data.ids[Math.floor(Math.random() * data.ids.length)], quantity: 1 }],
      }),
      { headers: { "Content-Type": "application/json" } },
    );
    check(order, { "order 201": (r) => r.status === 201 });
  }
  if (PAUSE > 0) sleep(PAUSE);
}
