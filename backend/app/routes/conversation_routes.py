from flask import Blueprint, request, jsonify, g
from app.controllers.conversation_controller import ConversationController
from app.repositories.conversation_repository import ConversationRepository
from app.services.ai.ai_factory import create_service
from app.services.scoring_service import ScoringService
from app.services.recommendation_service import RecommendationService
from app.utils.decorators import handle_errors, validate_json, require_auth
from app.auth.jwt_auth import require_roles
from app.schemas.conversation_schema import (
    ConversationCreateSchema,
    MessageSendSchema,
)
from app import mongo


bp = Blueprint('conversations', __name__)


def _get_controller() -> ConversationController:
    # Access mongo.db within app/request context
    conversation_repo = ConversationRepository(mongo.db.conversations)
    ai_service = create_service()
    scoring_service = ScoringService()
    recommendation_service = RecommendationService()
    return ConversationController(
        conversation_repo=conversation_repo,
        ai_service=ai_service,
        scoring_service=scoring_service,
        recommendation_service=recommendation_service,
    )


create_schema = ConversationCreateSchema()
message_schema = MessageSendSchema()


@bp.route('', methods=['POST'])
@handle_errors
@require_auth  # <-- Thêm xác thực ở đây
@validate_json(create_schema)
def create_conversation():
    """
    Create a new conversation
    ---
    tags:
      - Conversations
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: string
            topic:
              type: string
            level:
              type: string
              enum: [N5, N4, N3, N2, N1]
          required: [user_id, topic, level]
    responses:
      201:
        description: Conversation created
      400:
        description: Validation error
    """
    data = request.get_json()
    controller = _get_controller()
    conversation = controller.create_conversation(
        user_id=data['user_id'],
        topic=data['topic'],
        level=data['level']
    )
    return jsonify(conversation.to_dict()), 201


@bp.route('/<conversation_id>', methods=['GET'])
@handle_errors
@require_auth  # <-- Thêm xác thực
def get_conversation(conversation_id: str):
    """
    Get conversation by ID
    ---
    tags:
      - Conversations
    parameters:
      - in: path
        name: conversation_id
        required: true
        type: string
    responses:
      200:
        description: Conversation
      404:
        description: Not found
    """
    controller = _get_controller()
    conversation = controller.get_conversation(conversation_id)
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    return jsonify(conversation.to_dict())


@bp.route('/<conversation_id>/messages', methods=['POST'])
@handle_errors
@require_auth  # <-- Thêm xác thực
@validate_json(message_schema)
def send_message(conversation_id: str):
    """
    Send a message to a conversation
    ---
    tags:
      - Conversations
    consumes:
      - application/json
    parameters:
      - in: path
        name: conversation_id
        required: true
        type: string
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
            response_time:
              type: integer
          required: [message]
    responses:
      200:
        description: AI response and updated score
      400:
        description: Validation error
      404:
        description: Not found
    """
    data = request.get_json()
    controller = _get_controller()
    result = controller.send_message(
        conversation_id=conversation_id,
        message_content=data['message'],
        response_time=data.get('response_time')
    )
    return jsonify(result)


@bp.route('/<conversation_id>/recommendations', methods=['GET'])
@handle_errors
@require_auth  # <-- Thêm xác thực
def get_recommendations(conversation_id: str):
    """
    Get course recommendations for a conversation
    ---
    tags:
      - Conversations
    parameters:
      - in: path
        name: conversation_id
        required: true
        type: string
    responses:
      200:
        description: List of recommendations
      404:
        description: Not found
    """
    controller = _get_controller()
    recommendations = controller.get_recommendations(conversation_id)
    return jsonify(recommendations)


@bp.route('/users/<user_id>', methods=['GET'])
@handle_errors
@require_auth  # <-- Thêm xác thực
def get_user_conversations(user_id: str):
    """
    List conversations by user
    ---
    tags:
      - Conversations
    parameters:
      - in: path
        name: user_id
        required: true
        type: string
      - in: query
        name: skip
        type: integer
        required: false
      - in: query
        name: limit
        type: integer
        required: false
    responses:
      200:
        description: List of conversations
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    controller = _get_controller()
    conversations = controller.get_user_conversations(user_id, skip, limit)
    return jsonify([c.to_dict() for c in conversations])


@bp.route('/users/<user_id>/statistics', methods=['GET'])
@handle_errors
@require_auth  # <-- Thêm xác thực
def get_user_statistics(user_id: str):
    """
    Get conversation statistics for a user
    ---
    tags:
      - Conversations
    parameters:
      - in: path
        name: user_id
        required: true
        type: string
    responses:
      200:
        description: Statistics
    """
    controller = _get_controller()
    stats = controller.get_user_statistics(user_id)
    return jsonify(stats)


# Ví dụ route phân quyền theo role admin
@bp.route('/admin/stats', methods=['GET'])
@handle_errors
@require_roles('admin')  # <-- Chỉ admin mới được truy cập
def admin_stats():
    return jsonify({"msg": "Admin statistics"})
