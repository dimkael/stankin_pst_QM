from .timer import Timer

"""
Class that represents clients queue
Clients queue starts the timer, that pops up tokens (rows) from database
Also it provides notifies to all clients that are currently in queue
"""

class Queue:
    def __init__(self, app):
        self.app = app
        self.db = app['db']
        # Starting timer that will pop up token from queue every 30 seconds
        self.timer = Timer(self.pop_first, self.remove_first, 30)
        self.first = None
        self.is_empty = True

    async def insert(self, token, ip):
        # Calling custom function to insert new row into database
        await self.db.insert({'token': token, 'ip': ip})

        # Sending updated queue to all clients
        await self.send_queue()

        if self.is_empty:
            self.is_empty = False
            await self.timer.start()

    # Method that pops up first row in database
    async def pop_first(self):
        #self.first_in_queue = await self.db.pop()
        self.first = await self.db.get_first_row()

        # if database (queue) is empty (first row in database is none)
        # we canceling timer and waiting for first token that will be inserted into database
        # then we starting timer again
        if not self.first:
            self.is_empty = True
            await self.timer.cancel()

    # Method deletes first row in database, that was popped up earlier
    async def remove_first(self):
        await self.db.delete({'id': self.first['id']})
        # Sending updated queue to all clients
        await self.send_queue()

    async def skip(self):
        await self.timer.skip()

    # Method that notifying all clients and sending updated queue
    async def send_queue(self):
        # Getting all rows (entire queue) from updated database
        queue = await self.db.get_tokens()

        # Creating message with name of function to run and its arguments (data)
        msg = {'action': 'show_queue', 'data': queue}
        # sending updated queue converted to json to all clients
        for sock in self.app['sockets']:
            if sock.is_in_queue:
                await sock.websocket.send_json(msg)

    async def is_first_in_queue(self, token, ip):
        if token == self.first['token'] and ip == self.first['ip']:
            return True

        return False
