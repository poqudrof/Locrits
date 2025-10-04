"""
Memory API routes for viewing Locrit memory through the web interface.
"""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, jsonify, session
from backend.middleware.auth import login_required
from src.services.memory_manager_service import memory_manager
from src.services.config_service import config_service
from src.services.comprehensive_logging_service import comprehensive_logger, LogLevel, LogCategory

# Compatibility helper for older Python versions
def async_to_thread(func, *args, **kwargs):
    """Compatibility wrapper for asyncio.to_thread (Python 3.9+)"""
    if hasattr(asyncio, 'to_thread'):
        return asyncio.to_thread(func, *args, **kwargs)
    else:
        # Fallback for older Python versions
        executor = ThreadPoolExecutor()
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(executor, func, *args, **kwargs)

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
        # Start operation tracking
        operation_id = comprehensive_logger.start_operation(f"api_memory_search_{locrit_name}")

        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            comprehensive_logger.log_api_request(
                endpoint=f"/api/locrits/{locrit_name}/memory/search",
                method="GET",
                locrit_name=locrit_name,
                status_code=404,
                error="Locrit not found"
            )
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Check access level
        access_to = settings.get('access_to', {})
        has_quick_memory = access_to.get('quick_memory', False)
        has_full_memory = access_to.get('full_memory', False)

        if not (has_quick_memory or has_full_memory):
            comprehensive_logger.log_api_request(
                endpoint=f"/api/locrits/{locrit_name}/memory/search",
                method="GET",
                locrit_name=locrit_name,
                status_code=403,
                error="Memory access not authorized"
            )
            return jsonify({'error': 'Accès à la mémoire non autorisé pour ce Locrit'}), 403

        # Get search parameters
        query = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 results

        if not query:
            comprehensive_logger.log_api_request(
                endpoint=f"/api/locrits/{locrit_name}/memory/search",
                method="GET",
                locrit_name=locrit_name,
                status_code=400,
                error="Search query required"
            )
            return jsonify({'error': 'Paramètre de recherche requis'}), 400

        # Search memory
        results = asyncio.run(memory_manager.search_memories(locrit_name, query, limit))

        # If only quick memory access, limit results
        if has_quick_memory and not has_full_memory:
            results = results[:5]  # Limit to 5 results for quick memory

        # End operation tracking
        duration_ms = comprehensive_logger.end_operation(operation_id)

        # Log successful API request
        comprehensive_logger.log_api_request(
            endpoint=f"/api/locrits/{locrit_name}/memory/search",
            method="GET",
            locrit_name=locrit_name,
            duration_ms=duration_ms,
            status_code=200,
            data={
                "query": query,
                "results_count": len(results),
                "access_level": 'full' if has_full_memory else 'quick'
            }
        )

        return jsonify({
            'query': query,
            'results': results,
            'total': len(results),
            'access_level': 'full' if has_full_memory else 'quick'
        })

    except Exception as e:
        # End operation tracking for failed request
        if 'operation_id' in locals():
            duration_ms = comprehensive_logger.end_operation(operation_id)

        # Log failed API request
        comprehensive_logger.log_api_request(
            endpoint=f"/api/locrits/{locrit_name}/memory/search",
            method="GET",
            locrit_name=locrit_name,
            status_code=500,
            error=str(e)
        )

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


@memory_bp.route('/api/locrits/<locrit_name>/memory/concepts/details', methods=['GET'])
def get_concept_details(locrit_name):
    """Get detailed information about a specific concept"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Check if user has access to memory
        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        # Get concept name and type from query parameters
        concept_name = request.args.get('name', None)
        concept_type = request.args.get('type', None)

        if not concept_name:
            return jsonify({'error': 'Nom du concept requis'}), 400

        # Get concept details
        concept_details = asyncio.run(memory_manager.get_concept_details(locrit_name, concept_name, concept_type))

        if not concept_details:
            return jsonify({'error': 'Concept non trouvé'}), 404

        return jsonify(concept_details)

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


# Memory editing endpoints

@memory_bp.route('/api/locrits/<locrit_name>/memory/messages/<message_id>', methods=['GET'])
def get_message_by_id(locrit_name, message_id):
    """Get a specific message by ID"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        message = asyncio.run(memory_manager.get_message_by_id(locrit_name, message_id))
        if not message:
            return jsonify({'error': 'Message non trouvé'}), 404

        return jsonify({'message': message})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/messages/<message_id>', methods=['PUT'])
def edit_message(locrit_name, message_id):
    """Edit a specific message"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Nouveau contenu requis'}), 400

        success = asyncio.run(memory_manager.edit_message(locrit_name, message_id, data['content']))
        if not success:
            return jsonify({'error': 'Échec de la modification du message'}), 500

        return jsonify({'success': True, 'message': 'Message modifié avec succès'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/messages/<message_id>', methods=['DELETE'])
def delete_message(locrit_name, message_id):
    """Delete a specific message"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        success = asyncio.run(memory_manager.delete_message(locrit_name, message_id))
        if not success:
            return jsonify({'error': 'Échec de la suppression du message'}), 500

        return jsonify({'success': True, 'message': 'Message supprimé avec succès'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/sessions/<session_id>', methods=['GET'])
def get_session_by_id(locrit_name, session_id):
    """Get a specific session by ID"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        session = asyncio.run(memory_manager.get_session_by_id(locrit_name, session_id))
        if not session:
            return jsonify({'error': 'Session non trouvée'}), 404

        return jsonify({'session': session})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/sessions/<session_id>', methods=['DELETE'])
def delete_session(locrit_name, session_id):
    """Delete a specific session and all its messages"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        success = asyncio.run(memory_manager.delete_session(locrit_name, session_id))
        if not success:
            return jsonify({'error': 'Échec de la suppression de la session'}), 500

        return jsonify({'success': True, 'message': 'Session supprimée avec succès'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/memories', methods=['GET'])
def get_all_memories(locrit_name):
    """Get all standalone memory entries"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        memories = asyncio.run(memory_manager.get_all_memories(locrit_name))

        return jsonify({
            'memories': memories,
            'total': len(memories)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/memories', methods=['POST'])
def add_memory(locrit_name):
    """Add a standalone memory entry"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Contenu de la mémoire requis'}), 400

        content = data['content']
        importance = data.get('importance', 0.5)
        metadata = data.get('metadata', {})

        # Validate importance
        if not (0.0 <= importance <= 1.0):
            return jsonify({'error': 'L\'importance doit être entre 0.0 et 1.0'}), 400

        memory_id = asyncio.run(memory_manager.add_memory(locrit_name, content, importance, metadata))
        if not memory_id:
            return jsonify({'error': 'Échec de l\'ajout de la mémoire'}), 500

        return jsonify({'success': True, 'memory_id': memory_id, 'message': 'Mémoire ajoutée avec succès'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/memories/<memory_id>', methods=['DELETE'])
def delete_memory(locrit_name, memory_id):
    """Delete a standalone memory entry"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        success = asyncio.run(memory_manager.delete_memory(locrit_name, memory_id))
        if not success:
            return jsonify({'error': 'Échec de la suppression de la mémoire'}), 500

        return jsonify({'success': True, 'message': 'Mémoire supprimée avec succès'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/concepts/<concept_id>', methods=['PUT'])
def edit_concept(locrit_name, concept_id):
    """Edit a concept's properties"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données de modification requises'}), 400

        name = data.get('name')
        description = data.get('description')
        confidence = data.get('confidence')

        # Validate confidence if provided
        if confidence is not None and not (0.0 <= confidence <= 1.0):
            return jsonify({'error': 'La confiance doit être entre 0.0 et 1.0'}), 400

        success = asyncio.run(memory_manager.edit_concept(locrit_name, concept_id, name, description, confidence))
        if not success:
            return jsonify({'error': 'Échec de la modification du concept'}), 500

        return jsonify({'success': True, 'message': 'Concept modifié avec succès'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/concepts/<concept_id>', methods=['DELETE'])
def delete_concept(locrit_name, concept_id):
    """Delete a concept and its relationships"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        success = asyncio.run(memory_manager.delete_concept(locrit_name, concept_id))
        if not success:
            return jsonify({'error': 'Échec de la suppression du concept'}), 500

        return jsonify({'success': True, 'message': 'Concept supprimé avec succès'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/locrits/<locrit_name>/memory/clear', methods=['DELETE'])
def clear_all_memory(locrit_name):
    """Clear all memory data for the Locrit"""
    try:
        # Verify the Locrit exists and user has access
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        access_to = settings.get('access_to', {})
        if not access_to.get('full_memory', False):
            return jsonify({'error': 'Accès à la mémoire complète requis'}), 403

        # Require confirmation
        data = request.get_json()
        if not data or not data.get('confirm'):
            return jsonify({'error': 'Confirmation requise pour supprimer toute la mémoire'}), 400

        success = asyncio.run(memory_manager.clear_all_memory(locrit_name))
        if not success:
            return jsonify({'error': 'Échec de la suppression de toute la mémoire'}), 500

        return jsonify({'success': True, 'message': 'Toute la mémoire a été supprimée avec succès'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# New modular memory system endpoints

@memory_bp.route('/api/v1/locrits/<locrit_name>/memory/store-conversation', methods=['POST'])
def store_conversation_in_memory(locrit_name):
    """Store conversation messages in the new modular memory system"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({'error': 'Messages requis'}), 400

        messages = data['messages']
        force_update = data.get('force_update', False)

        if not messages:
            return jsonify({'error': 'Aucun message à sauvegarder'}), 400

        # Import the new memory system
        try:
            import asyncio
            import sys
            import os

            # Add the project root to Python path
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from src.services.memory import create_memory_system

            async def process_conversation():
                # Initialize memory system
                memory_manager, memory_tools = await create_memory_system(
                    locrit_name=locrit_name,
                    config_path="config/memory.yaml"
                )

                try:
                    # Process messages and let LLM decide storage
                    results = {
                        'total_processed': 0,
                        'memories_stored': 0,
                        'decisions': []
                    }

                    for message in messages:
                        if not message.get('content', '').strip():
                            continue

                        # Let the AI analyze and decide storage
                        analysis = await memory_tools["analyze_memory_decision"](
                            content=message['content'],
                            context={
                                'role': message.get('type', 'user'),
                                'timestamp': message.get('timestamp'),
                                'message_id': message.get('id'),
                                'source': 'web_chat'
                            }
                        )

                        if analysis['success']:
                            decision = analysis['recommendation']
                            results['decisions'].append({
                                'content_preview': message['content'][:50] + '...',
                                'memory_type': decision['memory_type'],
                                'importance': decision['importance'],
                                'reasoning': decision['reasoning']
                            })

                            # Store based on LLM decision
                            if decision['memory_type'] == 'graph':
                                store_result = await memory_tools["store_graph_memory"](
                                    content=message['content'],
                                    importance=decision['importance'],
                                    metadata={
                                        'role': message.get('type', 'user'),
                                        'timestamp': message.get('timestamp'),
                                        'source': 'web_chat',
                                        'ai_classified': True
                                    }
                                )
                            else:
                                store_result = await memory_tools["store_vector_memory"](
                                    content=message['content'],
                                    importance=decision['importance'],
                                    tags=decision['tags'],
                                    metadata={
                                        'role': message.get('type', 'user'),
                                        'timestamp': message.get('timestamp'),
                                        'source': 'web_chat',
                                        'ai_classified': True
                                    }
                                )

                            if store_result['success']:
                                results['memories_stored'] += 1

                        results['total_processed'] += 1

                    # Force memory update if requested
                    if force_update:
                        update_result = await memory_tools["update_memory_now"](force=True)
                        results['update_result'] = update_result

                    return results

                finally:
                    await memory_manager.close()

            # Run the async function
            result = asyncio.run(process_conversation())

            return jsonify({
                'success': True,
                'message': f'Processed {result["total_processed"]} messages, stored {result["memories_stored"]} memories',
                'details': result
            })

        except ImportError as e:
            # Fallback to legacy memory system
            try:
                from src.services.kuzu_memory_service import KuzuMemoryService

                async def fallback_process():
                    # Use the existing memory service as fallback
                    memory_service = KuzuMemoryService(locrit_name)

                    # Simple storage using the legacy system
                    stored_count = 0
                    for message in messages:
                        if not message.get('content', '').strip():
                            continue

                        # Store message in legacy format
                        role = message.get('type', 'user')
                        content = message['content']
                        session_id = f"web_chat_{locrit_name}"

                        await memory_service.save_message(role, content, session_id)
                        stored_count += 1

                    return {
                        'total_processed': len(messages),
                        'memories_stored': stored_count,
                        'method': 'legacy_kuzu'
                    }

                # Run the fallback process
                result = asyncio.run(fallback_process())

                return jsonify({
                    'success': True,
                    'message': f'Stored {result["memories_stored"]} messages using legacy system',
                    'fallback': True,
                    'details': result
                })

            except Exception as fallback_error:
                return jsonify({
                    'error': 'Both new and legacy memory systems failed',
                    'new_system_error': str(e),
                    'legacy_system_error': str(fallback_error)
                }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/v1/locrits/<locrit_name>/memory/ai-search', methods=['GET'])
def ai_search_memory(locrit_name):
    """Search memory using the AI-powered modular system"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        query = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 10)), 50)
        search_strategy = request.args.get('strategy', 'auto')

        if not query:
            return jsonify({'error': 'Paramètre de recherche requis'}), 400

        try:
            import asyncio
            import sys
            import os

            # Add the project root to Python path
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from src.services.memory import create_memory_system

            async def search_memories():
                # Initialize memory system
                memory_manager, memory_tools = await create_memory_system(
                    locrit_name=locrit_name,
                    config_path="config/memory.yaml"
                )

                try:
                    # Search using AI-powered comprehensive search
                    search_result = await memory_tools["search_all_memory"](
                        query=query,
                        limit=limit,
                        strategy=search_strategy
                    )

                    return search_result

                finally:
                    await memory_manager.close()

            # Run the async function
            result = asyncio.run(search_memories())

            if result['success']:
                return jsonify({
                    'query': query,
                    'strategy': result['strategy'],
                    'results': result['results'],
                    'total': result['total_results']
                })
            else:
                return jsonify({'error': 'Search failed'}), 500

        except ImportError as e:
            # Fallback to legacy search
            results = asyncio.run(memory_manager.search_memories(locrit_name, query, limit))
            return jsonify({
                'query': query,
                'results': results,
                'total': len(results),
                'fallback': True
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/api/v1/locrits/<locrit_name>/memory/status', methods=['GET'])
def get_memory_system_status(locrit_name):
    """Get comprehensive status of the memory system"""
    try:
        # Verify the Locrit exists
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        try:
            import asyncio
            import sys
            import os

            # Add the project root to Python path
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from src.services.memory import create_memory_system

            async def get_status():
                # Initialize memory system
                memory_manager, memory_tools = await create_memory_system(
                    locrit_name=locrit_name,
                    config_path="config/memory.yaml"
                )

                try:
                    # Get comprehensive status
                    status_result = await memory_tools["get_memory_status"]()
                    return status_result

                finally:
                    await memory_manager.close()

            # Run the async function
            result = asyncio.run(get_status())

            return jsonify(result)

        except ImportError as e:
            return jsonify({
                'error': 'New memory system not available',
                'fallback_status': 'legacy_system_active',
                'details': str(e)
            }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500