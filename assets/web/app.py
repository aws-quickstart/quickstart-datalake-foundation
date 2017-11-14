import argparse
import os

import multiprocessing
from configparser import ConfigParser

import functools

import logging

import sys

from flask import (
    Flask,
    render_template,
    request,
    session,
    jsonify,
    abort
)
from flask import redirect
from flask import url_for

from analysis.generator import generate_data_to_kinesis
from analysis.kinesis import create_kinesis_apps
from analysis.glue import run_aws_glue_crawler
from analysis.transformations import (
    run_redshift_analysis,
    publish_analysis_results,
    create_and_load_curated_datasets
)
from analysis.learn_more import learn_more
from analysis.exceptions import QuickstartException, handle_quickstart_exception
from root import PROJECT_DIR


app = Flask(
    __name__,
    template_folder=os.path.join(PROJECT_DIR, 'web/templates'),
    static_folder=os.path.join(PROJECT_DIR, 'web/static')
)

logger = logging.getLogger(__name__)


def login_required(fun):

    @functools.wraps(fun)
    def wrapper(*args, **kwargs):
        if session.get('logged_in') is None:
            abort(401)
        return fun(*args, **kwargs)

    return wrapper


def make_session_state():
    return jsonify({
        'current_step': session['current_step'],
        'completed_step': session['completed_step'],
        'seen_step': session['seen_step']
    })


def mark_step_as_done(step):

    def outer(fun):
        @functools.wraps(fun)
        def inner(*args, **kwargs):
            fun(*args, **kwargs)
            if session['completed_step'] < step:
                session['completed_step'] = step
            return make_session_state()

        return inner

    return outer


@app.errorhandler(QuickstartException)
def quickstart_exception_errorhandler(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == app.config['webapp_username'] and \
                    request.form['password'] == app.config['webapp_password']:
        session['logged_in'] = True
        session['current_step'] = 1
        session['completed_step'] = 1
        session['seen_step'] = 1
        return redirect(url_for('wizard'))
    else:
        return render_template('login.html')


@app.route('/step', methods=['GET', 'POST'])
@login_required
def step():
    if request.method == 'POST':
        data = request.get_json(force=True)
        if 'step' in data:
            session['current_step'] = data['step']
            session['seen_step'] = max(session['seen_step'], data['step'])
    return make_session_state()


@app.route('/')
def home():
    if session.get('logged_in') is None:
        return render_template('login.html')
    return redirect(url_for('wizard'))


@app.route('/wizard')
def wizard():
    if session.get('logged_in') is None:
        return render_template('login.html')
    return render_template(
        'wizard.html',
        kibana_url=app.config['kibana_url'],
        region_name=app.config['region_name'],
        published_bucket_name=app.config['published_bucket_name'],
        curated_bucket_name=app.config['curated_bucket_name'],
        submissions_bucket_name=app.config['submissions_bucket_name'],
        curated_datasets_database_name=app.config['curated_datasets_database_name'],
        curated_datasets_crawler_name=app.config['curated_datasets_crawler_name'],
        curated_datasets_job_name=app.config['curated_datasets_job_name']
    )


@app.route('/create_curated_datasets', methods=['POST'])
@handle_quickstart_exception("Error occured while creating curated datasets")
@login_required
@mark_step_as_done(step=2)
def create_curated_datasets():
    create_and_load_curated_datasets(app.config)


@app.route('/configure_kinesis', methods=['POST'])
@handle_quickstart_exception("Error occured while creating Kinesis applications")
@login_required
@mark_step_as_done(step=3)
def create_kinesis_applications_and_start_stream():
    create_kinesis_apps(app.config)
    process = multiprocessing.Process(target=generate_data_to_kinesis, args=(app.config,))
    process.start()


@app.route('/run_glue_crawler', methods=['POST'])
@handle_quickstart_exception("Error occured while using AWS Glue service")
@login_required
@mark_step_as_done(step=4)
def run_glue_crawler():
    run_aws_glue_crawler(app.config)


@app.route('/elastic_search', methods=['POST'])
@login_required
@mark_step_as_done(step=5)
def elastic_search():
    pass


@app.route('/run_spectrum_analytics', methods=['POST'])
@handle_quickstart_exception("Error running analytics with Spectrum")
@login_required
@mark_step_as_done(step=6)
def run_spectrum_analytics():
    run_redshift_analysis(app.config)


@app.route('/amazon_athena', methods=['POST'])
@handle_quickstart_exception("Error occured while configuring Athena")
@login_required
@mark_step_as_done(step=7)
def amazon_athena():
    pass


@app.route('/publish_datasets', methods=['POST'])
@handle_quickstart_exception("Error occured while publishing data")
@login_required
@mark_step_as_done(step=8)
def publish_datasets():
    publish_analysis_results(app.config)


@app.route('/learn_more', methods=['POST'])
@handle_quickstart_exception("Error occured while sending form")
@login_required
@mark_step_as_done(step=9)
def learn_more_form():
    learn_more(app.config, request.form)


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html',
                           curated_datasets_database_name=app.config['curated_datasets_database_name'])


def parse_command_line_args():
    parser = argparse.ArgumentParser(description='Quick start App')
    parser.add_argument('--config', required=True, help='Configuration')
    return parser.parse_args()


def read_config(config_path):
    parser = ConfigParser()
    parser.read(config_path)
    config = {}
    for section in parser.sections():
        for (config_key, config_value) in parser.items(section):
            config[config_key] = config_value
    return config


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    args = parse_command_line_args()
    config = read_config(args.config)
    app.secret_key = os.urandom(47)
    app.config.update(config)
    app.run(host='0.0.0.0', port=int(config['port']), threaded=True)
