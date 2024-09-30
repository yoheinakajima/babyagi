# babyagi/__init__.py

from flask import Flask, g
from .functionz.core.framework import Functionz
from .dashboard import create_dashboard
from .api import create_api_blueprint
import os
import importlib.util
import traceback
import sys

# Singleton instance of the functionz framework
_func_instance = Functionz()


def get_func_instance():
    return _func_instance

def create_app(dashboard_route='/dashboard'):
    app = Flask(__name__)

    # Remove leading slash if present to avoid double slashes
    if dashboard_route.startswith('/'):
        dashboard_route = dashboard_route[1:]

    # Create and register the dashboard blueprint with dashboard_route
    dashboard_blueprint = create_dashboard(_func_instance, dashboard_route)

    # Create and register the API blueprint
    api_blueprint = create_api_blueprint()

    # Register the blueprints
    app.register_blueprint(dashboard_blueprint, url_prefix=f'/{dashboard_route}')
    app.register_blueprint(api_blueprint)  # Mounted at '/api' as defined in the blueprint

    # Store the dashboard route for use in templates
    app.config['DASHBOARD_ROUTE'] = dashboard_route

    # Ensure the Functionz instance is accessible in the request context
    @app.before_request
    def set_functionz():
        g.functionz = _func_instance
        g.dashboard_route = dashboard_route  # Optional, if needed globally

    return app

# Function to register functions using the babyagi framework
def register_function(*args, **kwargs):
    def wrapper(func):
        try:
            _func_instance.register_function(*args, **kwargs)(func)
            setattr(sys.modules[__name__], func.__name__, func)
            #print(f"Function '{func.__name__}' registered successfully.")
        except Exception as e:
            print(f"Error registering function '{func.__name__}': {e}")
            traceback.print_exc()
        return func
    return wrapper

# Function to load additional function packs
def load_functions(pack_name_or_path):
    #print(f"Attempting to load function pack: {pack_name_or_path}")
    if os.path.exists(pack_name_or_path):
        try:
            spec = importlib.util.spec_from_file_location("custom_pack", pack_name_or_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            #print(f"Custom pack loaded from {pack_name_or_path}")
        except Exception as e:
            #print(f"Failed to load custom pack from path '{pack_name_or_path}': {e}")
            traceback.print_exc()
    else:
        try:
            print(f"Assuming '{pack_name_or_path}' is an internal pack...")
            _func_instance.load_function_pack(pack_name_or_path)
            print(f"Internal pack '{pack_name_or_path}' loaded successfully.")
        except Exception as e:
            print(f"Failed to load internal pack '{pack_name_or_path}': {e}")
            traceback.print_exc()


def use_blueprints(app, dashboard_route='/dashboard'):
    """
    Registers the babyagi blueprints with the provided Flask app.

    Args:
        app (Flask): The Flask application instance.
        dashboard_route (str): The route prefix for the dashboard.
    """
    # Remove leading slash if present
    if dashboard_route.startswith('/'):
        dashboard_route = dashboard_route[1:]

    # Create blueprints
    dashboard_blueprint = create_dashboard(_func_instance, dashboard_route)
    api_blueprint = create_api_blueprint()

    # Register blueprints
    app.register_blueprint(dashboard_blueprint, url_prefix=f'/{dashboard_route}')
    app.register_blueprint(api_blueprint)  # Mounted at '/api' as defined in the blueprint

    # Store the dashboard route for use in templates
    app.config['DASHBOARD_ROUTE'] = dashboard_route

    # Ensure the Functionz instance is accessible in the request context
    @app.before_request
    def set_functionz():
        g.functionz = _func_instance
        g.dashboard_route = dashboard_route  # Optional, if needed globally


def __getattr__(name):
    """
    Dynamic attribute access for the babyagi module.
    If a function with the given name exists in the database,
    return a callable that executes the function via the executor.
    """
    try:
        if _func_instance.get_function(name):
            # Return a callable that executes the function via the executor
            return lambda *args, **kwargs: _func_instance.executor.execute(name, *args, **kwargs)
    except Exception as e:
        pass
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Auto-load default function packs when babyagi is imported
try:
    print("Attempting to load default function packs...")
    # Uncomment if needed
    _func_instance.load_function_pack('default/default_functions')
    _func_instance.load_function_pack('default/ai_functions')
    _func_instance.load_function_pack('default/os')
    _func_instance.load_function_pack('default/function_calling_chat')
except Exception as e:
    print(f"Error loading default function packs: {e}")
    traceback.print_exc()

print("babyagi/__init__.py loaded")
