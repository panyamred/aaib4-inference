import config
from anuvaad_auditor.loghandler import log_info
from cron_job import NMTcronjob
from config import MODULE_CONTEXT
import threading
from flask import Flask, jsonify, request
from flask.blueprints import Blueprint
from flask_cors import CORS
import routes
from cron_job import NMTcronjob, TranslationScheduler

nmt_proxy_app = Flask(__name__)

if config.ENABLE_CORS:
    cors = CORS(nmt_proxy_app, resources={r"/api/*": {"origins": "*"}})

for blueprint in vars(routes).values():
    if isinstance(blueprint, Blueprint):
        nmt_proxy_app.register_blueprint(blueprint, url_prefix=config.API_URL_PREFIX)
if __name__ == "__main__":
    if not config.internal_cron_enabled:
        log_info('starting cronjob', MODULE_CONTEXT)
        wfm_jm_thread = NMTcronjob(threading.Event())
        wfm_jm_thread.start()
    nmt_proxy_app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, threaded=True)