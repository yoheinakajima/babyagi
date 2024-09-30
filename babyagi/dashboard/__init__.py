# babyagi/dashboard/__init__.py

from flask import Blueprint, render_template, g, send_from_directory
import logging
import os

logger = logging.getLogger(__name__)

def create_dashboard(func_instance, dashboard_route):
    if func_instance is None:
        raise ValueError("func_instance cannot be None")
    if dashboard_route is None:
        raise ValueError("dashboard_route cannot be None")

    dashboard = Blueprint('dashboard', __name__, 
                          template_folder='templates', 
                          static_folder='static',
                          static_url_path='/dashboard/static')

    logger.info("Creating dashboard blueprint...")

    @dashboard.before_request
    def before_request():
        """Set up the necessary context before each request."""
        g.functionz = func_instance
        g.dashboard_route = dashboard_route
        logger.debug("Set g.functionz and g.dashboard_route for the request context.")

    @dashboard.route('/')
    def dashboard_home():
        logger.info("Accessing dashboard home page.")
        try:
            logger.debug(f"Dashboard Route: {g.dashboard_route}")
            return render_template('index.html', dashboard_route=g.dashboard_route)
        except Exception as e:
            logger.error(f"Error in dashboard_home: {str(e)}", exc_info=True)
            return f"Error loading dashboard: {str(e)}", 500

    @dashboard.route('/function/<function_name>')
    def function_detail(function_name):
        logger.info(f"Accessing function detail for: {function_name}")
        try:
            function = g.functionz.db.get_function(function_name)
            if not function:
                logger.warning(f"Function '{function_name}' not found.")
                return f"Function '{function_name}' not found.", 404
            return render_template('function_details.html', function_name=function_name, dashboard_route=g.dashboard_route)
        except Exception as e:
            logger.error(f"Error in function_detail: {str(e)}", exc_info=True)
            return f"Error loading function detail: {str(e)}", 500

    @dashboard.route('/graph')
    def function_graph():
        logger.info("Accessing function relationship graph page.")
        try:
            return render_template('function_graph.html', dashboard_route=g.dashboard_route)
        except Exception as e:
            logger.error(f"Error in function_graph: {str(e)}", exc_info=True)
            return f"Error loading function graph: {str(e)}", 500

    @dashboard.route('/mermaid')
    def function_graph_mermaid():
        logger.info("Accessing mermaid function relationship graph page.")
        try:
            return render_template('function_graph_mermaid.html', dashboard_route=g.dashboard_route)
        except Exception as e:
            logger.error(f"Error in function_graph_mermaid: {str(e)}", exc_info=True)
            return f"Error loading mermaid function graph: {str(e)}", 500

    @dashboard.route('/3d')
    def function_graph_3d():
        logger.info("Accessing 3D function relationship graph page.")
        try:
            return render_template('function_graph_3d.html', dashboard_route=g.dashboard_route)
        except Exception as e:
            logger.error(f"Error in function_graph_3d: {str(e)}", exc_info=True)
            return f"Error loading 3D function graph: {str(e)}", 500

    @dashboard.route('/logs')
    def logs_dashboard():
        logger.info("Accessing logs dashboard.")
        try:
            return render_template('logs_dashboard.html', dashboard_route=g.dashboard_route)
        except Exception as e:
            logger.error(f"Error in logs_dashboard: {str(e)}", exc_info=True)
            return f"Error loading logs dashboard: {str(e)}", 500

    @dashboard.route('/log/<int:log_id>')
    def log_page(log_id):
        logger.info(f"Accessing log page for Log ID {log_id}.")
        try:
            return render_template(
                'log_page.html',
                log_id=log_id,
                dashboard_route=g.dashboard_route  # Pass the dashboard route if needed
            )
        except Exception as e:
            logger.error(f"Error in log_page for Log ID {log_id}: {str(e)}", exc_info=True)
            return f"Error loading log page for Log ID {log_id}: {str(e)}", 500
    
    @dashboard.route('/log_graph')
    def log_relationship_graph():
        logger.info("Accessing log relationship graph.")
        try:
            return render_template('log_relationship_graph.html', dashboard_route=g.dashboard_route)
        except Exception as e:
            logger.error(f"Error in log_relationship_graph: {str(e)}", exc_info=True)
            return f"Error loading log relationship graph: {str(e)}", 500

    @dashboard.route('/chat')
    def chat_page():
        logger.info("Accessing chat page.")
        try:
            return render_template('chat.html', dashboard_route=g.dashboard_route)
        except Exception as e:
            logger.error(f"Error in chat_page: {str(e)}", exc_info=True)
            return f"Error loading chat page: {str(e)}", 500
    
    @dashboard.route('/<path:filename>')
    def serve_static_files(filename):
        """Serve static files from the dashboard's static folder."""
        logger.debug(f"Serving static file: {filename}")
        try:
            return send_from_directory(dashboard.static_folder, filename)
        except Exception as e:
            logger.error(f"Error serving static file '{filename}': {str(e)}", exc_info=True)
            return "File not found.", 404

    logger.info("Dashboard blueprint created successfully.")
    return dashboard

logger.info("Dashboard __init__.py loaded successfully.")
