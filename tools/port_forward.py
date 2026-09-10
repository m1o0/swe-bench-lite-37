"""Minimal TCP forwarder: expose a 127.0.0.1-only proxy port to the WSL NAT interface.

Context: Clash Verge (mihomo) listens on 127.0.0.1:7897 only, and this WSL2 distro
runs in NAT mode, so WSL cannot reach the Windows loopback proxy.  Binding to an
address reachable from WSL and forwarding to 127.0.0.1 lets WSL use the proxy that
already works for the rest of the machine, without enabling Clash's LAN mode.

Usage: python port_forward.py [listen_host] [listen_port] [target_host] [target_port]
Default: 0.0.0.0 7898 127.0.0.1 7897
"""

import asyncio
import sys


async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def handle(client_reader, client_writer, target_host, target_port):
    try:
        remote_reader, remote_writer = await asyncio.open_connection(target_host, target_port)
    except Exception:
        client_writer.close()
        return
    await asyncio.gather(
        pipe(client_reader, remote_writer),
        pipe(remote_reader, client_writer),
    )
    for w in (client_writer, remote_writer):
        try:
            w.close()
        except Exception:
            pass


async def main(listen_host, listen_port, target_host, target_port):
    server = await asyncio.start_server(
        lambda r, w: handle(r, w, target_host, target_port), listen_host, listen_port
    )
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"forwarding {addrs} -> {target_host}:{target_port}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    argv = sys.argv[1:]
    listen_host = argv[0] if len(argv) > 0 else "0.0.0.0"
    listen_port = int(argv[1]) if len(argv) > 1 else 7898
    target_host = argv[2] if len(argv) > 2 else "127.0.0.1"
    target_port = int(argv[3]) if len(argv) > 3 else 7897
    try:
        asyncio.run(main(listen_host, listen_port, target_host, target_port))
    except KeyboardInterrupt:
        pass
