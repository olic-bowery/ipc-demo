#!/bin/bash

# BASH strict mode (see http://redsymbol.net/articles/unofficial-bash-strict-mode/)
set -euo pipefail

do_setup_venv() {
  echo "Setting up virtualenv"
  python3 -m venv venv
  do_install_requirements
}

do_install_requirements() {
  do_activate_venv
  echo "Installing requirements.txt"
  pip3 install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org -r requirements.txt
}

do_cleanup() {
  echo -e "cleaning logs.."
  rm -rf .log
  echo -e "cleaning virtual env.."
  rm -rf venv
}

do_activate_venv() {
  echo "Activating virtualenv"
  source venv/bin/activate
}

do_help() {
  echo "***** Bowery Crate *****"
  echo -e "Options:"
  echo -e "\t--install                       Install python environment"
  echo -e "\t--run                           Start scale service"
}
if [ $# -eq 0 ]; then
  do_help
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case $1 in
      --help)
        do_help
        exit 1
        ;;
      --install)
        do_setup_venv
        do_install_requirements
        exit 1
        ;;
      --run)
        do_activate_venv
        "$PWD/venv/bin/python3" -m main
        exit 1
        ;;
      *)
        echo "Use --help"
        exit 0
        ;;
  esac
  done
