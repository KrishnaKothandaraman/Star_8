from flask_cors import CORS
from flask import Flask
import services.database_management.app.controller.addorders_controller as addorders_controller
import services.database_management.app.controller.orders_database_controller as db_controller

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.add_url_rule('/swd-add-order', methods=["POST"], view_func=addorders_controller.swdAddOrder)
app.add_url_rule('/update-googlesheet', methods=["POST"], view_func=db_controller.updateGoogleSheet)


def create_api_app():
    return app


if __name__ == '__main__':
    # **** if you run locally without dockerfile, uncomment the below lines *****
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "../helloar-analytics-d4298ceae005.json")
    # os.environ["SENDGRID_API_KEY"] = "<enter api key here>"
    app.run(port=5001)
