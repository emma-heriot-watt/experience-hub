#!/bin/bash
set -euo pipefail

if [ -f /run/secrets/GITHUB_PAT ]; then
	GITHUB_PAT=$(cat /run/secrets/GITHUB_PAT)
	export GITHUB_PAT
fi

git config --global url."https://${GITHUB_PAT}@github.com/".insteadOf "https://github.com/"
