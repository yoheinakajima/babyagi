# babyagi/api/__init__.py

from flask import Blueprint, jsonify, request, g
from datetime import datetime
from io import StringIO
import logging
import os
import sys
import importlib.util

logger = logging.getLogger(__name__)

def create_api_blueprint():
    api = Blueprint('api', __name__, url_prefix='/api')

    # Removed the before_request function since g.functionz is set in the main app

    @api.route('/functions')
    def get_functions():
        logger.debug("Accessing /api/functions route.")
        try:
            functions = g.functionz.get_all_functions()
            logger.debug(f"Retrieved {len(functions)} functions.")
            return jsonify(functions)
        except Exception as e:
            logger.error(f"Error in get_functions: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @api.route('/function/<function_name>')
    def get_function(function_name):
        logger.debug(f"Accessing /api/function/{function_name} route.")
        try:
            function = g.functionz.db.get_function(function_name)
            if not function:
                logger.warning(f"Function '{function_name}' not found.")
                return jsonify({"error": f"Function '{function_name}' not found."}), 404
            return jsonify(function)
        except Exception as e:
            logger.error(f"Error getting function {function_name}: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @api.route('/function/<function_name>', methods=['PUT'])
    def update_function(function_name):
        logger.debug(f"Accessing /api/function/{function_name} [PUT] route.")
        try:
            data = request.get_json()
            if not data or 'code' not in data:
                logger.warning("No 'code' provided in request data.")
                return jsonify({"error": "No 'code' provided in request data."}), 400
            g.functionz.update_function(function_name, code=data['code'])
            logger.info(f"Function '{function_name}' updated successfully.")
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error updating function {function_name}: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @api.route('/execute/<function_name>', methods=['POST'])
    def execute_function(function_name):
        logger.debug(f"Accessing /api/execute/{function_name} [POST] route.")
        try:
            params = request.get_json() or {}

            if function_name == 'execute_function_wrapper':
                # Special handling for execute_function_wrapper
                inner_function_name = params.pop('function_name', None)
                args = params.pop('args', [])
                kwargs = params.pop('kwargs', {})
                result = g.functionz.executor.execute(function_name, inner_function_name, *args, **kwargs)
            else:
                # Normal execution for other functions
                result = g.functionz.executor.execute(function_name, **params)

            logger.info(f"Function '{function_name}' executed successfully.")
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @api.route('/function/<function_name>/versions')
    def get_function_versions(function_name):
        logger.debug(f"Accessing /api/function/{function_name}/versions route.")
        try:
            versions = g.functionz.get_function_versions(function_name)
            logger.debug(f"Retrieved {len(versions)} versions for function '{function_name}'.")
            return jsonify(versions)
        except Exception as e:
            logger.error(f"Error getting versions for function {function_name}: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @api.route('/function/<function_name>/activate/<version>', methods=['POST'])
    def activate_function_version(function_name, version):
        logger.debug(f"Accessing /api/function/{function_name}/activate/{version} [POST] route.")
        try:
            g.functionz.activate_function_version(function_name, int(version))
            logger.info(f"Version {version} of function '{function_name}' activated successfully.")
            return jsonify({"status": "success"})
        except ValueError:
            logger.warning(f"Invalid version number provided: {version}")
            return jsonify({"error": "Invalid version number."}), 400
        except Exception as e:
            logger.error(f"Error activating version {version} for function {function_name}: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500


    @api.route('/logs/<function_name>')
    @api.route('/logs', defaults={'function_name': None})
    def get_logs(function_name):
        logger.debug(f"Accessing /api/logs/{function_name if function_name else 'all'} route.")
        try:
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            triggered_by_log_id_str = request.args.get('triggered_by_log_id')  # New filter
            start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
            end_date = datetime.fromisoformat(end_date_str) if end_date_str else None
            triggered_by_log_id = int(triggered_by_log_id_str) if triggered_by_log_id_str else None  # Convert to int if provided

            logs = g.functionz.db.get_logs(function_name, start_date, end_date, triggered_by_log_id)
            if function_name:
                logger.debug(f"Retrieved {len(logs)} logs for function '{function_name}'.")
            else:
                logger.debug(f"Retrieved {len(logs)} logs for all functions.")
            return jsonify(logs)
        except ValueError:
            logger.warning("Invalid date format or triggered_by_log_id provided.")
            return jsonify({"error": "Invalid date format or triggered_by_log_id. Use ISO format for dates and integer for triggered_by_log_id."}), 400
        except Exception as e:
            logger.error(f"Error getting logs for function '{function_name}': {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @api.route('/log_bundle/<int:log_id>')
    def get_log_bundle(log_id):
        logger.debug(f"Accessing /api/log_bundle/{log_id} route.")
        try:
            logs = g.functionz.db.get_log_bundle(log_id)
            return jsonify({'logs': logs})
        except Exception as e:
            logger.error(f"Error getting log bundle for log_id '{log_id}': {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500


    @api.route('/triggers/<function_name>', methods=['GET'])
    def get_triggers(function_name):
        logger.debug(f"Accessing /api/triggers/{function_name} [GET] route.")
        try:
            triggers = g.functionz.get_triggers_for_function(function_name)
            trigger_list = [
                getattr(trigger.triggering_function, 'name', 'any function')
                for trigger in triggers
            ]
            logger.debug(f"Retrieved {len(trigger_list)} triggers for function '{function_name}'.")
            return jsonify(trigger_list)
        except Exception as e:
            logger.error(f"Error getting triggers for function {function_name}: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500


    logger.info("API blueprint created successfully.")
    return api
