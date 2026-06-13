' Phase 3.7 hidden launcher -- invoked by vault-reindex scheduled task.
' Spawns node.exe with WindowStyle=0 (hidden) so the reindex poll never
' flashes a console window onto the interactive desktop. Fire-and-forget;
' Task Scheduler still tracks the wscript exit, not node's.
'
' CONFIGURE: Set SUBSTRATE_PATH and NODE_PATH to match your environment.
' SUBSTRATE_PATH: path to your .vault-substrate directory (contains reindex-runner.mjs)
' NODE_PATH: path to your node.exe binary
Dim SUBSTRATE_PATH, NODE_PATH
SUBSTRATE_PATH = Environ("SUBSTRATE_ROOT")
If SUBSTRATE_PATH = "" Then SUBSTRATE_PATH = Environ("USERPROFILE") & "\.vault-substrate"
NODE_PATH = "node.exe"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run Chr(34) & NODE_PATH & Chr(34) & " " & Chr(34) & SUBSTRATE_PATH & "eindex-runner.mjs" & Chr(34), 0, False
