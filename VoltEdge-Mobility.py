import logging
import os
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from dotenv import load_dotenv
from api.routes import api

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config["SWAGGER"] = {"title": "VoltEdge Monitoring API", "uiversion": 3}
    Swagger(app)
    app.register_blueprint(api)
    logger.info("VoltEdge Monitoring API startet")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", debug=False, port=5001)
