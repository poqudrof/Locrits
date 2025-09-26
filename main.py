#!/usr/bin/env python3
"""
Point d'entrée principal de l'application Locrit.
"""

from src.app import LocritApp


def main():
    """Lance l'application principale."""
    app = LocritApp()
    app.run()


if __name__ == "__main__":
    main()
