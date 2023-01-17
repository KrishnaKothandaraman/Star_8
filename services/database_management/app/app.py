import os

os.environ["remote-check-api-key"] = "hu685pkl-0lr1-7jx5-r3be-yzxjaqnrzfm9"
os.environ["appsheet-accesskey"] = "V2-mwTj5-nvH7J-6sv08-6yfrG-OSs2H-jQEOe-sWbY9-mZ5ha"
os.environ["rf-token"] = "Plain e01e77cd-899f-4964-a44f-ec603ab62d17"
os.environ["bm-token"] = "YmFjazJsaWZlcHJvZHVjdHNAb3V0bG9vay5jb206ODMyNzhydWV3ZmI3MzpmbmopKE52OCY4"
os.environ["swd-shopkey"] = "9q7qDKnCX+XHtdAka96OTm3SEfyW/0gw/5HYQJClmtBet4grGl1/W5xuGxmuSGM2B/R5OADgmn+z" \
                            "+4GnkBtRapMqxRaOcpfqpMeLPDO4qGAlNmVCzXyFNbYHPA4ORmRHBo5pnRKmVtamFPjJh3BLdaSsYCD6IxckVJb8f6N10Kc= "
os.environ["swd-shopid"] = "11025"

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
