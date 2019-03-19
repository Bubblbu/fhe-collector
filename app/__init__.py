"""
.. module::
    :platform: Linux
    :synopsis: Web-app to collect facebook metrics.

.. moduleauthor:: Stefan Kasberger <mail@stefankasberger.at>
"""


import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_debugtoolbar import DebugToolbarExtension
import click


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    """Create application and loads settings."""
    app = Flask(__name__)

    ENVIRONMENT = os.getenv('ENV', default='development')
    TESTING = os.getenv('TESTING', default=False)
    print('* Updating App Mode to: ' + ENVIRONMENT)
    travis = os.getenv('TRAVIS', default=False)
    if not travis:
        print('* Loading User Settings.')
        app.config.from_pyfile(BASE_DIR+'/settings_user.py', silent=True)
    if ENVIRONMENT == 'development':
        print('* Loading Development Settings.')
        app.config.from_pyfile(BASE_DIR+'/settings_development.py', silent=True)
        app.config.from_object('settings_default.Development')
        if not travis:
            DebugToolbarExtension(app)
    elif ENVIRONMENT == 'production':
        print('* Loading Production Settings.')
        # order of settings loading: 1. settings file, 2. environment variable DATABASE_URL, 3. environment variable SQLALCHEMY_DATABASE_URI
        if not travis:
            app.config.from_pyfile(BASE_DIR+'/settings_production.py', silent=True)
        app.config.from_object('settings_default.Production')
    elif ENVIRONMENT == 'testing':
        print('* Loading Test Settings.')
        app.config['TESTING'] = True
        app.config.from_object('settings_default.Testing')
    if not travis:
        print('* Database: ' + app.config['SQLALCHEMY_DATABASE_URI'])
    db.init_app(app)
    migrate.init_app(app, db)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:

        # Logging (only production)
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/fhe.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Facebook Hidden Engagement')

    @app.cli.command()
    @click.option('--filename', default=None)
    def import_from_csv(filename):
        """Import csv file with doi's and OJS url's.

        Imports the DOI's and OJS url's from a csv file into the database.
        For development purposes there is a file with 100 entries you can use.
        With `--filename` you can pass the filename to the function.

        Args:
            filename: filename with path.
        """
        import pandas as pd
        from app.models import Doi
        from app.models import Import
        from app.models import Url
        import re

        try:
            df = pd.read_csv(filename, encoding='utf8', parse_dates=True)
            df = df.drop_duplicates(subset='doi')
            imp = Import('<file '+filename+'>', df.to_string())
            db.session.add(imp)
            db.session.commit()
        except:
            print('Error: CSV file for import not working.')

        if filename:
            num_rows = len(df.index)
            dois_added = 0
            dois_already_in = 0
            urls_added = 0
            urls_already_in = 0
            # Loop over each entry (row)
            for index, row in df.iloc[:num_rows].iterrows():
                doi = row['doi']
                # validate doi
                patterns = [
                    r"^10.\d{4,9}/[-._;()/:A-Z0-9]+$",
                    r"^10.1002/[^\s]+$",
                    r"^10.\d{4}/\d+-\d+X?(\d+)\d+<[\d\w]+:[\d\w]*>\d+.\d+.\w+;\d$",
                    r"^10.1021/\w\w\d+$",
                    r"^10.1207\/[\w\d]+\&\d+_\d+$"
                ]
                is_valid = False
                for pat in patterns:
                    if re.match(pat, doi, re.IGNORECASE):
                        is_valid = True
                if is_valid:
                    url = row['url']
                    # store doi
                    result_doi = Doi.query.filter_by(doi=doi).first()
                    if result_doi is None:
                        doi = Doi(
                            doi=doi,
                            import_id=imp.id
                        )
                        db.session.add(doi)
                        dois_added += 1
                    else:
                        dois_already_in += 1
                    # store url
                    result_url = Url.query.filter_by(url=url).first()
                    if result_url is None:
                        url = Url(
                            url=url,
                            doi=str(doi.doi),
                            url_type='ojs'
                        )
                        db.session.add(url)
                        urls_added += 1
                    else:
                        urls_already_in += 1
            db.session.commit()
            print(dois_added, 'doi\'s added to database.')
            print(dois_already_in, 'doi\'s already in database.')
            print(urls_added, 'url\'s added to database.')
            print(urls_already_in, 'url\'s already in database.')

    @app.cli.command()
    def delete_all_dois():
        """Delete all doi entries."""
        from app.models import Doi
        result = Doi.query.all()
        dois_deleted = 0
        for row in result:
            db.session.delete(row)
            dois_deleted += 1

        db.session.commit()
        print(dois_deleted, 'doi\'s deleted from database.')

    @app.cli.command()
    def create_doi_urls():
        """Create URL's from the identifier."""
        from app.models import Doi
        from app.models import Url
        import requests
        import urllib.parse

        urls_new_added = 0
        urls_new_already_in = 0
        urls_old_added = 0
        urls_old_already_in = 0
        urls_landing_page_added = 0
        urls_landing_page_already_in = 0
        result_doi = Doi.query.all()

        for row in result_doi:
            doi_url_encoded = urllib.parse.quote(row.doi)
            # create http url
            url = 'https://doi.org/{0}'.format(doi_url_encoded)
            result_url = Url.query.filter_by(url=url).first()
            if result_url is None:
                url = Url(
                    url=url,
                    doi=row.doi,
                    url_type='doi_old'
                )
                db.session.add(url)
                urls_new_added += 1
            else:
                urls_new_already_in += 1
            # create http url
            url = 'http://dx.doi.org/{0}'.format(doi_url_encoded)
            result_url = Url.query.filter_by(url=url).first()
            if result_url is None:
                url = Url(
                    url=url,
                    doi=row.doi,
                    url_type='doi_new'
                )
                db.session.add(url)
                urls_old_added += 1
            else:
                urls_old_already_in += 1
            # create landing page url
            url = 'https://doi.org/{0}'.format(doi_url_encoded)
            resp = requests.get(url, allow_redirects=True)
            url_landing_page = resp.url
            result_url = Url.query.filter_by(url=url_landing_page).first()
            if result_url is None:
                url = Url(
                    url=url_landing_page,
                    doi=row.doi,
                    url_type='doi_landing_page'
                )
                db.session.add(url)
                urls_landing_page_added += 1
            else:
                urls_landing_page_already_in += 1
        db.session.commit()
        print(urls_new_added, 'doi new url\'s added to database.')
        print(urls_new_already_in, 'doi new url\'s already in database.')
        print(urls_old_added, 'doi old url\'s added to database.')
        print(urls_old_already_in, 'doi old url\'s already in database.')
        print(urls_landing_page_added,
              'doi landing page url\'s added to database.')
        print(urls_landing_page_already_in,
              'doi landing page url\'s already in database.')

    @app.cli.command()
    def create_ncbi_urls():
        """Create NCBI URL's from the identifier."""
        from app.models import Doi
        from app.models import Url
        import urllib.parse
        import requests

        urls_pm_added = 0
        urls_pm_already_in = 0
        urls_pmc_added = 0
        urls_pmc_already_in = 0

        result_doi = Doi.query.all()

        for row in result_doi:
            # send request to NCBI API
            # https://www.ncbi.nlm.nih.gov/pmc/tools/id-converter-api/
            # TODO: allows up to 200 ids sent at the same time
            doi_url_encoded = urllib.parse.quote(row.doi)
            url = ' https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={0}'.format(doi_url_encoded)
            resp = requests.get(url, params={
                'tool': NCBI_TOOL, 'email': NCBI_EMAIL,
                'idtype': 'doi', 'versions': 'no', 'format': 'json'})
            resp = resp.json()
            if 'records' in resp:
                # create PMC url
                if 'pmcid' in resp['records']:
                    url = 'https://ncbi.nlm.nih.gov/pmc/articles/PMC{0}/'.format(resp['records']['pmcid'])
                    result_url = Url.query.filter_by(url=url).first()
                    if result_url is None:
                        url = Url(
                            url=url,
                            doi=row.doi,
                            url_type='pmc'
                        )
                        db.session.add(url)
                        urls_pmc_added += 1
                    else:
                        urls_pmc_already_in += 1

                # create PM url
                if 'pmid' in resp['records']:
                    url = 'https://www.ncbi.nlm.nih.gov/pubmed/{0}'.format(resp['records']['pmid'])
                    result_url = Url.query.filter_by(url=url).first()
                    if result_url is None:
                        url = Url(
                            url=url,
                            doi=row.doi,
                            url_type='pm'
                        )
                        db.session.add(url)
                        urls_pm_added += 1
                    else:
                        urls_pm_already_in += 1

        print(urls_pm_added, 'PM url\'s added to database.')
        print(urls_pm_already_in, 'PM url\'s already in database.')
        print(urls_pmc_added, 'PMC url\'s added to database.')
        print(urls_pmc_already_in, 'PMC url\'s already in database.')

    @app.cli.command()
    def delete_all_urls():
        """Delete all url entries."""
        from app.models import Url
        result = Url.query.all()
        urls_deleted = 0
        for row in result:
            db.session.delete(row)
            urls_deleted += 1

        db.session.commit()
        print(urls_deleted, 'url\'s deleted from database.')

    @app.cli.command()
    @click.option('--filename', default=None)
    def fb_request(filename):
        """Send facebook requests of URL's.

        urls: filename of json file with array of urls.
        """
        # FB_APP_ID = app.config['FB_APP_ID']
        FB_APP_SECRET = app.config['FB_APP_SECRET']
        # BATCH_SIZE = app.config['BATCH_SIZE']

        if not urls:
            from app.models import Url
            result = Url.query.all()
        else:
            try:
                import json
                with open(urls) as f:
                    data = json.load(f)
            except:
                print("URL's file not working.")

        # batches = range(0, len(urls), BATCH_SIZE)

        import facebook
        import urllib

        graph = facebook.GraphAPI(access_token=FB_APP_SECRET, version='2.12')

        print(result[0].url)
        for row in result:
            try:
                fb_response = graph.get_object(
                id=urllib.parse.quote_plus(row.url),
                    fields="engagement, og_object"
                )
                if 'og_object' in fb_response:
                    og_object = fb_response['og_object']
                    print('og_object', og_object)
                if 'engagement' in fb_response:
                    og_engagement = fb_response['engagement']
                    print('og_engagement', og_engagement)
            except Exception as e:
                og_error = e
                print('og_error:', og_error)


    return app


from app import models
