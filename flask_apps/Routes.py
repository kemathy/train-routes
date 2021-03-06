from flask_apps import app
from flask import render_template, request, redirect
import requests
from requests.auth import HTTPBasicAuth
import datetime
import re


@app.template_filter('secondsToTime')
def _jinja2_filter_datetime(seconds):
    minutes = seconds%3600/60
    hours = seconds/3600
    return str(hours) + ":" + str(minutes)


@app.template_filter('removeTownFromStationName')
def _jinja2_filter_datetime(station):
    parts = station.split('(')
    return parts[0].rstrip()


@app.template_filter('timeDifference')
def _jinja2_filter_datetime(diff):
    print "timeDifference"
    diffstr = "%06d" % diff
    timeArray = re.compile('(..)').findall(diffstr)
    return timeArray


@app.template_filter('humanReadableTime')
def _jinja2_filter_datetime(time):
    datetimeObject = datetime.datetime.strptime(time, '%Y%m%dT%H%M%S')
    return datetimeObject.strftime('%d/%m/%Y %H:%M')


def getPlaceID(city):
    req = requests.get("https://api.sncf.com/v1/coverage/sncf/places?q="+ city, auth=HTTPBasicAuth(app.config['SNCFAPIKEY'], ''))
    ret = []
    ret.append(req.status_code)
    ret.append(req.json())
    return ret


def getJourneys(srcStation, dstStation, departureDateTime):
    print "getJourneys"
    req = requests.get("https://api.sncf.com/v1/coverage/sncf/journeys?from="+ srcStation + "&to=" + dstStation + "&datetime=" + departureDateTime + "&datetime_represents=departure&min_nb_journeys=4"\
    , auth=HTTPBasicAuth(app.config['SNCFAPIKEY'], ''))
    ret = []
    ret.append(req.status_code)
    ret.append(req.json())
    return ret

@app.template_filter('getVehicleJourneyDetails')
def _jinja2_filter_datetime(vehicleJourney):
    print "jinja2_filter - getVehicleJourneyDetails for " + vehicleJourney
    req = requests.get("https://api.sncf.com/v1/coverage/sncf/vehicle_journeys/" + vehicleJourney, auth=HTTPBasicAuth(app.config['SNCFAPIKEY'], ''))
    ret = []
    ret.append(req.status_code)
    ret.append(req.json())
    #print req.json()
    return ret


@app.route("/route/<string:from_place>/<string:to_place>/<string:style>", methods=['GET', 'POST'])
def routes(from_place, to_place, style):
    places = []
    print request.form

    if 'otherway' in request.form:
        print "otherway"
        print to_place
        print from_place
        return redirect('/route/' + to_place + '/' + from_place + '/' + style)

    if 'othersize' in request.form:
        print "othersize"
        if style == "mini":
            return redirect('/route/' + from_place + '/' + to_place + '/classic')
        else:
            return redirect('/route/' + from_place + '/' + to_place + '/mini')


    # Get places IDs
    fromPlaceIdResult = getPlaceID(from_place)
    fromPlaceID = fromPlaceIdResult[1]['places'][1]['id']
    fromPlaceName = fromPlaceIdResult[1]['places'][1]['name']

    toPlaceIdResult = getPlaceID(to_place)
    toPlaceID = toPlaceIdResult[1]['places'][1]['id']
    toPlaceName = toPlaceIdResult[1]['places'][1]['name']

    places.append({'from_place': fromPlaceName, 'to_place': toPlaceName,\
                    'from_place_id': fromPlaceID, 'to_place_id': toPlaceID,\
    })

    date = datetime.datetime.today().strftime('%Y%m%d %R:%M')
    journeysResult = getJourneys(fromPlaceID, toPlaceID, date)

    if style == "mini":
        return render_template("route_mini.html", places=places, journeysResult=journeysResult)
    else:
        return render_template("route.html", places=places, journeysResult=journeysResult)
