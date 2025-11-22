
from functools import wraps
from flask import request, jsonify
from marshmallow import ValidationError
from app.auth.jwt_auth import require_auth as jwt_require_auth



def handle_errors(f):
    """
    Decorator to handle common errors
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except ValidationError as e:
            return jsonify({'error': 'Validation error', 'details': e.messages}), 400
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    return decorated_function


def validate_json(schema):
    """
    Decorator to validate JSON request body

    Args:
        schema: Marshmallow schema instance
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            json_data = request.get_json()

            if not json_data:
                return jsonify({'error': 'No JSON data provided'}), 400

            # Validate with schema
            errors = schema.validate(json_data)
            if errors:
                return jsonify({'error': 'Validation error', 'details': errors}), 400

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_auth(f):
    return jwt_require_auth(f)
