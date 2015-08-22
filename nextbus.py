import requests
import xml.etree.ElementTree as ET

BASE_URL = "http://webservices.nextbus.com/service/publicXMLFeed"

def get_agencies():
    res_agencies = requests.get(BASE_URL, {'command': 'agencyList'})

    agency_tree = ET.fromstring(res_agencies.text)
    agency_dict = {}

    for agency in agency_tree:
        att = agency.attrib

        agency_dict[att['tag']] = { 'title': att['title'], 
          'regionTitle': att['regionTitle'] }

        if 'shortTitle' in att:
            agency_dict['shortTitle'] = att['shortTitle']

    return agency_dict

class Agency:
    def __init__(self, agency):
        self.agency = agency
        self.routes = self.get_routes()

    def get_routes(self):
        res_routes = requests.get(BASE_URL,
          { 'a': self.agency, 'command': 'routeList' })

        routes_tree = ET.fromstring(res_routes.text)
        routes_dict = {}

        for route in routes_tree:
            att = route.attrib

            routes_dict[att['tag']] = att['title']

        return routes_dict

    def get_route_config(self, route_id):
        if route_id not in self.routes:
            raise Exception('The specified route is invalid.')

        res_route_cfg = requests.get(BASE_URL,
          { 'a': self.agency, 'command': 'routeConfig', 'r': route_id, 
            'terse': None })

        route_cfg_tree = ET.fromstring(res_route_cfg.text)
        route_cfg_dict = {'stops': {}, 'directions': {}, 'paths': {}}

        route_cfg = route_cfg_tree[0]

        if not route_cfg:
            raise Exception('Error retrieving route config.')

        for c in route_cfg:
            att = c.attrib

            if c.tag == 'stop':
                # required info
                stop_data = { 'lat': att['lat'], 'lon': att['lon'], 
                  'title': att['title'], 'stopId': att['stopId'] }

                # optional info
                if 'stopId' in att:
                    stop_data['stopId'] = att['stopId']
                if 'shortTitle' in att:
                    stop_data['shortTitle'] = att['shortTitle']

                # save the info
                route_cfg_dict['stops'][att['tag']] = stop_data

            elif c.tag == 'direction':
                # required info
                direction_data = { 'title': att['title'], 'stops': [] }

                for stop in c:
                    direction_data['stops'].append(stop.attrib['tag'])

                # optional info
                if 'name' in att:
                    direction_data['name'] = att['name']

                # save the info
                route_cfg_dict['directions'][att['tag']] = direction_data

        return route_cfg_dict
