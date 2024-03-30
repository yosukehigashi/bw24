from flask import Flask

app = Flask(__name__)

@app.route('/venue', methods=['GET'])
def venue():
    return {'dummy_id': 1}


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
