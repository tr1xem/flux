#!/bin/bash

#  /$$$$$$$$ /$$       /$$   /$$ /$$   /$$
# | $$_____/| $$      | $$  | $$| $$  / $$
# | $$      | $$      | $$  | $$|  $$/ $$/
# | $$$$$   | $$      | $$  | $$ \  $$$$/
# | $$__/   | $$      | $$  | $$  >$$  $$
# | $$      | $$      | $$  | $$ /$$/\  $$
# | $$      | $$$$$$$$|  $$$$$$/| $$  \ $$
# |__/      |________/ \______/ |__/  |__/
#

#  A hackable shell for Hyprland
#  Installation Script for Arch Linux
#
#  Repository:  https://github.com/tr1xem/flux
#  License: GPLv3

set -e          # Exit immediately if a command exits with a non-zero status
set -u          # Treat unset variables as an error
set -o pipefail # Prevent errors in a pipeline from being masked

REPO_URL="https://github.com/tr1xem/flux.git"
INSTALL_DIR="$HOME/.config/ignis"

PACKAGES=(
    python-ignis-git
    ignis-gvc
    gnome-bluetooth-3.0
    dart-sass
    python-numpy
    python-materialyoucolor
    upower
    gpu-screen-recorder
    networkmanager
    python-j2cli
    power-profiles-daemon
    ttf-jetbrains-mono-nerd
)

# Colors
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
RED=$(tput setaf 1)
CYAN=$(tput setaf 6)
RESET=$(tput sgr0)

# Function for status messages
step() {
    echo -e "${CYAN}→${RESET} $1"
}
success() {
    echo -e "${GREEN}✔${RESET} $1"
}
warn() {
    echo -e "${YELLOW}!${RESET} $1"
}
error() {
    echo -e "${RED}✖${RESET} $1"
}

echo -e "${GREEN}=================================="
echo "   Flux Installer for Arch Linux"
echo -e "==================================${RESET}"

# OS check
if ! grep -qi "arch" /etc/os-release; then
    error "This script is designed for Arch Linux or Arch-based distro."
    exit 1
fi

# Root check
if [ "$(id -u)" -eq 0 ]; then
    error "Please do not run as root."
    exit 1
fi

# Warn about sudo
# echo -e "\n${YELLOW}Some packages require root privileges (e.g., glace-git).${RESET}"
# echo "You will be prompted for your sudo password now so the installation runs smoothly."
# sudo -v || {
#     error "Sudo authentication failed."
#     exit 1
# }

# Keep sudo alive until script finishes
# while true; do
#     sudo -n true
#     sleep 60
#     kill -0 "$$" || exit
# done 2>/dev/null &
#
# Confirm installation (skip if running from pipe)
if [[ -t 0 ]]; then
    echo -e "\nThis will install Flux and the following packages:"
    printf "%s\n" "${PACKAGES[@]}"
    read -rp "$(echo -e "${YELLOW}""Proceed? (y/N): ""${RESET}")" confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        warn "Installation cancelled."
        exit 0
    fi
else
    echo -e "\nInstalling Flux and the following packages:"
    printf "%s\n" "${PACKAGES[@]}"
fi

aur_helper="yay"

# Check if paru exists, otherwise use yay
if command -v paru &>/dev/null; then
    aur_helper="paru"
elif ! command -v yay &>/dev/null; then
    echo "Installing yay-bin..."
    tmpdir=$(mktemp -d)
    git clone --depth=1 https://aur.archlinux.org/yay-bin.git "$tmpdir/yay-bin"
    (cd "$tmpdir/yay-bin" && makepkg -si --noconfirm)
    rm -rf "$tmpdir"
fi

# Clone or update repo
if [ -d "$INSTALL_DIR" ]; then
    step "Updating Flux repository..."
    git -C "$INSTALL_DIR" pull --rebase
else
    step "Cloning Flux repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
success "Repository ready."

# Install packages
step "Installing required packages..."
$aur_helper -Syy --needed --noconfirm "${PACKAGES[@]}" || warn "Some packages failed to install."

# Update outdated packages
step "Checking for outdated packages..."
outdated=$($aur_helper -Qu | awk '{print $1}' || true)
to_update=()
for pkg in "${PACKAGES[@]}"; do
    if echo "$outdated" | grep -q "^$pkg\$"; then
        to_update+=("$pkg")
    fi
done

if [ ${#to_update[@]} -gt 0 ]; then
    step "Updating outdated packages..."
    $aur_helper -S --noconfirm "${to_update[@]}"
else
    success "All packages are up-to-date."
fi

#  Run config
# step "Running configuration..."
# python "$INSTALL_DIR/config/config.py"

# Start Modus
step "Starting Flux..."
ignis init &
disown
success "Flux started successfully."

echo -e "\n${GREEN}Installation complete!${RESET}"
