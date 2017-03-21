import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from influxdb import InfluxDBClient


def upload(host, data=[], database='health'):
    if len(data):
        client = InfluxDBClient(host=host, database=database, port=8086)
        client.create_database('health')
        client.write_points(points=data, batch_size=1000)

def parse(export):
    with open(export) as f:
        tree = ET.parse(f)

    formattedData = []
    records = tree.findall('Record')

    # we only want records with numeric values
    records = list(filter(lambda x: str(x.get('value')).isdigit(), records))

    for record in records:
        attr = record.attrib

        unit = attr['unit']
        value = float(attr['value'])
        date = attr['endDate']
        source = attr['sourceName']
        measurement = attr['type']

        # chop off prefix if detected
        if measurement[0:24] == 'HKQuantityTypeIdentifier':
            measurement = measurement[24:]

        # parse the time string
        parsedTime = datetime.strptime(date, '%Y-%m-%d %H:%M:%S %z')
        # save as correct format in UTC timezone
        time = parsedTime.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        recordDict = {
            'measurement': measurement,
            'tags': {},
            'time': time,
            'fields': {
                'value': value
            }
        }

        if unit is not None:
            recordDict['tags']['unit'] = unit
        if source is not None:
            recordDict['tags']['source'] = source

        formattedData.append(recordDict)

    # print(formattedData)
    return formattedData


def main(host, export, database):
    try:
        data = parse(export)
        upload(host, data, database)

        print('Total upload success!')
    except Exception as e:
        print('Failure!')
        print(str(e))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Uploads HealthKit data to InfluxDB')
    parser.add_argument('dbhost', help='InfluxDB host')
    # TODO - make sure this is optional
    parser.add_argument('database', default='health', help="InfluxDB database")
    parser.add_argument('file', help='Health data export file')

    args = parser.parse_args()

    main(args.dbhost, args.file, args.database)