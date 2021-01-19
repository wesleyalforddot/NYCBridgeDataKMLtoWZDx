import xml.etree.ElementTree as Et  # used to traverse kml file
import json  # used to convert dictionary to json

tree = Et.parse('lowbridges_citywide_data_71309.kml')  # parses the kml file into a tree
root = tree.getroot()  # gets the base element

# creates the road_event_feed_info structure mocked up with several fake pieces of data
road_event_feed_info = {
    "publisher": "NYCDOT",
    "version": "3.0",
    "update_date": "2020-09-29T18:00:00Z",
    "update_frequency": 86400,
    "contact_name": "TBD",
    "contact_email": "TBD@gmail.com",
    "data_sources": [
        {
            "data_source_id": "nyc-bridge-data",
            "organization_name": "NYC DOT",
            "location_method": "channel-device-method",
            "contact_name": "TBD",
            "contact_email": "TBD@gmail.com"
        }
    ]
}

bridges = []  # list that will be used to bridge features

# initializing static values for the data feed
# road_event_features
data_source_id = "nyc-bridge-data"
event_type = "work-zone"
start_date = "2020-01-01T00:00:00Z"
end_date = "2021-12-31T00:00:00Z"
beginning_accuracy = "verified"
ending_accuracy = "estimated"  # this is made up to satisfy need for MultiPoint geometry
start_date_accuracy = "verified"
end_date_accuracy = "verified"
direction = "westbound"  # this is static and made up for all road events do to lack of road direction in data set
vehicle_impact = "all-lanes-open"
restrictions = "reduced-height"
# lane features
order = 1  # using just the left most lane to be able to identify the exact height restriction for the bridge
lane_type = "left-lane"
status = "open"
# lane restriction features
restriction_type = "reduced-height"
restriction_units = "feet"

index = 1  # index used to create unique road_event_id
# root[0][5] contains the <folder> with bridge objects referred to as Placemark
for bridge in root[0][5].iter('{http://earth.google.com/kml/2.0}Placemark'):
    road_event_id = (bridge[0].text) + str(index)  # road name that contains bridge + index to create unique id
    data_block = (bridge[2].text) # data element to be further processed that contains bridge information
    data_block = data_block.replace(
        '''<table border=1 style="border-collapse:collapse; border-color:#000000;" cellpadding=0 cellspacing=0  width=250 style="FONT-SIZE: 11px; FONT-FAMILY: Verdana, Arial, Helvetica, sans-serif;">''',
        '<table>')  # removes the <table> tags format so it can be processed as xml
    data_block = Et.fromstring(data_block)  # parse the data block as xml
    road_name = data_block[1][1][0].text  # impacted road
    # height restriction in feet
    restriction_value = round(int(data_block[2][1][0].text) +
                              int(data_block[3][1][0].text) / 12, 2)
    coords_text = bridge[4][2].text.split(",")  # geospatial coords
    float_coords = [round(float(coords), 5) for coords in coords_text]  # convert text data to numeric
    dummy_coords = [float_coords[0] + .00001, float_coords[1] + .00001, float_coords[2]]  # generate dummy coordinates
    # round to nearest 5th decimal place for data specificity
    dummy_coords = [round(coords, 5) for coords in dummy_coords]
    coordinates = [float_coords, dummy_coords]  # adds extra dummy value to make Multipoint

    # creates the road_event property structure
    road_event_properties = {
        "data_source_id": data_source_id,
        "road_event_id": road_event_id,
        "event_type": event_type,
        "start_date": start_date,
        "end_date": end_date,
        "beginning_accuracy": beginning_accuracy,
        "ending_accuracy": ending_accuracy,
        "start_date_accuracy": start_date_accuracy,
        "end_date_accuracy": end_date_accuracy,
        "road_name": road_name,
        "vehicle_impact": vehicle_impact,
        "direction": direction,
        "lanes": [
            {
                "order": order,
                "status": status,
                "type": lane_type,
                "restrictions": [
                    {
                        "restriction_type": restriction_type,
                        "restriction_value": restriction_value,
                        "restriction_units": restriction_units
                    }
                ]
            }
        ]
    }

    # creates the road event geometry
    road_event_geometry = {
        "type": "MultiPoint",
        "coordinates": coordinates
    }

    # combines structures to create a road_event feature
    road_event = {
        "type": "Feature",
        "properties": road_event_properties,
        "geometry": road_event_geometry
    }

    bridges.append(road_event)  # adds new road event to feature collection
    index = index + 1  # increment index to ensure unique road_event_id

# create dictionary that contains a formatted data feed
data_feed = {
    "road_event_feed_info": road_event_feed_info,
    "type": "FeatureCollection",
    "features": bridges
}

# converts the python dictionary into a formatted json record and writes to a file
with open('NYCBridgeWZDx.json', 'w') as outfile:
    json.dump(data_feed, outfile, indent=4)
