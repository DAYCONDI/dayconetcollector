"""Background collector service for DaycoNet."""

import logging
import signal
import sys
import threading
import time
from collections import defaultdict
from typing import Optional

import db
import psutil
import pydivert
from config import (
    AGGREGATE_INTERVAL_SEC,
    DB_DSN,
    LOG_DIR,
    LOG_LEVEL,
    RAW_RETENTION_DAYS,
    SAMPLE_INTERVAL_SEC,
)

log = logging.getLogger(__name__)

shutdown_event = threading.Event()  # MUST be initially CLEARED, not set
buffer: dict[int, list[int]] = defaultdict(lambda: [0, 0])
buffer_lock = threading.Lock()
port_to_pid: dict[int, int] = {}
port_map_lock = threading.Lock()
dropped_packets = 0
dropped_lock = threading.Lock()
flushed_total = 0
flushed_lock = threading.Lock()

name_cache = {}
name_cache_lock = threading.Lock()
NAME_CACHE_MAX = 512
_agg_cycle_count = 0

PORT_MAP_REFRESH_SEC = 2.0
PACKET_FILTER = "tcp or udp"
PORT_MAP_LOG_EVERY_N_REFRESHES = 30


def setup_logging() -> None:
    """Configure file and stderr logging for the collector."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(threadName)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "collector.log", encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def handle_signal(signum: int, frame) -> None:
    """Handle shutdown signals by setting the shutdown event."""
    log.info("Received signal %d, shutting down.", signum)
    shutdown_event.set()


def resolve_name(pid):
    """Return cached (name, exe) for pid, resolving via psutil on first miss."""
    with name_cache_lock:
        hit = name_cache.get(pid)
        if hit is not None:
            return hit
    try:
        p = psutil.Process(pid)
        info = (p.name(), p.exe())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        info = ("unknown(pid=%d)" % pid, "")
    with name_cache_lock:
        if len(name_cache) >= NAME_CACHE_MAX:
            # evict the oldest insertion (dict preserves insertion order in 3.7+)
            try:
                first_key = next(iter(name_cache))
                del name_cache[first_key]
            except StopIteration:
                pass
        name_cache[pid] = info
    return info


def refresh_port_map() -> None:
    """Periodically rebuild the local port -> pid map from psutil."""
    global port_to_pid
    refresh_count = 0
    while not shutdown_event.is_set():
        try:
            new_map: dict[int, int] = {}
            for conn in psutil.net_connections(kind="inet"):
                if conn.laddr and conn.pid:
                    new_map[conn.laddr.port] = conn.pid
            with port_map_lock:
                port_to_pid = new_map
            refresh_count += 1
            if refresh_count % PORT_MAP_LOG_EVERY_N_REFRESHES == 0:
                with port_map_lock:
                    size = len(port_to_pid)
                log.info("Port map refreshed: %d entries (%d refreshes so far).", size, refresh_count)
        except (psutil.AccessDenied, OSError) as e:
            log.warning("Port map refresh failed: %s", e)
        if shutdown_event.wait(PORT_MAP_REFRESH_SEC):
            break


def flush_loop(pool) -> None:
    """Flush buffered per-pid byte counters to the DB every SAMPLE_INTERVAL_SEC."""
    global flushed_total
    while not shutdown_event.is_set():
        if shutdown_event.wait(SAMPLE_INTERVAL_SEC):
            break
        with buffer_lock:
            snapshot = dict(buffer)
            buffer.clear()
        if not snapshot:
            continue
        rows = []
        for pid, (sent, recv) in snapshot.items():
            if sent == 0 and recv == 0:
                continue
            name, exe = resolve_name(pid)
            rows.append((pid, name, exe, sent, recv))
        if not rows:
            continue
        try:
            n = db.insert_traffic_batch(pool, rows)
            with flushed_lock:
                global flushed_total  # must be declared at top of function; see below
                flushed_total += n
            total_bytes = sum(r[3] + r[4] for r in rows)
            log.info("Flushed %d records (%d bytes).", n, total_bytes)
        except Exception as e:
            log.error("Flush failed: %s", e)
            with buffer_lock:
                for pid, (sent, recv) in snapshot.items():
                    buffer[pid][0] += sent
                    buffer[pid][1] += recv


def aggregate_loop(pool) -> None:
    """Aggregate raw rows into hourly buckets and prune old rows periodically."""
    global dropped_packets
    while not shutdown_event.is_set():
        if shutdown_event.wait(AGGREGATE_INTERVAL_SEC):
            break
        try:
            agg, pruned = db.aggregate_and_prune(pool, RAW_RETENTION_DAYS)
            with dropped_lock:
                dropped_now = dropped_packets
                dropped_packets = 0
            with buffer_lock:
                buffered_pids = len(buffer)
            with port_map_lock:
                map_size = len(port_to_pid)
            with flushed_lock:
                flushed_now = flushed_total
                # do not reset flushed_total here; it is a cumulative counter for visibility only
            global _agg_cycle_count
            with name_cache_lock:
                cache_size = len(name_cache)
            _agg_cycle_count += 1
            if _agg_cycle_count % 10 == 0:
                with name_cache_lock:
                    name_cache.clear()
            log.info(
                "Status: aggregated=%d pruned=%d dropped=%d buffered_pids=%d port_map=%d flushed_cumulative=%d name_cache=%d.",
                agg, pruned, dropped_now, buffered_pids, map_size, flushed_now, cache_size,
            )
        except Exception as e:
            log.error("Aggregation failed: %s", e)


def packet_loop() -> None:
    """Read WinDivert packets, attribute to pids, buffer bytes, and re-inject."""
    global dropped_packets
    with pydivert.WinDivert(PACKET_FILTER) as wd:
        for packet in wd:
            try:
                if packet.is_outbound:
                    local_port = packet.src_port
                    direction = 0
                else:
                    local_port = packet.dst_port
                    direction = 1
                with port_map_lock:
                    pid = port_to_pid.get(local_port)
                if pid is not None:
                    resolve_name(pid)
                    size = len(packet.raw)
                    with buffer_lock:
                        buffer[pid][direction] += size
                else:
                    with dropped_lock:
                        dropped_packets += 1
            except Exception as e:
                log.debug("Packet handling error: %s", e)
            try:
                wd.send(packet)
            except OSError as e:
                log.warning("Failed to re-inject packet: %s", e)
            if shutdown_event.is_set():
                break


def main() -> int:
    """Entry point: start threads, run packet loop, shut down cleanly."""
    setup_logging()
    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, handle_signal)
    try:
        pool = db.make_pool(DB_DSN)
    except ValueError as e:
        log.error("Configuration error: %s", e)
        return 1
    try:
        db.wait_for_db(pool)
    except RuntimeError as e:
        log.error(str(e))
        pool.close()
        return 1
    log.info("DaycoNet Collector starting.")
    threads = [
        threading.Thread(target=refresh_port_map, name="portmap", daemon=True),
        threading.Thread(target=flush_loop, args=(pool,), name="flush", daemon=True),
        threading.Thread(target=aggregate_loop, args=(pool,), name="aggregate", daemon=True),
    ]
    for t in threads:
        t.start()
    try:
        packet_loop()
    except KeyboardInterrupt:
        log.info("Interrupted.")
    except Exception as e:
        log.exception("Packet loop crashed: %s", e)
        return 1
    finally:
        shutdown_event.set()
        for t in threads:
            t.join(timeout=10)
        pool.close()
    log.info("DaycoNet Collector stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
