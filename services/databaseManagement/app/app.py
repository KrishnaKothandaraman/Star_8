import sys
import os

# add root to paths
sys.path.append(os.path.join(""))

import json
import traceback
from flask_cors import CORS, cross_origin
import googleapiclient.errors
from flask import Flask, request, make_response, jsonify, send_file
import requests
from core.google_services.googleSheetsService import GoogleSheetsService

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

GOOGLE_DOCS_MIMETYPE = "application/vnd.google-apps.document"
GOOGLE_SHEETS_MIMETYPE = "application/vnd.google-apps.spreadsheet"


@app.route('/update-bm-googlesheet', methods=['POST'])
def updateBMGoogleSheet():
    try:
        service = GoogleSheetsService()
    except Exception as e:
        print(traceback.print_exc())
        return make_response(jsonify({"type": "fail",
                                      "message": "Failed to open Google Sheets. Check server logs for more info"
                                      }),
                             400)

    return make_response(jsonify({"type": "success",
                                  "message": f"Hello world!"
                                  }),
                         200)
    try:
        body = request.get_json()
        if not body:
            return make_response(jsonify({"type": "fail",
                                          "message": "Invalid Json"
                                          }),
                                 400)
    except ValueError:
        return make_response(jsonify({"type": "fail",
                                      "message": "Expected content type application/json"
                                      }),
                             400)

    try:
        templateFileId = body["template_file_id"]
        optionalParameters = body["optional_parameters"]
        template_type = body["type"] if "type" in body else "docs"

        if template_type != "sheets" and template_type != "docs":
            return make_response(jsonify({"type": "fail",
                                          "message": f"Unsupported type, expected docs/sheets"
                                          }),
                                 400)
    except KeyError as e:
        return make_response(jsonify({"type": "fail",
                                      "message": f"Missing Parameter {e.args[0]}"
                                      }),
                             400)

    try:
        orders = body["order"]
    except:
        orders = None

    try:
        if template_type == "docs":
            service = GoogleDocsService()

        else:
            service = GoogleSheetsService()

        templateCopyID = service.generateCopyFromTemplate(templateFileId=templateFileId)

        if incompatibleFileTypeProvided(templateFileId, template_type, service):
            return make_response(jsonify({"type": "fail",
                                          "message": f"Incompatible type provided for template_file_id"
                                          }),
                                 400)

        # replaces all optional parameters
        replaceTextRequests = service.makeReplaceTextRequests(data=optionalParameters)

        service.executeBatchRequest(requests=replaceTextRequests, documentId=templateCopyID)

        if orders != None:
            # creates table
            service.createTableFromOrders(orders=orders, documentID=templateCopyID)

        # gets pdf binary
        fileBytesIO = service.downloadDocument(fileId=templateCopyID)

        response = make_response(fileBytesIO)

        if template_type == "docs":
            response.headers.set('Content-Type', 'application/pdf')
            response.headers.set(
                'Content-Disposition', 'attachment', filename="invoice.pdf")

        else:
            response.headers.set('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response.headers.set(
                'Content-Disposition', 'attachment', filename="invoice.xlsx")

        return response
    except FileNotFoundError:
        traceback.print_exc()
        return make_response(jsonify({"type": "fail",
                                      "message": "Internal server error"
                                      }),
                             500)
    except googleapiclient.errors.HttpError as e:
        traceback.print_exc()
        return make_response(jsonify({"type": "fail",
                                      "message": "Invalid template ID",
                                      }),
                             400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({"type": "fail",
                                      "message": "Internal Server Error",
                                      }),
                             500)


if __name__ == '__main__':
    # **** if you run locally without dockerfile, uncomment the below lines *****
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "../helloar-analytics-d4298ceae005.json")
    # os.environ["SENDGRID_API_KEY"] = "<enter api key here>"
    app.run(port=5001)
