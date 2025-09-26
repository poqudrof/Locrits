#!/usr/bin/env python3
"""
Script de test pour la communication entre Locrits via l'API.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional


class LocritClient:
    """Client pour communiquer avec l'API Locrit"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialise le client Locrit.

        Args:
            base_url: URL de base de l'API Locrit
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def ping(self) -> Dict[str, Any]:
        """Teste la connexion à l'API"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/ping")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}

    def list_locrits(self) -> Dict[str, Any]:
        """Liste les Locrits disponibles"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/locrits")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}

    def get_locrit_info(self, locrit_name: str) -> Dict[str, Any]:
        """Obtient les informations d'un Locrit"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/locrits/{locrit_name}/info")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}

    def chat_with_locrit(self, locrit_name: str, message: str,
                        sender_name: str = "TestClient",
                        context: str = "") -> Dict[str, Any]:
        """Envoie un message à un Locrit"""
        try:
            data = {
                'message': message,
                'sender_name': sender_name,
                'sender_type': 'locrit',
                'context': context
            }

            response = self.session.post(
                f"{self.base_url}/api/v1/locrits/{locrit_name}/chat",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}

    def chat_stream_with_locrit(self, locrit_name: str, message: str,
                               sender_name: str = "TestClient",
                               context: str = "") -> None:
        """Chat en streaming avec un Locrit"""
        try:
            data = {
                'message': message,
                'sender_name': sender_name,
                'sender_type': 'locrit',
                'context': context
            }

            response = self.session.post(
                f"{self.base_url}/api/v1/locrits/{locrit_name}/chat/stream",
                json=data,
                headers={'Content-Type': 'application/json'},
                stream=True
            )
            response.raise_for_status()

            print(f"\n{locrit_name}: ", end="", flush=True)

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if 'chunk' in data:
                                print(data['chunk'], end="", flush=True)
                            elif data.get('done'):
                                print()
                                break
                            elif 'error' in data:
                                print(f"\nErreur: {data['error']}")
                                break
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.RequestException as e:
            print(f"\nErreur de connexion: {e}")


def main():
    """Fonction principale de test"""
    print("🤖 Test de communication entre Locrits")
    print("=" * 50)

    # Initialiser le client
    client = LocritClient()

    # Tester la connexion
    print("1. Test de connexion à l'API...")
    ping_result = client.ping()
    if not ping_result.get('success'):
        print(f"❌ Erreur de connexion: {ping_result.get('error')}")
        sys.exit(1)

    print(f"✅ API disponible: {ping_result.get('message')}")
    print(f"   Version: {ping_result.get('version')}")
    print(f"   Timestamp: {ping_result.get('timestamp')}")

    # Lister les Locrits disponibles
    print("\n2. Liste des Locrits disponibles...")
    locrits_result = client.list_locrits()
    if not locrits_result.get('success'):
        print(f"❌ Erreur: {locrits_result.get('error')}")
        sys.exit(1)

    locrits = locrits_result.get('locrits', [])
    if not locrits:
        print("❌ Aucun Locrit disponible pour la communication.")
        print("   Assurez-vous qu'au moins un Locrit est:")
        print("   - Actif")
        print("   - Configuré pour être ouvert aux autres Locrits")
        sys.exit(1)

    print(f"✅ {len(locrits)} Locrit(s) trouvé(s):")
    for locrit in locrits:
        print(f"   - {locrit['name']}: {locrit['description']}")
        print(f"     Modèle: {locrit['model']}")

    # Sélectionner le premier Locrit pour le test
    target_locrit = locrits[0]['name']
    print(f"\n3. Test de communication avec '{target_locrit}'...")

    # Obtenir les infos détaillées du Locrit
    info_result = client.get_locrit_info(target_locrit)
    if info_result.get('success'):
        locrit_info = info_result['locrit']
        print(f"✅ Informations du Locrit:")
        print(f"   Description: {locrit_info['description']}")
        print(f"   Modèle: {locrit_info['model']}")
        print(f"   Ouvert aux Locrits: {locrit_info['open_to'].get('locrits', False)}")

    # Test de chat simple
    print(f"\n4. Test de chat simple...")
    message = "Bonjour ! Peux-tu me dire qui tu es et quel est ton rôle ?"

    print(f"Envoi du message: \"{message}\"")
    chat_result = client.chat_with_locrit(
        target_locrit,
        message,
        sender_name="TestBot",
        context="Test de communication inter-Locrits"
    )

    if chat_result.get('success'):
        print(f"✅ Réponse reçue:")
        print(f"   {target_locrit}: {chat_result['response']}")
        print(f"   Modèle utilisé: {chat_result['model']}")
        print(f"   Timestamp: {chat_result['timestamp']}")
    else:
        print(f"❌ Erreur: {chat_result.get('error')}")

    # Test de chat en streaming
    print(f"\n5. Test de chat en streaming...")
    stream_message = "Raconte-moi une courte histoire sur les Locrits qui communiquent entre eux."

    print(f"Envoi du message en streaming: \"{stream_message}\"")
    client.chat_stream_with_locrit(
        target_locrit,
        stream_message,
        sender_name="TestBot",
        context="Test de streaming inter-Locrits"
    )

    # Test de conversation multi-tours
    print(f"\n6. Test de conversation multi-tours...")
    conversation_messages = [
        "Quel est ton nom ?",
        "Que penses-tu de la communication entre IA ?",
        "Merci pour cette conversation !"
    ]

    for i, msg in enumerate(conversation_messages, 1):
        print(f"\nTour {i}: \"{msg}\"")
        result = client.chat_with_locrit(
            target_locrit,
            msg,
            sender_name="TestBot",
            context=f"Tour {i} d'une conversation de test"
        )

        if result.get('success'):
            print(f"{target_locrit}: {result['response']}")
        else:
            print(f"❌ Erreur: {result.get('error')}")

        # Petite pause entre les messages
        time.sleep(1)

    print(f"\n" + "=" * 50)
    print("🎉 Tests terminés avec succès !")
    print("\nLes Locrits peuvent maintenant communiquer entre eux via l'API.")
    print("Utilisez les endpoints suivants pour vos propres implémentations:")
    print("- GET  /api/v1/locrits : Lister les Locrits")
    print("- GET  /api/v1/locrits/<name>/info : Info d'un Locrit")
    print("- POST /api/v1/locrits/<name>/chat : Chat simple")
    print("- POST /api/v1/locrits/<name>/chat/stream : Chat streaming")


if __name__ == "__main__":
    main()