from flask import Flask
from flask_cors import CORS
from .config_service import config_bp
from .simulation_service import simulation_bp
from .agent_service import agent_bp
from .analysis_service import analysis_bp
from .visualization_service import visualization_bp
from .content_service import content_bp
from .environment_service import environment_bp

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 启用CORS以支持跨域请求
    CORS(app)
    
    # 注册蓝图
    app.register_blueprint(config_bp, url_prefix='/api/simulation')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(agent_bp, url_prefix='/api/agents')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(visualization_bp, url_prefix='/api/visualization')
    app.register_blueprint(content_bp, url_prefix='/api/content')
    app.register_blueprint(environment_bp, url_prefix='/api')
    
    return app 