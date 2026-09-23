#!/bin/sh
# ==============================================================================
# oh-my-antigravity Installer (macOS & Linux)
# https://github.com/HengWeiBin/oh-my-antigravity
# ==============================================================================
set -eu

REPO_URL="https://github.com/HengWeiBin/oh-my-antigravity.git"

# Setup terminal color codes if output is a TTY
if [ -t 1 ]; then
  BOLD="\033[1m"
  DIM="\033[2m"
  GREEN="\033[32m"
  CYAN="\033[36m"
  YELLOW="\033[33m"
  RED="\033[31m"
  RESET="\033[0m"
else
  BOLD=""
  DIM=""
  GREEN=""
  CYAN=""
  YELLOW=""
  RED=""
  RESET=""
fi

log_info() {
  printf "${CYAN}→ %s${RESET}\n" "$*"
}

log_success() {
  printf "${GREEN}✓ %s${RESET}\n" "$*"
}

log_warn() {
  printf "${YELLOW}! %s${RESET}\n" "$*"
}

log_error() {
  printf "${RED}✗ %s${RESET}\n" "$*" >&2
}

print_banner() {
  printf "${CYAN}"
  cat << "EOF"
   ___  __               __  __           ___         __  _                       __  __     
  / _ \/ /_  ____ __ _  / / / /_ _____   / _ | ___  / /_(_)__ ________ __  _____ / /_/ /_  __
 / // / _ \ /___// '  \/ /_/ / // /___/ / __ |/ _ \/ __/ / _ `/ __/ _ `/ |/ / // / __/ // / 
 \___/_//_/     /_/_/_/\____/\_, /     /_/ |_/_//_/\__/_/\_, /_/  \_,_/|___/\_, /\__/\_, /  
                            /___/                       /___/              /___/    /___/   
EOF
  printf "${RESET}\n"
  printf "${BOLD}oh-my-antigravity — Release Readiness Installer${RESET}\n"
  printf "${DIM}Orchestration, Skills & Lifecycle Hooks for Google Antigravity 2.0${RESET}\n\n"
}

# ------------------------------------------------------------------------------
# 1. Target Directory Resolution
# ------------------------------------------------------------------------------
resolve_target_dir() {
  if [ -n "${ANTIGRAVITY_PLUGINS_DIR:-}" ]; then
    case "$ANTIGRAVITY_PLUGINS_DIR" in
      */oh-my-antigravity)
        TARGET_DIR="$ANTIGRAVITY_PLUGINS_DIR"
        ;;
      *)
        TARGET_DIR="$ANTIGRAVITY_PLUGINS_DIR/oh-my-antigravity"
        ;;
    esac
  else
    TARGET_DIR="${HOME}/.gemini/config/plugins/oh-my-antigravity"
  fi
}

# ------------------------------------------------------------------------------
# 2. Pre-flight Checks (Git & Python 3.13+ / uv)
# ------------------------------------------------------------------------------
check_prerequisites() {
  log_info "Running pre-flight environment checks..."

  # Check Git
  if ! command -v git >/dev/null 2>&1; then
    log_error "git is required but was not found in PATH."
    printf "  Please install Git before proceeding:\n"
    printf "    macOS: brew install git\n"
    printf "    Debian/Ubuntu: sudo apt-get install git\n"
    printf "    Fedora/RHEL: sudo dnf install git\n\n"
    exit 1
  fi
  log_success "Found git: $(git --version)"

  # Check Python >= 3.13 or uv
  runtime_found=0
  runtime_desc=""

  # Try python3
  if command -v python3 >/dev/null 2>&1; then
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)" >/dev/null 2>&1; then
      py_ver="$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}")' 2>/dev/null || echo ">=3.13")"
      runtime_found=1
      runtime_desc="python3 (v${py_ver})"
    fi
  fi

  # Try python if python3 didn't qualify
  if [ "$runtime_found" -eq 0 ] && command -v python >/dev/null 2>&1; then
    if python -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)" >/dev/null 2>&1; then
      py_ver="$(python -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}")' 2>/dev/null || echo ">=3.13")"
      runtime_found=1
      runtime_desc="python (v${py_ver})"
    fi
  fi

  # Try uv
  if command -v uv >/dev/null 2>&1; then
    uv_ver="$(uv --version 2>/dev/null || echo "uv")"
    if [ "$runtime_found" -eq 1 ]; then
      runtime_desc="${runtime_desc} + ${uv_ver}"
    else
      runtime_found=1
      runtime_desc="${uv_ver}"
    fi
  fi

  if [ "$runtime_found" -eq 0 ]; then
    log_error "Python >= 3.13 or uv is required to run oh-my-antigravity hooks."

    # Try to detect what python is currently installed
    curr_py=""
    if command -v python3 >/dev/null 2>&1; then
      curr_py="$(python3 --version 2>&1 || true)"
    elif command -v python >/dev/null 2>&1; then
      curr_py="$(python --version 2>&1 || true)"
    fi

    if [ -n "$curr_py" ]; then
      printf "  Currently detected: %s (requires >= 3.13)\n\n" "$curr_py"
    else
      printf "  No Python installation found in PATH.\n\n"
    fi

    printf "  ${BOLD}Recommended resolution:${RESET}\n"
    printf "    1. Install uv (ultra-fast Python package & tool manager):\n"
    printf "       ${CYAN}curl -LsSf https://astral.sh/uv/install.sh | sh${RESET}\n"
    printf "    2. Or install Python 3.13+ directly:\n"
    printf "       macOS:          ${CYAN}brew install python@3.13${RESET}\n"
    printf "       Ubuntu/Debian:  ${CYAN}sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt update && sudo apt install python3.13${RESET}\n"
    printf "       Fedora:         ${CYAN}sudo dnf install python3.13${RESET}\n\n"
    exit 1
  fi

  log_success "Found runtime prerequisite: ${runtime_desc}"
}

# ------------------------------------------------------------------------------
# 3. Idempotent Clone / Pull
# ------------------------------------------------------------------------------
install_or_update() {
  if [ -d "$TARGET_DIR" ]; then
    if [ -d "$TARGET_DIR/.git" ]; then
      log_info "Existing installation detected at: $TARGET_DIR"
      if git -C "$TARGET_DIR" remote >/dev/null 2>&1 && [ -n "$(git -C "$TARGET_DIR" remote 2>/dev/null)" ]; then
        log_info "Updating repository via git pull --ff-only..."
        if git -C "$TARGET_DIR" pull --ff-only; then
          log_success "Repository updated successfully."
        else
          log_warn "git pull --ff-only failed. If you have local modifications, please resolve them in: $TARGET_DIR"
        fi
      else
        log_info "Local repository detected. Skipping remote pull."
      fi
    else
      log_error "Target directory already exists but is not a Git repository:"
      printf "  %s\n" "$TARGET_DIR"
      printf "  Please remove or back up this directory, then run the installer again.\n"
      exit 1
    fi
  else
    PARENT_DIR="$(dirname "$TARGET_DIR")"
    if [ ! -d "$PARENT_DIR" ]; then
      log_info "Creating plugin directory tree: $PARENT_DIR"
      mkdir -p "$PARENT_DIR"
    fi

    log_info "Cloning oh-my-antigravity repository into:"
    printf "  %s\n" "$TARGET_DIR"
    git clone "$REPO_URL" "$TARGET_DIR"
    log_success "Repository cloned successfully."
  fi
}

# ------------------------------------------------------------------------------
# 4. Integrity Verification
# ------------------------------------------------------------------------------
verify_installation() {
  log_info "Verifying plugin integrity..."

  missing=""
  if [ ! -f "$TARGET_DIR/plugin.json" ]; then
    missing="${missing} plugin.json"
  fi
  if [ ! -f "$TARGET_DIR/hooks.json" ]; then
    missing="${missing} hooks.json"
  fi

  if [ -n "$missing" ]; then
    log_error "Integrity check failed! Missing essential files:${missing}"
    exit 1
  fi

  log_success "Integrity check passed (plugin.json and hooks.json present)."
}

# ------------------------------------------------------------------------------
# 5. Success Message & Next Steps
# ------------------------------------------------------------------------------
print_success() {
  printf "\n"
  printf "${GREEN}══════════════════════════════════════════════════════════════════════${RESET}\n"
  printf "${BOLD}${GREEN}  ★ oh-my-antigravity is successfully installed! ★${RESET}\n"
  printf "${GREEN}══════════════════════════════════════════════════════════════════════${RESET}\n\n"

  printf "  ${BOLD}Install Location:${RESET} %s\n" "$TARGET_DIR"
  printf "  ${BOLD}Version:${RESET}          0.1.0\n"
  printf "  ${BOLD}Status:${RESET}           Ready for Google Antigravity 2.0\n\n"

  printf "${BOLD}Next Steps:${RESET}\n"
  printf "  1. Start or restart Google Antigravity to load the plugin.\n"
  printf "  2. Verify installed plugins via Antigravity CLI:\n"
  printf "     ${CYAN}agy plugin list${RESET}\n"
  printf "  3. Or inspect in GUI: ${BOLD}Settings > Customizations > Plugins${RESET}\n"
  printf "  4. Try invoking subagents (e.g. ${CYAN}@Atlas${RESET}, ${CYAN}@Prometheus${RESET}, ${CYAN}@Hephaestus${RESET})\n"
  printf "     or explore bundled skills in ${CYAN}skills/${RESET}.\n\n"

  printf "${DIM}Repository & Docs:${RESET} https://github.com/HengWeiBin/oh-my-antigravity\n\n"
}

main() {
  print_banner
  resolve_target_dir
  check_prerequisites
  install_or_update
  verify_installation
  print_success
}

main "$@"
