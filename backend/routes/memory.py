"""
Memory API routes for viewing Locrit memory through the web interface.
"""

import asyncio
from flask import Blueprint, request, jsonify, session
from backend.middleware.auth import login_required
from src.services.memory_manager_service import memory_manager
from src.services.config_service import config_service

memory_bp = Blueprint('memory', __name__)


@memory_bp.route('/api/locrits/<locrit_name>/memory/summary', methods=['GET'])
def get_memory_summary(locrit_name):
    """Get complete memory summary for a Locrit"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Check if user has access to memory
        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète non autorisé pour ce Locrit'}), 403

        # Get memory summary
        summary = asyncio.run(memory_manager.get_full_memory_summary(locrit_name))
        return jsonify(summary)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/search', methods=['GET'])
def search_memory(locrit_name):
    """Search through Locrit memory"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Check access level
        access_to = settings.get('access_to', {})
        has_quick_memory = access_to.get('quick_memory', False)
        has_full_memory = access_to.get('full_memory', False)

        if not (has_quick_memory or has_full_memory):
            return jsonify({'error': 'Accès à la mémoire non autorisé pour ce Locrit'}), 403

        # Get search parameters
        query = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 results

        if not query:
            return jsonify({'error': 'Paramètre de recherche requis'}), 400

        # Search memory
        results = asyncio.run(memory_manager.search_memories(locrit_name, query, limit))

        # If only quick memory access, limit results
        if has_quick_memory and not has_full_memory:
            results = results[:5]  # Limit to 5 results for quick memory

        return jsonify({
            'query': query,
            'results': results,
            'total': len(results),
            'access_level': 'full' if has_full_memory else 'quick'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/sessions', methods=['GET'])
def get_memory_sessions(locrit_name):
    """Get conversation sessions for a Locrit"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Check if user has access to memory
        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        # Get memory summary which includes sessions
        summary = asyncio.run(memory_manager.get_full_memory_summary(locrit_name))

        sessions = summary.get('sessions', [])
        return jsonify({
            'sessions': sessions,
            'total': len(sessions)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/sessions/<session_id>/messages', methods=['GET'])
def get_session_messages(locrit_name, session_id):
    """Get messages for a specific session"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Check if user has access to memory
        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        # Get limit parameter
        limit = min(int(request.args.get('limit', 100)), 500)  # Max 500 messages

        # Get conversation history
        messages = asyncio.run(memory_manager.get_conversation_history(locrit_name, session_id, limit))

        return jsonify({
            'session_id': session_id,
            'messages': messages,
            'total': len(messages)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/concepts', methods=['GET'])
def get_memory_concepts(locrit_name):
    """Get concepts learned by the Locrit"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Check if user has access to memory
        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        # Get memory summary which includes concepts
        summary = asyncio.run(memory_manager.get_full_memory_summary(locrit_name))

        concepts = summary.get('top_concepts', [])
        return jsonify({
            'concepts': concepts,
            'total': len(concepts)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/concepts/<concept_name>/related', methods=['GET'])
def get_related_concepts(locrit_name, concept_name):
    """Get concepts related to a specific concept"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Check if user has access to memory
        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        # Get depth parameter
        depth = min(int(request.args.get('depth', 2)), 5)  # Max depth 5

        # Get related concepts
        related = asyncio.run(memory_manager.get_related_concepts(locrit_name, concept_name, depth))

        return jsonify({
            'concept': concept_name,
            'related_concepts': related,
            'total': len(related),
            'depth': depth
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/stats', methods=['GET'])
def get_memory_stats(locrit_name):
    """Get memory statistics for a Locrit"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Check if user has access to memory (quick memory is sufficient for stats)
        access_to = settings.get('access_to', {})
        has_memory_access = access_to.get('quick_memory', False) or access_to.get('full_memory', False)

        if not has_memory_access:
            return jsonify({'error': 'Accès à la mémoire requis'}), 403

        # Get memory summary
        summary = asyncio.run(memory_manager.get_full_memory_summary(locrit_name))

        # Return only statistics for quick memory access
        if 'statistics' in summary:
            return jsonify({
                'locrit_name': locrit_name,
                'statistics': summary['statistics'],
                'access_level': 'full' if access_to.get('full_memory', False) else 'quick'
            })
        else:
            return jsonify({'error': summary.get('error', 'Erreur lors de la récupération des statistiques')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500