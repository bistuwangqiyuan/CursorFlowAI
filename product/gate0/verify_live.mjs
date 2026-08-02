import { get } from "node:https";

const url = process.argv[2] || "https://triadguard.vercel.app/";

get(url, (res) => {
  let data = "";
  res.on("data", (c) => (data += c));
  res.on("end", () => {
    console.log("status", res.statusCode);
    console.log("hasBrand", data.includes("TriadGuard"));
    console.log("hasScanner", data.includes("Scan in browser") || data.includes("workflow"));
    process.exit(res.statusCode === 200 && data.includes("TriadGuard") ? 0 : 1);
  });
}).on("error", (e) => {
  console.error("ERR", e.message);
  process.exit(2);
});
