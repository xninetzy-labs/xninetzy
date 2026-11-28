# Reverse engineering — load before shipped-artifact analysis
<!-- id: xninetzy.rea; version: 2.3.0; scope: conditional-client-guidance -->

Load skill `reverse-engineer-anything` and use the `rea` MCP when the question depends on a shipped artifact without source: binary, APK/IPA, ASAR/Electron, .NET, firmware, WASM, pcap/HAR, build diffs, installed apps or websites. For a repository with source, use `codebase-memory-mcp` instead.
Authorized targets only. Static analysis may proceed; ask before runtime capture, launching or instrumenting a target, adb/device actions or installing an engine.
Shell use: `set -a; . ~/.local/share/rea-tools/env.sh; set +a`, then `rea doctor --json` lists the engines (IDA and JEB are not installed). Report REA's evidence and limits as returned; never fill gaps by guessing.

This guidance does not grant permission or replace CORE_RULES.md.
