# Serviceless Distributor
The Serviceless Distributor is a library to help you to run exact functions without any other service.

## How it works?
It is simply a decorator which takes arguments and keyword arguments, pickles them and sends them to other nodes with **HTTP** requests.

## Is it efficient to use?
The answer is depends on the mode you select. If you set `Distributor.bounce_mode = False` one node need to send data to all nodes **BUT** if you set `Distributor.bounce_mode = True` (which is default) all nodes will send data to next node so all nodes will make only one request instead of `len(SERVICELESS_DISTRIBUTOR_NODES)`.

## Is it secure?
It is secure as you keep your **key** as a secret. Library uses `django.core.signing` replica([djangoless-signing](https://github.com/FKLC/djangoless-signing)) to sign and unsign data to make sure data is sent over servers. **BUT** it is always recommended to configure your servers to restrict IPs connecting to this endpoint.

## Quick Start for Flask
**USE THIS LIBRARY IF YOU AREN'T USING DJANGO** if you are using Django check [django-serviceless-distributor](https://github.com/FKLC/django-serviceless-distributor)


Install library
```bash
pip install serviceless-distributor
```

Add this snippet to your app
```py
....
from serviceless_distributor import Distributor
....

....
# Key to sign your data
Distributor.key = b"literally anything but you'll have to keep it secret"

# Nodes IPs (Do not use load balancer IP, we couldn't know
# if all nodes affected if you use load balancer IP)
Distributor.nodes = ["http://10.0.0.0", "http://10.0.0.1"]

# Headers to use while sending data
# (This can be used to change "Host" to pass Host restriction)
Distributor.headers = {}
....

@app.route("/serviceless_distributor", methods=['POST'])
def hello():
    data = request.form.get('username')
    if data:
        Distributor._run_function(data)
    return ""
```

Register functions you want to distributed
```py
from serviceless_distributor import Distributor

@Distributor.register_function()
def sum_arguments(*args):
  return sum(args)

# Or lets suppose you want to distribute an imported function
from some_module import some_function

some_function = Distributor.register_function()(some_function)
```


### (Not) Frequently Asked Questions
1. How do I set different node set for diffrent functions?
    ```py
    special_nodes = ["http://10.0.0.0", "http://10.0.0.1"]

    @Distributor.register_function(nodes=special_nodes)
    def sum_arguments(*args):
        return sum(args)

    # Or
    from some_module import some_function

    Distributor.register_function(nodes=special_nodes)(some_function)
    ```

2. Can I change the path?

    Yes, you can change `Distributor.path` **BUT** also don't forget to change your url config according to the change you made.

3. How many requests sent by library simultaneously?

    It is 10 by default but you can change by setting `Distributor.simultaneous_requests`. **ATTENTION** by simultaneously requests it means distributing registered functions to other nodes. If you run a registered function X times in a row server will send X times of requests. It doesn't create X threads for every registered function run.

4. Is it blocking?

    **No**, it creates threads using `concurrent.futures.ThreadPoolExecutor` and returns the output of registered function.

5. Why should I use this instead of other libraries?

    The only reason could be saving money this is actually why I created that. To me this isn't a good solution when compared to other libraries but the best at least I can do without any other servers.
