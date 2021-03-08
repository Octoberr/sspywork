"""
app status
目前有邮箱，购物，社交，打车，旅游
目前好像没有一个网盘
"""
from .apps.appmail import Mail_apps
from .apps.apptravel import Travel_apps
from .apps.appshopping import Shopping_apps
from .apps.appsocial import Social_apps
from .apps.apptaxi import Taxi_apps
# from datacontract import Mail_apps, Travel_apps, Shopping_apps, Social_apps, Taxi_apps

ALL_APPS: dict = {
    **Mail_apps,
    **Shopping_apps,
    **Social_apps,
    **Taxi_apps,
    **Travel_apps
}
