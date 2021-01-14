.. _basebot:


Setup Your First Bot
============

We are going to get you going using guilded.py 

Setup The Library
---------------
You can get the library directly from PyPI: ::

    python3 -m pip install guilded.py

If you are using Windows, then the following should be used instead: ::

    py -3 -m pip install  guilded.py

A Basic Bot
---------------

The following code consists of a bot that will respond to a message like !ping and reply with "Pong"

.. code-block:: python3

    import guilded

    bot = guilded.Bot(comamnd_prefix="!")

    @bot.event()
    async def on_ready():
        print("The Bot has connected to Guilded")
        
    @bot.command()
    async def ping(ctx):
        await ctx.send("Pong")

    bot.run('email@example.com', 'password123')
    
    
    
Let me explain what is happening line by line
 "import guilded" imports the library for guilded
 "bot = guilded.Bot(command_prefix="!")" Defines what a bot is and sets the prefix
 "@bot.event()
  async def on_ready():
    print("The Bot has connected to Guilded")" An event that is ran when the bot connects to Guilded
"@bot.command()
 async def ping(ctx):
    await ctx.send("Pong")" Called when you use !ping in your server, ctx stands for the context of the message including the team, author, and all attributes related to the message, and the bot replies with "Pong"
"bot.run('email@example.com', 'password123')" Tells the bot to login to Guilded and runs the script that you just wrote

Name this file anything you want except "guilded.py" or you may cause issues with the library

Since you made a python script, it is simple 1 line to get it running

Note if you get an error about websockets not being installed or found make sure to do the following
Windows:
.. code-block:: shell

    $ py -3 -m pip install websockets

Otheerwise do 
.. code-block:: shell

    $ pip3 install websockets

On Windows:

.. code-block:: shell

    $ py -3 guilded_bot.py

On other systems:

.. code-block:: shell

    $ python3 guilded_bot.py
