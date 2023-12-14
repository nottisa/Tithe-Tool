import importlib
import os, sys, json
from colorama import Fore, Style, Back, init as coloramainit
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

if not "routes" in os.listdir():
    os.mkdir("routes")

class CONFIG:
    """Configuration for the application."""
    def __init__(self):
        data = json.load(open("configs/config.json", "r"))
        self.debug = data["Debug"]
        self.port = data["Port"]
        self.productID = data["Product_ID"]
        self.stripeToken = data["Stripe_Token"]
        self.redirectURL = data["Redirect_URL"]
        self.paymentCycle = data["Payment_Cycle"]
        self.enforceCurrency = data["Enforce_Currency"]
        self.currency = data["Currency"]
        self.minimumAmount = data["Minimum_Amount"]
        self.inactiveMessage = data["Bad_Payment_Link_Message"]

def loadRoutes(folder, cleanup:bool=True):
    global app
    """Load Routes from the routes directory."""
    for root, dirs, files in os.walk(folder, topdown=False):
        for file in files:
            if not "__pycache__" in root:
                route_name = os.path.join(root, file).removesuffix(".py").replace("\\", "/").replace("/", ".")
                route_version = route_name.split(".")[0]
                if route_name.endswith("index"):
                    route = importlib.import_module(route_name)
                    if route.donotload:
                        continue
                    route_name = route_name.split(".")
                    del route_name[-1]
                    del route_name[0]
                    route_name = ".".join(route_name)
                    route.router.prefix = "/"+route_name.replace(".", "/")
                    route.router.tags = route.router.tags + [route_version] if isinstance(route.router.tags, list) else [route_version]
                    # route.router.name = route_name
                    route.setup()
                    app.include_router(route.router)
                    print(Fore.CYAN + "routes."+route_name)
                else:
                    route = importlib.import_module(route_name)
                    if route.donotload:
                        continue
                    route_name = route_name.split(".")
                    del route_name[0]
                    route_name = ".".join(route_name)
                    route.router.prefix = "/"+route_name.replace(".", "/")
                    route.router.tags = route.router.tags + [route_version] if isinstance(route.router.tags, list) else [route_version]
                    # route.router.name = route_name
                    route.setup()
                    app.include_router(route.router)
                    print(Fore.CYAN + "routes."+route_name)
    if cleanup:
        print(Fore.GREEN + "Cleaning __pycache__ up!")
        for root, dirs, files in os.walk(folder, topdown=False):
            if "__pycache__" in dirs:
                pycache_dir = os.path.join(root, "__pycache__")
                print(Fore.YELLOW + f"Deleting: {pycache_dir}")
                try:
                    # Remove the directory and its contents
                    for item in os.listdir(pycache_dir):
                        item_path = os.path.join(pycache_dir, item)
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        else:
                            os.rmdir(item_path)
                    os.rmdir(pycache_dir)
                except Exception as e:
                    print(f"Error deleting {pycache_dir}: {e}")


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

async def startup_event():
    coloramainit(autoreset=True)
    if len(os.listdir("routes")) == 0:
        print(Fore.RED + "No routes loaded")
        sys.exit()
    print(Fore.BLUE + "Routes Loading...")
    loadRoutes("routes")
    print(Fore.GREEN + "Routes Loaded!")

app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    uvicorn.run("app:app", port=8080)