import requests
import xml.etree.ElementTree as ET

BASE_URL = "http://webservices.nextbus.com/service/publicXMLFeed"

JAVA_TF_TO_PYTHON_TF = { 'true': True, 'false': False }

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

        for c in route_cfg:
            att = c.attrib

            if c.tag == 'stop':
                # required info
                stop_data = { 'lat': att['lat'], 'lon': att['lon'], 
                  'title': att['title'] }

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

    def predictions(self, stop_id, route_id=None):
        req_params = { 'a': self.agency, 'command': 'predictions',
          'stopId': stop_id }

        # add the optional parameter if present
        if route_id:
            req_params['routeTag'] = route_id

        res_predictions = requests.get(BASE_URL, req_params)

        predictions_tree = ET.fromstring(res_predictions.text)

        predictions_dict = {}

        # iterate over all route predictions at this stop
        for predictions in predictions_tree:
            pred_line_dict = { 'directions': {}, 'messages': [] }

            # iterate over all directions/messages for this line
            for pred_info in predictions:
                att = pred_info.attrib

                if pred_info.tag == 'direction':
                    pred_dir_list = []

                    for p in pred_info:
                        p_att = p.attrib

                        p_dict = { 'epochTime': p_att['epochTime'],
                                   'seconds': p_att['seconds'],
                                   'minutes': p_att['minutes'],
                                   'isDeparture': p_att['isDeparture'],
                                   'dirTag': p_att['dirTag'],
                                   'tripTag': p_att['tripTag'],
                                   'affectedByLayover': False,
                                   'isScheduleBased': False,
                                   'isDelayed': False }

                        # optional info

                        if 'affectedByLayover' in p_att:
                            p_dict['affectedByLayover'] = \
                              JAVA_TF_TO_PYTHON_TF[p_att['affectedByLayover']]

                        if 'isScheduleBased' in p_att:
                            p_dict['isScheduleBased'] = \
                              JAVA_TF_TO_PYTHON_TF[p_att['isScheduleBased']]

                        if 'isDelayed' in p_att:
                            p_dict['isDelayed'] = \
                              JAVA_TF_TO_PYTHON_TF[p_att['isDelayed']]

                        pred_dir_list.append(p_dict)

                    pred_line_dict[pred_info.attrib['title']] = pred_dir_list

                elif pred_info.tag == 'message':
                    pred_line_dict['messages'].append({
                      'priority': att['priority'], 'text': att['text']
                    })

            predictions_dict[predictions.attrib['routeTag']] = pred_line_dict

        # if specific route specified, return the only item in the dict
        if not route_id:
            return predictions_dict
        else:
            return predictions_dict[route_id]
