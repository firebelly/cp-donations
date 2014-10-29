from flask import Flask, jsonify, request, current_app
import shopify, hashlib, time
from functools import wraps
from flask.ext.appconfig import HerokuConfig

def create_app(configfile=None):
    app = Flask(__name__)
    HerokuConfig(app, configfile)
    return app

def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f().data) + ')'
            return current_app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home(): 
  return 'Hello! Nothing to see here.'
  
@app.route('/donation')
@support_jsonp
def donation():
  shop_url = "https://%s:%s@%s.myshopify.com/admin" % (app.config['SHOPIFY_API_KEY'], app.config['SHOPIFY_API_PASSWORD'], app.config['SHOP_NAME'])
  shopify.ShopifyResource.set_site(shop_url)
  shop = shopify.Shop.current
  variant = None
  product = None
  message = ''

  if request.args.get('id'):
    product = shopify.Product.find(int(request.args.get('id')))
  else:
    message = 'No product id sent.'

  if product and request.args.get('amount'):
    # check if a variant exists with donation amount that we can reuse  
    for v in product.variants:
      if float(v.price) == float(request.args.get('amount')):
        variant = v

    if not variant:
      # if we are running out of skus trash an old one
      if len(product.variants) >= 245:
        del product.variants[1]

      # get hash for variant
      hash = hashlib.sha1()
      hash.update(str(time.time()))
      donation_id = hash.hexdigest()

      # create new variant and associate with product
      variant = shopify.Variant()
      variant.price = request.args.get('amount')
      variant.option1 = donation_id
      product.variants.append(variant)
      product.save()
      
      # set to saved variant
      variant = product.variants[-1]
  else:
    message = 'No amount sent.'

  if variant:
    return jsonify(vid = variant.id,
                   message = 'success',
                   price = variant.price)
  else:
    return jsonify(message = 'failure: %s' % message)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
