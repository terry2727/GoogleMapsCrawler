from googlemapscrawler import GoogleMapsCrawler

URL = 'https://www.google.com/maps/place/Highlands+Coffee/@21.0282839,105.7664912,17z/data=!4m7!3m6!1s0x313454baeaf08769:0xca17b41d816029e4!8m2!3d21.0282789!4d105.7686799!9m1!1b1'
URL2 = 'https://www.google.com/maps/place/Highlands+Coffee/@21.0282839,105.7664912,17z/data=!3m1!4b1!4m5!3m4!1s0x313454baeaf08769:0xca17b41d816029e4!8m2!3d21.0282789!4d105.7686799'

if __name__ == '__main__':

    with GoogleMapsCrawler(debug=True) as crawler:
        error = crawler.sort_by_date(URL2)
