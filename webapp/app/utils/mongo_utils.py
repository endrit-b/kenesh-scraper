class MongoUtils(object):

    mongo = None

    def __init__(self):
        pass

    def init(self, mongo):
        self.mongo = mongo

    def get_absentees(self, year=None, group_type=None, group_name=None):

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