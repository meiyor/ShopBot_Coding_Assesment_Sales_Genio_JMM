"""
This app.py code contains the functions for runing and setting app
the ShopBot API and realease it in ngro or AWS.
Please follow the serverless deployment to set this up in AWS or
the ngrok instructions to put it there.
Add the permissions defined in the READme if you want to configure it
"""
# import Flask dependencies

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from bing_image_downloader import downloader

# import the SQLAlchemy and database support modules
from models_database import db, ShopData, ShopData_Product

# import openai and waiting modules
import openai
from openai import OpenAI
from waiting import wait

# import this for the ShopAPI purposes
import json
import os
import random
import datetime
import string
import shutil
import glob
# import re

# remove warning here
import warnings
warnings.filterwarnings(
    action='ignore',
    message='Could not obtain multiprocessing lock')

# Initialize the OpenAI API client
openai.api_key = os.environ['openAI_key']

# set the openAI client for this specific test
client = OpenAI(api_key=os.environ['openAI_key'])

# define the app object
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://postgres:DataBase@localhost:5432/Shopdb"

# use this configuration for docker and for AWS only
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://postgres:DataBase@backend_chatbot:5432/apidb"
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://' + \
#    user_name + ':' + password + '@' + rds_host + ':' + rds_port + '/' + db_name

# always use this flag
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize database initially - don't call it from main
db.init_app(app)
with app.app_context():
    db.create_all()

CORS(app)


def run_handler_poll(run=None):
    """
    This function Polls the status of the GPT assistant run until it is either completed, requires action,
    fails, or expires.
    If the run fails or expires, it raises an exception with an error message. If the run
    requires action, it prepares and returns tool output information. If the run completes,
    it returns None.

    :param run : object, optional
     An GPT assistant's run object that represents a run object with 'status' attribute,
     which could be "completed", "failed", "expired", or "requires_action". If 'status'
     is "requires_action", it should also have a `required_action` attribute to handle
     tool outputs.

    :return: tuple
     If the GPT run requires action, returns a tuple containing:
     - tool_output (list of dict): A list of dictionaries with tool output information,
       each containing:
     - tool_call_id (str): The ID of the tool call.
     - output (str): The output associated with the tool call, initialized as an empty string.
     - value_return (object): The `submit_tool_outputs` object from the run's required action.

        If the run is completed, returns '(None, None)'.
    """

    status = run.status
    while status != "completed":
        if status == 'failed':
            raise Exception(f"Run failed with error: {run.last_error}")
        if status == 'expired':
            raise Exception("Run expired.")
        if status == 'requires_action':
            tool_output = []
            id = run.required_action.submit_tool_outputs.tool_calls[0].id
            value_return = run.required_action.submit_tool_outputs
            # make the json object for the tool to be returned
            tool_output.append({
                "tool_call_id": id,
                "output": ""
            })

            return tool_output, value_return

        return None, None

# define the functions associated with the other GPT tool functions


def checkStock(stock_value=None, mock_products=None):
    """
    This functiomn Determines stock availability of a specified product based on GPT tool
    call information and mock product data.

    This function inspects the GPT model's tool call response to determine if a stock check
    is required. If the model response provides a 'checkValue', it validates against the mock
    product list. Returns a stock availability message and the stock status.

    :param stock_value (Optional): A model response object that may contain tool calls, including
    the product's stock check information.
    :param mock_products (Optional): A JSON string of a list of dictionaries, where each dictionary
    ontains product information such as `product_name` and 'stock_avail'.

    :return:  Tuple[str, str]: A tuple containing:
    - stock_availability_string: A formatted HTML string indicating stock availability status.
    - tool_stock_value: A string representing the stock status ('true' if available, 'false' if not).
    """
    # determine if the response from the model includes a tool call.
    tool_stock = stock_value.tool_calls

    if tool_stock:
        # If true the model will return the name of the tool / function to call
        # and the argument(s)
        tool_stock[0].id
        tool_stock[0].function.name
        tool_stock_value = json.loads(
            tool_stock[0].function.arguments)['checkValue']

    # double validation of the GPT ack
    if str(tool_stock_value).lower() != 'true' and str(
            tool_stock_value).lower() != 'false':
        # read the values
        data = json.loads(mock_products)

        for index_val_data in range(0, len(data)):
            if str(tool_stock_value).lower() == str(
                    data[index_val_data]['product_name']).lower():
                tool_stock_value = str(data[index_val_data]['stock_avail'])
                break

    if str(tool_stock_value).lower() == 'true':
        stock_availability_string = "<b>** This product is on stock! **</b><br>"
    else:
        stock_availability_string = "<b>** This product is out of stock! **</b><br>"

    return stock_availability_string, tool_stock_value

# define the functions associated with the description and GPT tools


def getInformation(info_values=None):
    """
    This function retrieves product information based on GPT tool call data with the function getInformation.
    This function also examines the model's response to check if it includes a tool call containing
    product information, such as price and description. If found, it extracts these details
    and formats them into an HTML string.

    :params info_values (Optional): An object representing the model's response that may contain
    tool calls, which include details like product price and description.

    :return: Tuple[str, str, str]: A tuple containing:
    - info_string: A formatted HTML string displaying the product price and description.
    - tool_info_price: A string representing the product price.
    - tool_info_description: A string representing the product description.
    """

    # determine if the response from the model includes a tool call.
    tool_info = info_values.tool_calls

    if tool_info:
        # If true the model will return the name of the tool / function to call
        # and the argument(s)
        tool_info[0].id
        tool_info[0].function.name
        tool_info_price = json.loads(tool_info[0].function.arguments)['price']
        tool_info_description = json.loads(
            tool_info[0].function.arguments)['description_val']

    info_string = "<b>Price:</b> " + tool_info_price + " USD <br>" + \
        "<b>Description:</b> " + tool_info_description + "<br>"

    return info_string, tool_info_price, tool_info_description

# define the functions that extract the product_name values in the catalog


def extract_product_names_values(json_values=None):
    """
    This function Extracts product_name values from the Mock catalog in JSON format and formats them
    as a string for display.

    This function also parses a JSON string of product data, extracts each product name, and creates
    a formatted HTML string for display. Also returns a list of product names.

    :params json_values (Optional): A JSON string representing a list of product dictionaries,
    where each dictionary contains a 'product_name' key.

    :return Tuple[str, List[str]]: A tuple containing:
    - string_value: A formatted HTML string with product names for display.
    - product_names: A list of product names extracted from the JSON data.
    """

    data = json.loads(json_values)

    product_names = []
    for index_val_data in range(0, len(data)):
        product_names.append(str(data[index_val_data]['product_name']))

    string_value = ""
    for index_val in range(0, len(product_names)):
        string_value = string_value + '<b>-' + \
            product_names[index_val] + '</b><br>'
    return string_value, product_names


def getProductInfo(
        productName=None,
        mock_products=None,
        text=None,
        tools=None,
        thread=None,
        assistant=None):
    """
    This function retrieves information about a specific product_name from the Mock catalog,
    including availability, price, description, and associated image, based on a product_name
    or a variable user query input.

    This function first processes a list of product names from the Mock catalog. If the specified
    'productName' is invalid or missing. Subsequently, it prompts the user to specify a valid
    product name or generates a response based on the input. When a valid 'productName' is provided,
    the function uses GPT tool calls to fetch additional details about the query, such as, stock availability,
    price, and description, and attempts to download an image of the product.

    :params productName (Optional[str]): The name of the product to query. If 'None' or invalid,
    the function prompts for clarification.
    :params mock_products (Optional[str]): A JSON string representing a catalog of products, where
    each product includes attributes like 'product_name', 'price', and 'description'.
    :params text (Optional[str]): User input text for querying; used to guide the function if 'productName' is
    not specified.
    :params tools (Optional): Tools or functions available for GPT model calls, including
     getInformation' and 'checkStock' functions.
    :params thread (Optional): This is the Assistant Thread parsed from the precict function to do the
     specific query. Inside this function the thread is always the same for each chatbot session.
    :params assistant (Optional): This is the Assistant object parsed from the precict function to do the
     specific query. Inside this function the thread is always the same for each chatbot session and the assistant
     is always the same for each chatbot session as well.

    :returns: Tuple[str, str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
    A tuple containing:
    - 'response_text' (str): A formatted HTML string with product information or a prompt for clarification.
    - 'img_path' (str): The file path of the downloaded product image (or a placeholder path if unavailable).
    - 'product_query' (bool): Indicates whether the product query was successful ('True' for success, 'False' otherwise).
    - 'productName' (Optional[str]): The name of the queried product if valid.
    - 'price' (Optional[str]): The product's price, if available.
    - 'description' (Optional[str]): The product's description, if available.
    - 'stock_avail' (Optional[str]): The product's stock availability status, if available.
    """

    # process the value in the json catalog first and separate the product
    # names
    product_names_values, product_names_strings = extract_product_names_values(
        json_values=mock_products)

    # check if the response is null or the same output so the query to a
    # particular product is not done yet
    if productName == 'null' or productName == text or productName is None or not (
            productName in ' '.join(product_names_strings)):

        if 'product' in text.lower() or 'products' in text.lower():
            response_text = 'Please, can you specifiy what product you want to query for..<br><br> These are the products we have in catalog: <br>' + product_names_values
        else:

            # create the messages here to the thread
            message_product = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=text
            )

            # define a new run
            run_product = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
            )

            wait(
                lambda: run_product.status == 'completed',
                timeout_seconds=60,
                waiting_for="product run for being completed")

            # process message payload
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            response_specific = messages.data[0].content[0].text.value

            response_text = response_specific + '<br><br> ' + \
                'These are the products we have in catalog: <br>' + product_names_values

        product_query = False

        img_path = '../static/images/gray.jpg'

        return response_text, img_path, product_query, productName, None, None, None

    # go to the particular selected product and do the specific query
    else:

        # create the json message to the thread for an specific query
        message_json = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="The JSON input catalog is: " + mock_products
        )

        # create the user sorted message to the thread for an specific query
        message_user = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="user: " + productName
        )

        """
          ** Here you call the getInformation function run **
        """
        # create the run here and specify the tool_choice to make it easier and
        # more efficient
        run_info = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Give priority to this client! Return the tools that are activated by the user message",
            tool_choice={
                "type": "function",
                "function": {
                    "name": "getInformation"}})

        # evaluate the getInformation function here
        # parsing the tool output here after the requied action is processed
        tool_outputs, tool_value_getinfo = run_handler_poll(run=run_info)

        # send the tool outputs back to complete the run
        if tool_outputs:
            run_info = client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread.id,
                run_id=run_info.id,
                tool_outputs=tool_outputs
            )

        # waiting for run to be completed
        wait(
            lambda: run_info.status == 'completed',
            timeout_seconds=60,
            waiting_for="run info for being completed")

        # receiving the corresponding payload
        messages_response_getinfo = client.beta.threads.messages.list(
            thread_id=thread.id)

        # create the user sorted message to the thread for an specific query
        # again
        message_user = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="user: " + productName
        )

        """
          ** Here you call the checkStock function run **
        """
        # create the run here and specify the tool_choice to make it easier and
        # more efficient
        run_check = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Give priority to this client! Return the tools that are activated by the user message",
            tool_choice={
                "type": "function",
                "function": {
                    "name": "checkStock"}})

        # evaluate the getInformation function here
        # parsing the tool output here after the requied action is processed
        tool_outputs, tool_value_check = run_handler_poll(run=run_check)

        # send the tool outputs back to complete the run
        if tool_outputs:
            run_check = client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread.id,
                run_id=run_check.id,
                tool_outputs=tool_outputs
            )

        # waiting for run to be completed
        wait(
            lambda: run_check.status == 'completed',
            timeout_seconds=60,
            waiting_for="run check for being completed")

        # receiving the corresponding payload
        messages_response_getcheck = client.beta.threads.messages.list(
            thread_id=thread.id)

        # here invoke the functions
        response_check_val = tool_value_check
        response_info_val = tool_value_getinfo

        stock_availability_string, stock_avail = checkStock(
            stock_value=response_check_val, mock_products=mock_products)
        info_string, price, description = getInformation(
            info_values=response_info_val)

        response_text = "<b>" + productName + "</b><br>" + \
            info_string + stock_availability_string
        product_query = True

        # try to make a query to an image
        downloader.download(
            productName.replace(
                ' ',
                '_'),
            limit=1,
            output_dir='./images/',
            adult_filter_off=True,
            force_replace=False,
            timeout=60,
            verbose=True)

        list_of_files = glob.glob(
            './images/' +
            productName.replace(
                ' ',
                '_') +
            '/*')
        latest_file = max(list_of_files, key=os.path.getctime)

        # copy the tree to the static folder
        if os.path.exists('./static/img_results/'):
            shutil.copytree(
                './images/',
                './static/img_results/',
                dirs_exist_ok=True)

        img_path = '../static/img_results/' + \
            productName.replace(' ', '_') + '/' + latest_file.split('/')[3]

        return response_text, img_path, product_query, productName, price, description, stock_avail


# tools definition for association functions to the query
tools = [
    {
        "type": "function",
        "function": {
                "name": "getProductInfo",
                "description": "Give the product_name value described in the JSON input catalog that contains any string in the text after 'user: '",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "productName": {
                            "type": "string",
                            "description": "The complete product_name value given in the JSON input catalog that contains any string given after 'user: '. If any string after 'user: ' is NOT contained in any product_name this value MUST BE 'null'! The query should be returned in plain text, not in JSON.",
                        }
                    },
                    "required": ["productName"],
                },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "checkStock",
            "description": "Give the single stock_avail value associated with the user input. This is NOT the product_name! Only the stock_avail value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "checkValue": {
                        "type": "string",
                        "description": "The value of stock_avail associated with the product given in the text after 'user: '. This is NOT the product_name! Only the stock_avail value.",
                    }
                },
                "required": ["checkValue"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getInformation",
            "description": "Give the description and prices values associated with the user input. This is NOT the product_name! Only the information required.",
            "parameters": {
                "type": "object",
                "properties": {
                    "price": {
                        "type": "string",
                        "description": "The value of price associated with the product given in the text after 'user: '. This is NOT the product_name! Only give the associated price value! The query should be returned in plain text."
                    },
                    "description_val": {
                        "type": "string",
                        "description": "The value of description associated with the product given in the text after 'user: '. This is NOT the product_name! Only give the associated description value! The query should be returned in plain text."
                    },
                },
                "required": ["price", "description_val"],
            },
        }
    }
]


@app.get("/")
def index_get():
    return render_template("index.html")


@app.post("/adduser")
def adduser():
    """
     This is the preliminary function for adding and validating
     the user form. This will execute first than anything.

     :return jsonify(ack): the jsonified object of the ack value to
     validate the complete input.
     :rtype jsonify(ack): json dict/map
    """
    # validate the input
    ack = 'none'
    global username
    global password
    userpass = request.get_json()
    print(userpass)
    username = userpass.get("user")
    password = userpass.get("pass")
    if len(username) == 0 or len(password) == 0:
        return (jsonify('incomplete'))
    else:
        return jsonify(ack)


@app.post("/ini")
def ini():
    """
     This is the initialization function that starts the API.
     it returns a welcome message to the client from the chatbot
     widget. The mocks product as the json file with the generated
     json catalog in created here.

     :return jsonify(message): the jsonified object of the  initial
     message composed with the welcome string in "answer" and the returned
     image status in "file_name"
     to the API
     :rtype jsonify(message): json dict/map
    """

    global mock_products
    global assistant
    global thread

    # initialize the openai endpoint

    size = random.randint(2, 15)

    # this will be only used for generating the Mock catalog, this won't be
    """
     ** Here you define the mock catalog with a different role **
    """
    response_mock = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI ShopBot system. You will give me adequate prompts for giving a good serving in a shopping context as mock catalogs"},
            {
                "role": "system",
                "content": "Can you give me a random Mock catalog of unique products with size of " +
                str(size) +
                " as json, with product_name, description, price, and stock_avail (as string between 'True' or 'False') fields? \n"}])

    """
     ** Here you define the assistant for the session **
    """
    # create the assistant here before to do any other call using the threads
    assistant = client.beta.assistants.create(
        name="Shopping Bot Assistant",
        instructions="You are a helpful AI ShopBot assistant. You will give me adequate prompts for giving a good service in a shopping context. Use the provided functions to answer questions. Generate function outputs (in tools) depending on the received messages",
        model="gpt-4o",
        tools=tools
    )

    # now create the thread after you initialize the chatbot only after the
    # initialization
    thread = client.beta.threads.create()

    mock_products = response_mock.choices[0].message.content

    # cut the json string only
    idx1 = mock_products.index('[')
    idx2 = mock_products.index(']')

    # length of substring 1 is added to
    # get string from next character
    mock_products = mock_products[idx1:idx2 + 1]

    print(mock_products, 'mock_products')

    message = {
        "answer": "Let's start having an interaction with the ShopBot.. <br>"}
    return jsonify(message)


@app.post("/predict")
def predict(Data=ShopData, DataProduct=ShopData_Product, db=db, tools=tools):
    """
     This is the predict post function receiving the ShopBot models object
     and the database object generated for this Flask API. The database must
     be initialized outside the main or any POST functions defined in this
     app.py file. This function contains the Bedrock enpoint invoking, the
     data deploying, and the database updating after two interactions.

     :param Data: An ShopData object defined in the models_database module
     This defines the parameters of the database but to add a new item on it.
     :param Data: An ShopData_Product object defined in the models_database module,
     such as, the product_name, price, description, and stock_availability as strings for
     the postgresql db.
     :param db: This is a SQLAlchemy database session as Postgresql. This initialized
     before any app function will run.
     :return jsonify(message): the jsonified object of the message
     coming from the bedrock endpoint response in "answer" and the returned
     image status in "file_name" with the updated image input coming from the front
     to the API, in case the image is presented.
     :rtype jsonify(message): json dict/map
    """

    global username
    global file_name
    global mock_products
    global assistant
    global thread

    inside = 0

    # This is the input of the chatbox
    text = request.get_json().get("message")

    random.random()

    # Step 1: get the endpoint for interactions

    text_sub_val = text.replace('?', '')
    text_sub_val = text_sub_val.replace('!', '')
    text_sub_val = text_sub_val.replace('.', '')
    text_sub_val = text_sub_val.replace(',', '')

    # create the messages here to the thread
    message_catalog = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="The JSON input catalog is: " + mock_products + " \n"
    )

    # create the parsing message here to the thread
    message_content = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="user: " + text_sub_val,
    )

    # create the run here and specify the tool_choice to make it easier and
    # more efficient
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Give priority to this client! Return the tools that are activated by the user message",
        tool_choice={
            "type": "function",
            "function": {
                "name": "getProductInfo"}})

    # parsing the tool output here after the requied action is processed
    tool_outputs, tool_value_returned = run_handler_poll(run=run)

    # send the tool outputs back to complete the run
    if tool_outputs:
        run = client.beta.threads.runs.submit_tool_outputs_and_poll(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )

    # waiting for run to be completed
    wait(
        lambda: run.status == 'completed',
        timeout_seconds=120,
        waiting_for="run for being completed")

    # receiving the corresponding payload
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    # parse the response from the main query
    response = messages.data[0].content[0].text.value

    print(response, 'response_message')

    # Step 2: determine if the response from the model includes a tool call.
    tool_calls = tool_value_returned.tool_calls

    print(response, 'response', tool_calls, 'tool_calls')

    if tool_calls:
        # If true the model will return the name of the tool / function to call
        # and the argument(s)
        tool_calls[0].id
        tool_calls[0].function.name
        tool_value = json.loads(
            tool_calls[0].function.arguments)['productName']
        text_sub = text.replace('?', '')
        text_sub = text_sub.replace('!', '')
        text_sub = text_sub.replace('.', '')
        text_sub = text_sub.replace(',', '')
        # text_sub = re.sub(r'[^a-zA-Z0-9]','', text_sub)
        text_split = text_sub.split(" ")

        # double validation
        if tool_value != 'null' and not (tool_value is None):
            for index in range(0, len(text_split)):
                if text_split[index] in tool_value.lower():
                    inside = 1
                    break

        if inside == 0:
            tool_value = 'null'

    if not ('bye' in text_sub_val.lower()):
        # invoke the GetProductInfo function the rest functions will be
        # executed inside
        response_text, image_path, product_query, product_name_def, price_def, description_def, stock_availability_def = getProductInfo(
            productName=tool_value, mock_products=mock_products, text=text, tools=tools, thread=thread, assistant=assistant)
    else:

        # create the messages here to the thread
        message_bye = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content="user: " + text_sub_val
        )

        # define a bye run
        run_bye = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
        )

        wait(
              lambda: run_bye.status == 'completed',
              timeout_seconds=60,
              waiting_for="bye run for being completed")

        # process message payload
        messages_bye = client.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content[0].text.value

        image_path = '../static/images/gray.jpg'
        product_query = False

    message = {
        "answer": response_text, "file_name": image_path}

    print(response_text, 'dataresponse')

    # get the time just after the query is done
    time_now = datetime.datetime.now().strftime("%I:%M:%S%p-%B-%d-%Y")

    # Code and ID generator
    code_str = ''.join(random.choice(string.ascii_letters)
                       for i in range(16))

    id = random.randint(0, 100000)

    file_ids_r = open("./ids.txt", "r")
    lst = []
    for line in file_ids_r:
        lst.append(int(line.strip()))

    # check if the ids are repeated
    while id in lst:
        id = random.randint(0, 100000)

    # create file with new ids to save in the database
    with open("./ids.txt", "a+") as file_ids:
        file_ids.write(str(id) + '\n')

    # fill the database item values
    register = Data(
        id=id,
        code=code_str,
        date=time_now,
        username=username,
        Interaction="user: " + text + ", ShopBot: " + response_text)

    # add a new register to the database
    db.session.add(register)
    db.session.commit()

    # add the second table with the product information
    if product_query is True:

        id_table = random.randint(0, 100000)

        file_ids_product = open("./ids_products.txt", "r")
        lst = []
        for line in file_ids_product:
            lst.append(int(line.strip()))

        # check if the ids are repeated
        while id in lst:
            id_table = random.randint(0, 100000)

        # create file with new ids to save in the database
        with open("./ids_products.txt", "a+") as file_ids_product:
            file_ids_product.write(str(id_table) + '\n')

        # fill the product table item values
        register_product = DataProduct(
            id=id_table,
            code=code_str,
            date=time_now,
            username=username,
            product_name=product_name_def,
            price=price_def,
            description=description_def,
            stock_availability=stock_availability_def)

        # add a new register to the new product table in database
        db.session.add(register_product)
        db.session.commit()

    return jsonify(message)


if __name__ == "__main__":
    # create the table in the database
    # run the main in localhost
    app.run(host='0.0.0.0', port=8000, debug=True)
    # run this for Docker
    # app.run(host='0.0.0.0', port=8000, debug=True)
