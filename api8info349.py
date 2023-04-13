from flask import Flask,request,jsonify, make_response
from models import db,Products, Order
from rq import Queue, Worker, Connection
from redis import Redis

import redis
import pickle
import requests, json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['DEBUG'] = os.getenv('FLASK_DEBUG')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
app.config['REDIS_URL'] = os.getenv('REDIS_URL')

headers = {'Accept': 'application/json'}
 
# redis_client = redis.Redis(host='localhost', port=6379, db=0)
listen = ['high', 'default', 'low']
redis_client = redis.from_url(app.config['REDIS_URL'])

@app.cli.command('init-db')
def initdb_command():
    db.connect()
    db.create_tables([Products, Order], safe=True)

@app.cli.command('worker')
def initdb_command():
    with Connection(redis_client):
        worker = Worker(map(Queue, listen))
        worker.work()

def init_db():
    db.connect()
    db.create_tables([Products, Order], safe=True)

@app.route('/')
def words():
    prd = Products.select()
    prd_info = Products.select()
    if request.method == 'GET':
        if not prd:
            r = requests.get('http://dimprojetu.uqac.ca/~jgnault/shops/products/', 
                    headers={'Accept': 'application/json'})
            with open('file.json', 'w') as outfile:
                json.dump(r.json(), outfile)
            product = r.json()['products']
            for product in product:
                new = Products(
                    id = product['id'],
                    name = product['name'],
                    type = product['type'],
                    description = product['description'],
                    image = product['image'],
                    height = product['height'],
                    weight = product['weight'],
                    price = product['price'],
                    in_stock = product['in_stock']
                )
                new.save(new)
            with open('file.json') as qotd_file:
                data = json.load(qotd_file)
                rr = data['products']
                car = json.dumps(data, indent=4)
            return json.dumps(data, indent=4)
        else:
            with open('file.json') as qotd_file:
                data = json.load(qotd_file)
                rr = data['products']
                car = json.dumps(data, indent=4)
            return json.dumps(data, indent=4)

@app.route('/order', methods=['POST'])
def new_order():
    if request.method == 'POST':
        error = check_error(request)
        request_content = request.get_json()
        if not error:
            if (request_content.get('product') is not None):
                quantity = request.get_json()['product']['quantity']
                id = request.get_json()['product']['id']
                prd_info = Products.select().where(Products.id==id).first()
                poid = prd_info.weight * quantity
                if poid > 0 and poid < 500:
                    shipping_price = 5
                elif poid < 2000:
                    shipping_price = 10
                elif poid >= 2000:
                    shipping_price = 25
                total_price = prd_info.price * quantity
                prd = request.get_json()['product']
                new = json.dumps(prd)
                order = Order(product = new, shipping_price = shipping_price, total_price = total_price, being_paid = False)
                order.save()
                # db.session.add(order)
                # db.session.commit()
                return "302 Found\nLocation: /order/" + str(order.id)
            elif (request_content.get('products') is not None):
                poid = 0
                price = 0
                products = request.get_json()['products']
                for product in products:
                    quantity = product['quantity']
                    # quantity = request.get_json()['product']['quantity']
                    id = product['id']
                    prd_info = Products.select().where(Products.id==id).first()
                    poid = poid + prd_info.weight * quantity
                    price = price + prd_info.price * quantity
                
                if poid > 0 and poid < 500:
                    shipping_price = 5
                elif poid < 2000:
                    shipping_price = 10
                elif poid >= 2000:
                    shipping_price = 25
                total_price = price
                prd = request.get_json()['products']
                new = json.dumps(prd)
                order = Order(product = new, shipping_price = shipping_price, total_price = total_price)
                order.save()
                # db.session.add(order)
                # db.session.commit()
                return "302 Found\nLocation: /order/" + str(order.id)
        else:
            return error

def check_error(request):
    request_content = request.get_json()
    if (request_content.get('product') is None and request_content.get('products') is None):
        error = "422 Unprocessable Entity"
        with open('422.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (error + car)
    elif (request_content.get('product') is not None):
        id = request.get_json()['product']['id']
        quantity = request.get_json()['product']['quantity']
        if (id <= 0 or id > 50 or quantity <= 0):
            error = "422 Unprocessable Entity"
            with open('422.json') as qotd_file:
                data = json.load(qotd_file)
                car = json.dumps(data, indent=4)
            return (error + car)
        else:
            prd_info = Products.select().where(Products.id==id).first()
            if (prd_info.in_stock == False):
                error = "422 Unprocessable Entity"
                with open('422_2.json') as qotd_file:
                    data = json.load(qotd_file)
                    car = json.dumps(data, indent=4)
                return (error + car)
    elif (request_content.get('products') is not None):
        products = request.get_json()['products']
        for product in products:
            id = product['id']
            quantity = product['quantity']
            if (id <= 0 or id > 50 or quantity <= 0):
                error = "422 Unprocessable Entity"
                with open('422.json') as qotd_file:
                    data = json.load(qotd_file)
                    car = json.dumps(data, indent=4)
                return (error + car)
            else:
                prd_info = Products.select().where(Products.id==id).first()
                if (prd_info.in_stock == False):
                    error = "422 Unprocessable Entity"
                    with open('422_2.json') as qotd_file:
                        data = json.load(qotd_file)
                        car = json.dumps(data, indent=4)
                    return (error + car)

@app.route('/order/<id>', methods=['GET','PUT'])
def order_infos(id):
    if request.method == 'GET':
        if (redis_client.get(id) is not None):
            order_info = pickle.loads(redis_client.get(id))
        else:
            order_info = Order.select().where(Order.id==id).first()
        # print (order_info.being_paid)
        if not order_info:
            error = "404 Command Not found"
            return (error) 
        if (order_info.being_paid == True):
            return make_response('', 202)
        else:
            if not order_info:
                error = "404 Command Not found"
                return (error)
            else:
                total_price = order_info.total_price
                if not order_info.email:
                    email = None
                else:
                    email = order_info.email
                if not order_info.credit_card:
                    credit_card = {}
                else:
                    credit_card = json.loads(order_info.credit_card)
                paid = order_info.paid
                if not order_info.transaction:
                    transaction = {}
                else:
                    transaction = json.loads(order_info.transaction)
                if not order_info.shipping_information:
                    shipping_information = {}
                else:
                    shipping_information = json.loads(order_info.shipping_information)
                product = json.loads(order_info.product)
                shipping_price = order_info.shipping_price
                dict = {
                    "order": {
                        "id": id,
                        "total_price": total_price,
                        "email": email,
                        "credit_card": credit_card,
                        "shipping_information": shipping_information,
                        "paid": paid,
                        "transaction": transaction,
                        "product": product,
                        "shipping_price": shipping_price
                    }
                }
                js = json.dumps(dict, indent=4)
                return js
    elif request.method == "PUT":
        ord = request.get_json()
        order_info = Order.select().where(Order.id==id).first()
        # order_info.being_paid = False
        # order_info.paid = False
        # order_info.transaction = {}
        # order_info.credit_card = {}
        # redis_client.set(order_info.id, pickle.dumps(order_info))
        # order_info.save()
        # return ("ok")
        if (order_info.being_paid == True):
            return make_response('', 409)
        else:
            if not order_info:
                error = "404 Command Not found"
                return (error)
            else:
                new_queue = Queue(connection=Redis())
                if (ord.get('amount_charged') is None):
                    ord['amount_charged'] = order_info.total_price + order_info.shipping_price
                    json.dumps(ord)
                if (ord.get('credit_card') is not None):
                    error = check_error3(request, id)
                    if not error:
                        ord = request.get_json()
                        r = requests.post('http://dimprojetu.uqac.ca/~jgnault/shops/pay/', json.dumps(ord),
                            headers={'Accept': 'application/json'})
                        print(r)
                        save_job = new_queue.enqueue(payment_succ, id, r)
                        order_info.being_paid = True
                        order_info.save()
                        print("ok")
                        print(r)
                        return make_response('', 202)
                        # r = requests.post('http://dimprojetu.uqac.ca/~jgnault/shops/pay/', json.dumps(ord),
                        #     headers={'Accept': 'application/json'})
                        # order_info.transaction = json.dumps(r.json()['transaction'])
                        # order_info.credit_card = json.dumps(r.json()['credit_card'])
                        # order_info.paid = True
                        # redis_client.set(order_info.id, pickle.dumps(order_info))
                        # order_info.save()
                        # return r.json()
                    else:
                        return error
                else:
                    error = check_error2(request, id)
                    if not error:
                        email = request.get_json()['order']['email']
                        order_info = Order.select().where(Order.id==id).first()
                        order_info.email = email
                        order_info.shipping_information = json.dumps(request.get_json()['order']['shipping_information'])
                        order_info.save()
                        return infos(id)
                    else:
                        return error

def payment_succ(id, r):
    # ord = request.get_json()
    # request_content = request.get_json()
    order_info = Order.select().where(Order.id==id).first()
    # r = requests.post('http://dimprojetu.uqac.ca/~jgnault/shops/pay/', json.dumps(ord),
    #     headers={'Accept': 'application/json'})
    if ("transaction" in r.json().keys()):
        order_info.transaction = json.dumps(r.json()['transaction'])
        order_info.credit_card = json.dumps(r.json()['credit_card'])
        order_info.paid = True
        order_info.being_paid = False
        redis_client.set(order_info.id, pickle.dumps(order_info))
        order_info.save()
        return r.json()
    else:
        card_data = {
            "success": False,
            "error": json.dumps(r.json()['errors']['credit_card']),
            "amount_charged": order_info.shipping_price + order_info.total_price
        }
        order_info.transaction = json.dumps(card_data)
        order_info.paid = False
        order_info.being_paid = False
        redis_client.set(order_info.id, pickle.dumps(order_info))
        order_info.save()

def infos(id):
    if (redis_client.get(id) is not None):
        order_info = redis_client.get(id)
    else:
        order_info = Order.select().where(Order.id==id).first()

    total_price = order_info.total_price
    if not order_info.email:
        email = None
    else:
        email = order_info.email
    if not order_info.credit_card:
        credit_card = {}
    else:
        credit_card = json.loads(order_info.credit_card)
    paid = order_info.paid
    if not order_info.transaction:
        transaction = {}
    else:
        transaction = json.loads(order_info.transaction)
    if not order_info.shipping_information:
        shipping_information = {}
    else:
        shipping_information = json.loads(order_info.shipping_information)
    product = json.loads(order_info.product)
    shipping_price = order_info.shipping_price
    dict = {
        "order": {
            "id": id,
            "total_price": total_price,
            "email": email,
            "credit_card": credit_card,
            "paid": paid,
            "transaction": transaction,
            "product": product,
            "shipping_information": shipping_information,
            "shipping_price": shipping_price
        }
    }
    js = json.dumps(dict, indent=4)
    return js

def check_error2(request,id):
    if (int(id) <= 0):
        error = "422 Unprocessable Entity"
        with open('422.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (error + car)
    else:
        order_info = Order.select().where(Order.id==id).first()
        if not order_info:
            error = "404 Command Not found"
            return (error)
        else:
            ord = request.get_json()
            if (ord.get('order') is None):
                error = "422 Unprocessable Entity"
                with open('422_3.json') as qotd_file:
                    data = json.load(qotd_file)
                    car = json.dumps(data, indent=4)
                return (error + car)
            ord = request.get_json()['order']
            if (ord.get('shipping_information') is None):
                error = "422 Unprocessable Entity"
                with open('422_3.json') as qotd_file:
                    data = json.load(qotd_file)
                    car = json.dumps(data, indent=4)
                return (error + car)
            elif (ord.get('email') is None):
                error = "422 Unprocessable Entity"
                with open('422_3.json') as qotd_file:
                    data = json.load(qotd_file)
                    car = json.dumps(data, indent=4)
                return (error + car)
            ship = request.get_json()['order']['shipping_information']
            email = request.get_json()['order']['email']
            if (email is None or ship.get('country') is None or ship.get('address') is None
            or ship.get('postal_code') is None or ship.get('city') is None or ship.get('province') is None):
                error = "422 Unprocessable Entity"
                with open('422_3.json') as qotd_file:
                    data = json.load(qotd_file)
                    car = json.dumps(data, indent=4)
                return (error + car)

def check_error3(request, id):
    request_content = request.get_json()
    credit = request_content.get('credit_card')
    amount = request.get_json()
    order_info = Order.select().where(Order.id==id).first()
    if not order_info.shipping_information:
        with open('422_3.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (car)
    elif not order_info.email:
        with open('422_3.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (car)
    elif(order_info.paid == True):
        error = "422 Unprocessable Entity\nContent-Type: application/json"
        with open('already.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (error + car)
    # elif (credit.get('number') == "4000 0000 0000 0002"):
    #     error = "422 Unprocessable Entity\nContent-Type: application/json"
    #     with open('decline.json') as qotd_file:
    #         data = json.load(qotd_file)
    #         car = json.dumps(data, indent=4)
    #     return (error + car)
    elif (credit.get('number') is None):
        with open('invalidcard.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (car)
    elif (credit.get('expiration_year') is None or credit.get('expiration_year') < 2023):
        with open('expiration.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (car)
    elif (credit.get('expiration_year') == 2023 and credit.get('expiration_month') < 4):
        with open('expiration.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (car)
    elif (credit.get('cvv') is None ):
        with open('expiration.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (car)
    elif(amount.get('amount_charged') <= 0 or amount.get('amount_charged') < order_info.total_price + order_info.shipping_price):
        with open('amount.json') as qotd_file:
            data = json.load(qotd_file)
            car = json.dumps(data, indent=4)
        return (car)

if __name__ == "__main__":
    app.run(host='localhost', port=5000)