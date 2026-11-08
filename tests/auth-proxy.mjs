import http from "node:http";

// 로컬 GoTrue 단독 테스트에서만 /auth/v1 게이트웨이 경로를 제공한다.
const server = http.createServer(async (request, response) => {
  if (!request.url.startsWith("/auth/v1/")) { response.writeHead(404).end(); return; }
  try {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    const headers = { ...request.headers };
    delete headers.host; delete headers.connection; delete headers["content-length"];
    const upstream = await fetch("http://127.0.0.1:55999" + request.url.slice("/auth/v1".length), {
      method: request.method, headers, redirect: "manual",
      body: ["GET", "HEAD"].includes(request.method) ? undefined : Buffer.concat(chunks),
    });
    response.statusCode = upstream.status;
    upstream.headers.forEach((value, name) => {
      if (!["transfer-encoding", "content-encoding", "content-length", "set-cookie"].includes(name)) response.setHeader(name, value);
    });
    const cookies = upstream.headers.getSetCookie();
    if (cookies.length) response.setHeader("Set-Cookie", cookies);
    response.end(Buffer.from(await upstream.arrayBuffer()));
  } catch { response.writeHead(502).end("로컬 Auth 서버에 연결하지 못했습니다."); }
});
server.listen(55821, "127.0.0.1", () => console.log("로컬 Auth 테스트 게이트웨이 준비"));
process.on("SIGTERM", () => server.close(() => process.exit(0)));
