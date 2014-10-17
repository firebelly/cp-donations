from flask import Flask, jsonify, request
import shopify, hashlib, time

app = Flask(__name__)
app.config.from_object('config')
app.debug = True

@app.route('/donation')
def donation():
  shop_url = "https://%s:%s@%s.myshopify.com/admin" % (app.config['API_KEY'], app.config['PASSWORD'], app.config['SHOP_NAME'])
  shopify.ShopifyResource.set_site(shop_url)
  shop = shopify.Shop.current

  product = shopify.Product.find(request.get.id)

  # check if a variant exists with donation amount that we can reuse  
  for v in product.variants:
    if v.price == request.get.amount:
      variant = v

  if not variant:
    # if we are running out of skus trash an old one
    if len(product.variants) >= 245:
      del product.variants[0]

    # get hash for variant
    hash = hashlib.sha1()
    hash.update(str(time.time()))
    donation_id = hash.hexdigest()

    # create new variant and associate with product
    variant = shopify.Variant()
    variant.price = request.get.amount
    variant.option1 = donation_id
    product.variants.append(variant)
    product.save()
    
    # set variant var to saved variant
    variant = product.variants[-1]

  if variant:
    return jsonify(vid = variant.id,
                   message = 'success',
                   callback = request.args.callback,
                   price = variant.price)
  else:
    return jsonify(message = 'failure',
                   callback = request.args.callback)

if __name__ == '__main__':
    app.run()