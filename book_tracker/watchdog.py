import argparse
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .proxies import refresh_proxy_pool


HEADER_RE = re.compile(r'^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] -+$')
RESULT_RE = re.compile(r'^.+\s:\s(?P<value>FAILED \(skipping\)|[\d,]+)$')
DEFAULT_OUTPUT_LOG = Path('tracker-output.log')
DEFAULT_WATCHDOG_LOG = Path('watchdog.log')


@dataclass
class Block:
    timestamp: str
    results: list[str]

    @property
    def all_failed(self):
        return bool(self.results) and all(
            result == 'FAILED (skipping)' for result in self.results
        )


def log(message, log_file):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with log_file.open('a') as f:
        f.write(f'[{timestamp}] {message}\n')


def parse_blocks(output_log, expected_results):
    try:
        lines = output_log.read_text().splitlines()
    except FileNotFoundError:
        return []

    blocks = []
    current = None
    for line in lines:
        header = HEADER_RE.match(line)
        if header:
            if current is not None:
                blocks.append(current)
            current = Block(timestamp=header.group('timestamp'), results=[])
            continue

        result = RESULT_RE.match(line)
        if result and current is not None:
            current.results.append(result.group('value'))

    if current is not None:
        blocks.append(current)
    return [block for block in blocks if len(block.results) >= expected_results]


def count_failure_streak(blocks):
    streak = 0
    for block in reversed(blocks):
        if not block.all_failed:
            break
        streak += 1
    return streak


def restart_cmux(surface, command, log_file):
    if not surface:
        log('event=restart_skipped reason=no_surface', log_file)
        return

    subprocess.run(
        ['cmux', 'send-key', '--surface', surface, 'Ctrl-C'],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)
    subprocess.run(
        ['cmux', 'send', '--surface', surface, command],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        ['cmux', 'send-key', '--surface', surface, 'Enter'],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    log(f'event=restarted surface={surface} command="{command}"', log_file)


def remediate(args, latest_block):
    log(
        f'event=trigger latest_block="{latest_block.timestamp}" '
        f'action=refresh_proxies threshold={args.failure_threshold}',
        args.watchdog_log,
    )
    proxies = refresh_proxy_pool(force=True)
    log(f'event=proxy_refresh pool_size={len(proxies)}', args.watchdog_log)
    restart_cmux(args.surface, args.restart_command, args.watchdog_log)


def run_once(args, last_triggered_timestamp=None):
    blocks = parse_blocks(args.output_log, args.expected_results)
    if not blocks:
        log('event=no_blocks', args.watchdog_log)
        return last_triggered_timestamp

    latest = blocks[-1]
    streak = count_failure_streak(blocks)
    log(
        f'event=checked latest_block="{latest.timestamp}" '
        f'results={len(latest.results)} full_failure_streak={streak}',
        args.watchdog_log,
    )
    if streak >= args.failure_threshold and latest.timestamp != last_triggered_timestamp:
        remediate(args, latest)
        return latest.timestamp
    return last_triggered_timestamp


def parse_args():
    parser = argparse.ArgumentParser(
        description='Deterministic watchdog for book-tracker failures.'
    )
    parser.add_argument('--output-log', type=Path, default=DEFAULT_OUTPUT_LOG)
    parser.add_argument('--watchdog-log', type=Path, default=DEFAULT_WATCHDOG_LOG)
    parser.add_argument(
        '--surface',
        default=os.environ.get('BOOK_TRACKER_CMUX_SURFACE'),
        help='cmux surface to restart, for example surface:41',
    )
    parser.add_argument(
        '--restart-command',
        default=os.environ.get('BOOK_TRACKER_RESTART_COMMAND', './run.sh'),
    )
    parser.add_argument('--failure-threshold', type=int, default=2)
    parser.add_argument('--expected-results', type=int, default=2)
    parser.add_argument('--interval', type=int, default=60)
    parser.add_argument('--once', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    last_triggered_timestamp = None
    while True:
        last_triggered_timestamp = run_once(args, last_triggered_timestamp)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
