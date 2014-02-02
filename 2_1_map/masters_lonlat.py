#!/usr/bin/env python

import sys, csv, math, json, os, time


def as_numeric(s):
    try:
        s = int(s)
    except ValueError:
        try:
            s = float(s)
        except ValueError:
            pass
    return s


def get_locations():
    print("Parsing locations...")
    location_lookup = {}
    with open("school-names-locations.csv") as f:    
        rows = csv.reader(f)
        indexes = []
        for r, row in enumerate(rows):
            if r == 0:
                indexes = row
                continue
            # convert to dict format                
            row = dict(zip(indexes, row))                
            row = {key: as_numeric(row[key]) for key in row}
            # extract useful values
            unitid = row['unitid']
            lon = row['HD2012.Longitude location of institution']
            lat = row['HD2012.Latitude location of institution']  
            name = row['institution name']
            # add to lookup
            entry = {'unitid': unitid, 'lon': lon, 'lat': lat, 'name': name}
            location_lookup[unitid] = entry
    print("--> done")
    return location_lookup


def parse(path, year, locations):
    print("Parsing '%s'..." % path)
    entries = {}
    with open(path) as f:
        rows = csv.reader(f)
        indexes = []
        for r, row in enumerate(rows):
            if r % 500 == 0:
                print(r)
            if r == 0:
                indexes = [r.lower() for r in row]
                continue
            # convert to dict format
            row = dict(zip(indexes, row))
            row = {key: (as_numeric(row[key]) if len(row[key].strip()) else 0) for key in row}
            # filter for arts cips
            if not ((row['cipcode'] >= 50000 and row['cipcode'] < 60000) or math.floor(row['cipcode']) == 50):
                continue
            # filter for masters degrees
            if row['awlevel'] != 7:
                continue
            # count degrees
            if 'crace15' in row:
                total_men, total_women = row['crace15'], row['crace16']
            else:
                total_men, total_women = row['ctotalm'], row['ctotalw']
            # if this institution is in entries, add the degrees
            if row['unitid'] in entries:
                entries[row['unitid']]['degrees'] += total_men + total_women
                entries[row['unitid']]['subjects'] += 1
                continue
            # otherwise, create a new entry
            else:
                entry = {}
                entry['unitid'] = row['unitid']
                entry['subjects'] = 1     
                entry['degrees'] = total_men + total_women
                entry['year'] = year
                try:
                    location = locations[entry['unitid']]
                    entry['lon'] = location['lon']
                    entry['lat'] = location['lat']
                    entry['name'] = location['name']
                except KeyError as e:
                    print(e)                
                    break
                entries[entry['unitid']] = entry
    # package as list
    entries = [entry for (key, entry) in entries.items()]
    print("--> finished %s" % year)                
    return entries


if __name__ == "__main__":
    locations = get_locations()
    result = {}
    for filename in os.listdir("data"):
        if filename[-4:] != ".csv":
            continue
        year = filename[1:5]
        result[year] = parse(os.path.join("data", filename), year, locations)
    with open("%s_output.json" % int(time.time()), 'w') as f:
        f.write(json.dumps(result, indent=4))

