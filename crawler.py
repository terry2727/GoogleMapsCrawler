from googlemapscrawler import GoogleMapsCrawler
import pymongo
from pymongo import MongoClient
from collections import OrderedDict
from bson.objectid import ObjectId

URL = 'https://www.google.com/maps/place/Bobapop+Ch%C3%B9a+L%C3%A1ng/@21.0231414,105.806109,17z/data=!3m1!4b1!4m5!3m4!1s0x3135ab66298c530f:0x3c6ec4bc056f7aed!8m2!3d21.0231364!4d105.8082977'

MERCHANT_ID = '5e56509f49f2a7a05da3ee73'
SHOP_ID = '5e565128aba586894e988e59'
LATEST_REVIEW_ID = 'ChdDSUhNMG9nS0VJQ0FnSURNOE1xOGp3RRAB'

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["localhostz"]

mycol = mydb["gg_reviews"]


def get_latest_review_id(shop_id, merchant_id):
    my_query = {"merchant_id": ObjectId(
        merchant_id), "shop_id": ObjectId(shop_id)}

    rv = mycol.find_one(my_query)

    id = rv['reviews'][0]['review_id']

    return id

if __name__ == '__main__':
    with GoogleMapsCrawler() as crawler:
        # mycol.remove({})

        error = crawler.sort_by_date(URL)

        if error == 0:

            location = {
                'shop_id': ObjectId(SHOP_ID),
                'merchant_id': ObjectId(MERCHANT_ID),
                'total_reviews': crawler.get_total_reviews(),
                'average_rating': crawler.get_average_rating(),
                'location_url' : URL,
                'reviews': crawler.get_all_reviews(),
            }
            mycol.insert(location)

            latest_review_id = get_latest_review_id(SHOP_ID, MERCHANT_ID)
            my_query = {"merchant_id": ObjectId(
                MERCHANT_ID), "shop_id": ObjectId(SHOP_ID)}
            updated_reviews_list = crawler.get_recent_updated_reviews(
                LATEST_REVIEW_ID) + list(mycol.find_one(my_query)['reviews'])[5:]

            location = {
                'shop_id': ObjectId(SHOP_ID),
                'merchant_id': ObjectId(MERCHANT_ID),
                'total_reviews': crawler.get_total_reviews(),
                'average_rating': crawler.get_average_rating(),
                'location_url': URL,
                'reviews': updated_reviews_list
            }
            mycol.insert(location)
