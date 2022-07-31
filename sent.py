from logging import raiseExceptions
import os
import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)
import controller

import pdfkit
from time import time, sleep
from sentinelsat import SentinelAPI, geojson_to_wkt
import base64

db_object = {
      'email': 'baloolamu@gmail.com',
      'password': 'baloola',
      'products_bucket_list': [],
      # 'last_product_date': datetime.datetime.now(),
      'last_product_date': 'NOW-7DAYS',
      'polygon': {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [[[34.41673278808594, 13.260664834527315], [34.751129150390625, 13.260664834527315], [34.751129150390625, 13.525181420242227], [34.41673278808594, 13.525181420242227], [34.41673278808594, 13.260664834527315]]]}}]}
    }


def render_report(items):
    api = establish_connection('baloola', 'rastaman')
    products_items = ''
    items_content = ''
    main_template = f"""
    <h1 style="color: #5e9ca0;">Weekly Report</h1>
    <h2 style="color: #2e6c80;">You have {len(items)} products this week :)</h2>
    <p>There is {len(items)} available products within the pre-specified area for you to download. <br />Below you have your report about these products.&nbsp;</p>
    <h2 style="color: #2e6c80;">Products this week:</h2>
    """

    for key, item in items:
        api.download_quicklook(item['uuid'])
        file_path = "./%s.jpeg" % item["identifier"]
        encoded = base64.b64encode(open(file_path, "rb").read()).decode('ascii')
        image_data = f'data:image/jpeg;base64,{encoded}'
        products_items += f'<li style="clear: both;">{item["identifier"]}</li>'
        items_content += f"""
          <p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p>
          <h2 style="color: #2e6c80;">{item["title"]} :</h2>
          <table class="editorDemoTable" style="height: 162px;">
          <thead>
          <tr style="height: 18px;">
          <td style="height: 18px; width: 137.766px;">Identifier</td>
          <td style="height: 18px; width: 140.672px;">{item["title"]}</td>
          </tr>
          </thead>
          <tbody>
          <tr style="height: 18px;">
          <td style="height: 18px; width: 137.766px;">processinglevel</td>
          <td style="height: 18px; width: 140.672px;">
          <div>
          <div>{item["processinglevel"]}</div>
          </div>
          </td>
          </tr>
          <tr style="height: 18px;">
          <td style="height: 18px; width: 137.766px;">producttype</td>
          <td style="height: 18px; width: 140.672px;">{item["producttype"]}</td>
          </tr>
          <tr style="height: 18px;">
          <td style="height: 18px; width: 137.766px;">size</td>
          <td style="height: 18px; width: 140.672px;">{item["size"]}</td>
          </tr>
          <tr style="height: 18px;">
          <td style="width: 137.766px; height: 18px;">format</td>
          <td style="width: 140.672px; height: 18px;">{item["format"]}</td>
          </tr>
          <tr style="height: 18px;">
          <td style="width: 137.766px; height: 18px;">cloudcoverpercentage</td>
          <td style="width: 140.672px; height: 18px;">{item["cloudcoverpercentage"]}</td>
          </tr>
          </tbody>
          </table>
          <p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p>
          <h2 style="color: #2e6c80;">Preview Image :</h2>
          <p><img style="display: block; -webkit-user-select: none; margin: auto; background-color: hsl(0, 0%, 90%); transition: background-color 300ms;" src="{image_data}" /></p>
        """
        os.remove(file_path)

    products_list = f'<ol style="list-style: none; font-size: 14px; line-height: 32px; font-weight: bold;">{products_items}</ol>'
    try:

        with open("temp_result.html", "w") as f:
            f.write(main_template + products_list + items_content)
        pdfkit.from_file('temp_result.html', 'output.pdf')

    except Exception as e:
        print(e.message)

    return main_template + products_list


def send_email_notification(sender_email, user, password, values):
    Controller = controller.Controller()

    content = render_report(values)
    if content:

        message = Mail(
            from_email=sender_email,
            to_emails=user['email'],
            subject='Test report',
            html_content=content)

        try:
            with open('output.pdf', 'rb') as f:
                data = f.read()
                f.close()
            encoded_file = base64.b64encode(data).decode()

            attachedFile = Attachment(
                FileContent(encoded_file),
                FileName('attachment.pdf'),
                FileType('application/pdf'),
                Disposition('attachment')
            )
            message.attachment = attachedFile
            # sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            sg = SendGridAPIClient(password)

            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
            Controller.update_history(user, values)
            os.remove('temp_result.html')
            os.remove('output.pdf')

        except Exception as e:
            print(e)


def establish_connection(username, password):
    api = SentinelAPI(username, password, 'https://apihub.copernicus.eu/apihub')
    return api


def listen_for_Update():
    print(1)


def look_for(identifier, user):

    # TODO: look for the product inside the mongoDB
    Controller = controller.Controller()
    # user should be an object that contains {email, password,.....etc}
    Controller.login(user)

    user_object = Controller.get_user_by_email(user['email'])
    products_list = user_object['products_bucket_list'] if hasattr(user_object, 'products_bucket_list') else []
    if identifier not in products_list:
        return True


def listener():
    while True:
        sleep(432000 - time() % 1)
        print("k")


footprint = geojson_to_wkt(db_object['polygon'])
api = establish_connection('baloola', 'rastaman')
products = api.query(footprint,
                     date=(db_object['last_product_date'], "NOW"),
                     platformname='Sentinel-2',
                     cloudcoverpercentage=(0, 30))
values = []

for key, value in products.items():
    if not look_for(value['identifier'], db_object):
        values.append(value['identifier'])
if len(values) > 0:
    send_email_notification('baloola-mu@hotmail.com', db_object, '<sendgrid_key>', products.items())
else:
    print("all up to date!")
# baloola.strangled.net