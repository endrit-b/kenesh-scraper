# -*- coding: utf-8 -*-
from bson.son import SON

class MongoUtils(object):

    mongo = None

    def __init__(self):
        pass

    def init(self, mongo):
        self.mongo = mongo

    def get_absences(self, year=None):

        docs = self.mongo.db.absence.aggregate([
            {
                "$group":{
                    "_id":{
                        "firstName": "$firstName",
                        "lastName": "$lastName"
                    },
                    "count":{
                        "$sum": 1
                    }
                }
            },
            {
                "$sort": {
                    "count": -1
                }   
            },
            {
                "$project":{
                    "_id": 0,
                    "firstName": "$_id.firstName",
                    "lastName": "$_id.lastName",
                    "count": "$count"
                }   
            }
        ])

        return docs['result']


    def get_parliament_members(self, party_type=None, last_name=None, first_name=None):

        match = {'$match': {}}

        if party_type != None:
            if party_type == 'faction':
                party_type = 'Фракция'
            
            elif party_type == 'deputies':
                party_type = 'депутатская группа'

            elif party_type == 'independent':
                party_type = ''

            match['$match']['group.type'] = party_type


        if first_name != None:
            match['$match']['firstNameLatin'] = first_name

        if last_name != None:
            match['$match']['lastNameLatin'] = last_name


        sort = {
            "$sort": SON([
                ("absences.days.count", -1), 
                ("absences.sessions.count", -1),
                ("absences.lastName", -1),
                ("absences.firstName", -1)
            ]) 
        }

        docs = self.mongo.db.deputies.aggregate([
            match,
            sort
        ])

        return docs['result']


