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
    vicinae-bin
    gnome-bluetooth-3.0
    dart-sass
    python-numpy
    python-materialyoucolor
    python-pip
    hyprsunset
    git
    upower
    gpu-screen-recorder
    networkmanager
    python-j2cli
    power-profiles-daemon
    ttf-jetbrains-mono-nerd
    awww
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

echo -e "${CYAN}"
echo "  /$$$$$$$$ /$$       /$$   /$$ /$$   /$$"
echo " | $$_____/| $$      | $$  | $$| $$  / $$"
echo " | $$      | $$      | $$  | $$|  $$/ $$/"
echo " | $$$$$   | $$      | $$  | $$ \  $$$$/ "
echo " | $$__/   | $$      | $$  | $$  >$$  $$ "
echo " | $$      | $$      | $$  | $$ /$$/\  $$"
echo " | $$      | $$$$$$$$|  $$$$$$/| $$  \ $$"
echo " |__/      |________/ \______/ |__/  |__/"
echo -e "${RESET}"

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
    step "Backing up existing installation..."
    mv "$INSTALL_DIR" "${INSTALL_DIR}_bak"
    success "Existing installation backed up to ${INSTALL_DIR}_bak"
fi

step "Cloning Flux repository..."
git clone "$REPO_URL" "$INSTALL_DIR"
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

# Install rembg package
step "Installing rembg package..."
pip install rembg --break-system-packages || warn "rembg installation failed."
success "rembg installed successfully."

# Install onnxruntime package
step "Installing onnxruntime package..."
pip install onnxruntime --break-system-packages || warn "onnxruntime installation failed."
success "onnxruntime installed successfully."

# Download models in parallel
step "Downloading AI models..."
mkdir -p ~/.local/share/.u2net

# Download both models in parallel with progress
curl -# -L "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx" -o ~/.local/share/.u2net/u2net.onnx &
u2net_pid=$!

curl -# -L "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx" -o ~/.local/share/.u2net/isnet-general-use.onnx &
isnet_pid=$!

# Wait for both downloads to complete
wait $u2net_pid && success "u2net model downloaded" || warn "u2net model download failed"
wait $isnet_pid && success "isnet-general-use model downloaded" || warn "isnet-general-use model download failed"

# Copy fonts to ~/.fonts
step "Installing fonts..."
mkdir -p ~/.fonts
if [ -d "$INSTALL_DIR/fonts" ]; then
    cp -r "$INSTALL_DIR/fonts/"* ~/.fonts/
    fc-cache -f ~/.fonts
    success "Fonts installed and cache updated"
else
    warn "Fonts directory not found in $INSTALL_DIR/fonts"
fi

# Add source line to hyprland config
step "Adding flux config to hyprland..."
mkdir -p ~/.config/hypr

# Verify flux.conf exists
if [ ! -f "$INSTALL_DIR/assets/hypr/flux.conf" ]; then
    warn "flux.conf not found in assets/hypr, skipping hyprland config"
else
    if ! grep -q "source=~/.config/ignis/assets/hypr/flux.conf" ~/.config/hypr/hyprland.conf 2>/dev/null; then
        echo "source=~/.config/ignis/assets/hypr/flux.conf" >> ~/.config/hypr/hyprland.conf
        success "Added flux config to hyprland.conf"
    else
        success "Flux config already in hyprland.conf"
    fi
fi
step "Setting up viciane..."
systemctl enable --user --now vicinae.service || warn "vicinae service failed to start"
# Start Flux
step "Starting Flux..."
ignis init > /dev/null 2>&1 &
disown
success "Flux started successfully."

echo -e "\n${GREEN}═══════════════════════════════════${RESET}"
echo -e "${GREEN}        Installation Complete!${RESET}"
echo -e "${GREEN}═══════════════════════════════════${RESET}"

echo -e "\n${CYAN}📦 What was installed:${RESET}"
echo -e "  • Flux Shell"
echo -e "  • Vicinae as run menu"
echo -e "  • AI background removal models"

echo -e "\n${CYAN}🚀 Next Steps:${RESET}"
echo -e "  • Restart Hyprland or reload config: ${YELLOW}hyprctl reload${RESET}"
echo -e "  • Access settings: ${YELLOW}Super + I${RESET}"
echo -e "  • Toggle Vicinae: ${YELLOW}Super + Space${RESET}"
echo -e "  • Reload Flux: ${YELLOW}Super + Alt + B${RESET}"

echo -e "\n${GREEN}✨ Enjoy your new Flux desktop! ✨${RESET}"
echo -e "${CYAN}Report issues: https://github.com/tr1xem/flux/issues${RESET}\n"
echo -e "${CYAN}For Support Join: https://discord.gg/tRFxkbQ3Zq${RESET}\n"
