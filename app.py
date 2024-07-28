import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv
from heyoo import WhatsApp
from flask import Flask, request, make_response

load_dotenv()
# Initialize Flask App
app = Flask(__name__)
# Initialize messenger functionality
messenger = WhatsApp(os.getenv("WHATSAPP_TOKEN"),
                     os.getenv("PHONE_ID"))
# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

genai.configure(
    api_key=os.environ['API_KEY']
)


def main(chat):
    def respond(user_input):
        response = chat.send_message(user_input)
        return response

    @app.route("/", methods=["GET", "POST"])
    def hook():
        if request.method == "GET":
            if request.args.get("hub.verify_token") == os.environ['VERIFY_TOKEN']:
                logging.info("Verified webhook")
                response = make_response(request.args.get("hub.challenge"), 200)
                response.mimetype = "text/plain"
                return response
            logging.error("Webhook Verification failed")
            return "Invalid verification token"

        data = request.get_json()
        logging.info("Received data: %s", data)
        changed_field = messenger.changed_field(data)

        if changed_field == "messages":
            new_message = messenger.get_mobile(data)
            if new_message:
                mobile = messenger.get_mobile(data)
                message_type = messenger.get_message_type(data)
                if message_type == "text":
                    message = messenger.get_message(data)
                    response = respond(message)
                    logging.info("\nResponse: %s\n", response)
                    messenger.send_message(message=f"{response}", recipient_id=mobile)
                else:
                    messenger.send_message(message="Please send me text messages", recipient_id=mobile)
        return "ok"


if __name__ == "__main__":
    model = genai.GenerativeModel(
        "gemini-1.5-pro-latest"
    )
    chat = model.start_chat()
    main(chat=chat)
    app.run(port=5000, debug=False)
