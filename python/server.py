from flask import Flask
from flask import render_template
import templates


def main_runner():
    app = Flask(__name__)

    @app.route('/')
    @app.route('/index')
    def index():
        name = 'alex'
        # return 'spotify dance app coming soon'
        return render_template('index.html', title='welcome', username=name)


    app.run(host='0.0.0.0', port=81)

if __name__ == '__main__':
    main_runner()
