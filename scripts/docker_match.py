"""Run one local match using separate containers and referee-only network links."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import uuid


def docker(*args, timeout=120, check=True):
    return subprocess.run(["docker", *map(str, args)], capture_output=True, text=True,
                          timeout=timeout, check=check)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--player-image", default="pfi-player:dev")
    parser.add_argument("--referee-image", default="pfi-referee:dev")
    parser.add_argument("--submission", action="append", required=True)
    parser.add_argument("--episodes", type=int, choices=[256, 2048, 8192, 32768], default=256)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--seed", type=int, default=21)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "result.json").exists():
        parser.error("output already contains a result")
    token = "apex-market-" + uuid.uuid4().hex[:10]
    networks, containers = [], []
    volume = None
    started = time.monotonic()
    common = ["--platform", "linux/amd64", "--cpus", "1", "--memory", "512m", "--pids-limit", "64",
              "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--read-only",
              "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m"]
    try:
        for i, submission in enumerate(args.submission):
            network, name = f"{token}-net{i}", f"{token}-p{i}"
            docker("network", "create", "--internal", network)
            networks.append(network)
            docker("create", *common, "--network", network, "--network-alias", f"p{i}", "--name", name,
                   "--mount", f"type=bind,src={Path(submission).resolve()},dst=/app/submission.py,readonly",
                   args.player_image)
            containers.append(name)
            docker("start", name)
        volume = token + "-data"
        docker("volume", "create", volume)
        name = token + "-referee"
        config = {"episodes": args.episodes, "batch_size": args.batch_size, "deadline_ms": 100}
        docker("create", *common, "--network", networks[0], "--name", name,
               "--env", "MATCH_ID=local-market", "--env", f"SEED={args.seed}",
               "--env", f"NUM_PLAYERS={len(args.submission)}", "--env", "CONFIG_JSON=" + json.dumps(config),
               "--env", "PLAYER_URLS=" + ",".join(f"http://p{i}:8000" for i in range(len(args.submission))),
               "--mount", f"type=volume,source={volume},target=/data", args.referee_image)
        containers.append(name)
        for network in networks[1:]:
            docker("network", "connect", network, name)
        docker("start", name)
        exit_code = docker("wait", name, timeout=1200).stdout.strip()
        docker("cp", f"{name}:/data/.", output, check=exit_code == "0")
        logs = docker("logs", name, check=False)
        (output / "referee.log").write_text(logs.stdout + logs.stderr)
        if exit_code != "0":
            raise RuntimeError(f"referee exit {exit_code}: {(logs.stdout + logs.stderr)[-2000:]}")
        result = json.loads((output / "result.json").read_text())
        manifest = {"local_only": True, "architecture": "linux/amd64", "cpu_limit": 1,
                    "memory_bytes": 536870912, "player_count": len(args.submission),
                    "referee_only_internal_networks": True, "wall_seconds": round(time.monotonic() - started, 3),
                    "player_image": json.loads(docker("image", "inspect", args.player_image).stdout)[0]["Id"],
                    "referee_image": json.loads(docker("image", "inspect", args.referee_image).stdout)[0]["Id"],
                    "config": config, "result": result}
        (output / "run.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps(manifest, indent=2))
    finally:
        for name in reversed(containers):
            docker("rm", "-f", name, check=False)
        if volume:
            docker("volume", "rm", volume, check=False)
        for network in reversed(networks):
            docker("network", "rm", network, check=False)


if __name__ == "__main__":
    main()
